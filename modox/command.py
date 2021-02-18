
""" This module is a wrapper for lxu.command.BasicCommand.

    It improves and simplifies command implementations including popups,
    sPresetText fields, and Form Command Lists.

    This is based on Adam O'Hern Commander code but is vastly enhanced.
    https://github.com/adamohern/commander
"""

import time
import traceback
import operator

import lx, lxu, lxifc
import modo
from xfrm import TransformUtils
from item import ItemUtils
from message import Message
from setup import SetupMode
from run import run


def bless(commandClass, commandName):
    """ Custom bless function.
    """
    commandClass.NAME = commandName
    try:
        lx.bless(commandClass, commandName)
    except TypeError:
        lx.out('Blessing failed: %s, %s' % (str(commandClass), str(commandName)))
        

class Argument(object):
    """ Argument represents single command argument.
    
    Arguments should be added as this class instances to the command.
    """
    
    # These datatypes will be treated as Float values
    sTYPE_FLOATs = [
        'acceleration',
        'angle',
        'axis',
        'color1',
        'distance',
        'float',
        'force',
        'light',
        'mass',
        'percent',
        'speed',
        'time',
        'uvcoord'
    ]
    
    # Treated as Str values
    sTYPE_STRINGs = [
        'date',
        'datetime',
        'filepath',
        'string',
        'vertmapname',
        '&item'
    ]
    
    # Treated as Str values in the MODO UI,
    # but parsed into [Float, Float, Float] for use in the execute()
    sTYPE_STRING_vectors = [
        'angle3',
        'color',
        'float3',
        'percent3'
    ]
    
    # Treated as Int values
    sTYPE_INTEGERs = [
        'integer'
    ]
    
    # Treated as Bool values
    sTYPE_BOOLEANs = [
        'boolean'
    ]
    
    DATATYPES = sTYPE_FLOATs + sTYPE_STRINGs + sTYPE_STRING_vectors + sTYPE_INTEGERs + sTYPE_BOOLEANs

    def __init__(self, name="", datatype=None):
        self.name = name
        self.label = None
        self.defaultValue = None
        self.datatype = None
        if datatype is not None:
            self.datatype = datatype.lower()
        self.valuesList = None
        self.valuesListUIType = None
        self.flags = None
        self.index = -1
        self.hints = None

    def __str__ (self):
        """ Represent argument as its name and string datatype.
        """
        reprString = "Command argument: " + self.name
        if isinstance(self.datatype, str):
            reprString += " type: "
            reprString += self.datatype
        return reprString

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        elif isinstance(other, Argument):
            return self.name == other.name
        elif isinstance(other, int):
            return self.index == other
        else:
            return False


class ArgumentPopupContent(object):
    """ Use this class for filling contents of a popup.
    """
    def __init__(self):
        self._entries = []
        self.iconWidth = None
        self.iconHeight = None

    def __len__(self):
        return len(self._entries)

    def __getitem__(self, key):
        if not isinstance(key, int):
            raise TypeError
        if key >= len(self._entries):
            raise KeyError
        return self._entries[key]

    def __iter__(self):
        return iter(self._entries)

    def addEntry(self, entry):
        self._entries.append(entry)

    def getEntry(self, index):
        return self._entries[index]

    @property
    def entriesCount(self):
        return len(self._entries)


class ArgumentPopupEntry(object):
    def __init__(self, internalName="", userName=""):
        self.internalName = internalName
        self.userName = userName
        self.iconImage = None
        self.iconResource = None


class ArgumentItemsContent(object):
    """ Use this class to define values for the item popup argument. 
    """
    def __init__(self):
        self.noneOption = False
        self.testOnRawItems = False # use lx.object.Item rather then modo.Item.
        self.itemTestFunction = False


class ArgumentValuesListType(object):
    """ When argument represents a list of values these can show up
    in UI as Popup, sPresetText or Form Command List.
    A popup with item list is also supported.
    """
    POPUP = 1
    S_PRESET_TEXT = 2
    FORM_COMMAND_LIST = 3
    ITEM_POPUP = 4


class Command(lxu.command.BasicCommand):
    """Wrapper for lxu.command.BasicCommand.
    
    Based on Adam OHern commander code.
    https://github.com/adamohern/commander
    """
    
    # NAME is only used for debugging purposes.
    NAME = ''

    @property
    def name(self):
        return self.NAME

    # --- Public methods, to be overriden by user.

    def init(self):
        """ Performs any extra initialisation steps that the command requires.
        
        This is called from commands __init__() method.
        """
        pass

    def interact(self):
        """ Perform interaction with user before command is actually executed.
        
        Typically this means opening file dialogs, confirm messages, etc.
        Interact() happens before command posts its dialog with arguments.
        
        Returns
        -------
        bool
            False if command should not be executed, True if it should go ahead.
        """
        return True

    def enable(self, msg):
        """ Decides if the command should be enabled or disabled.

        Parameters
        ----------
        msg : modox.Message
            Wrapper around lx.object.Message, use it to set disable/enable message.

        Returns
        -------
        bool
            True for enabled command, False otherwise.
        """
        return True

    def flags(self):
        """ Command flags.
        """
        return lx.symbol.fCMD_UNDO

    def arguments(self):
        """ Gets a list of arguments for a command.
        
        Returns
        -------
        list of Argument or single Argument
            Return either single or a list of Argument objects, one for each argument.
        """
        return []

    def getArgument(self, ident):
        """ Gets argument by index or name.
        
        Parameters
        ----------
        ident : str or int
            Either argument name or its index.
            
        Returns
        -------
        Argument
        
        Raises
        ------
        LookupError?
        """
        if type(ident) == str:
            ident = self._argumentsByName[ident]

        return self._argumentsList[ident]

    def isArgumentSet(self, ident):
        """ Returns whether given argument is set in a command or not.
        
        Parameters
        ----------
        ident : str or int
            Either argument name or its index.
        
        Returns
        -------
        bool
        """
        arg = self.getArgument(ident)
        return self.dyna_IsSet(arg.index)

    def getArgumentValue(self, ident):
        """Return a command argument value by index.
            If no argument value exists, returns the default parameter.
            NOTE: The commander_args() method is simpler to use than this method.
            You should probably use that one unless you have a reason to find a specific
            argument by index.
            :param index: (int) index of argument to retrieve
            :param default: value to return if argument is not set
            :returns: argument value (str, int, float, or boolean as appropriate)
        """
        arg = self.getArgument(ident)

        # If no value is set, return the default.
        if not self.dyna_IsSet(arg.index):
            return self._resolveDefaultValue(arg.defaultValue)

        # TODO: I think it's about variable argument value?
        #if 'variable' in self.commander_arguments()[index].get(FLAGS, []):
            #datatype = self.basic_ArgType(index)
        #else:
            #datatype = self.commander_arguments()[index][DATATYPE].lower()
            
        # If it's a string, use dyna_String to grab it.
        if arg.datatype in Argument.sTYPE_STRINGs:
            return self.dyna_String(arg.index)

        # If the value is a vector, use dyna_String to grab it, then parse it
        # into a list of float vlues.
        elif arg.datatype in Argument.sTYPE_STRING_vectors:
            return [float(i) for i in self.dyna_String(arg.index).split(" ")]

        # If the value is an integer, use dyna_Int to grab it.
        elif arg.datatype in Argument.sTYPE_INTEGERs:
            return self.dyna_Int(arg.index)

        # If the value is a float, use dyna_Float to grab it.
        elif arg.datatype in Argument.sTYPE_FLOATs:
            return self.dyna_Float(arg.index)

        # If the value is a boolean, use dyna_Bool to grab it.
        elif arg.datatype in Argument.sTYPE_BOOLEANs:
            return self.dyna_Bool(arg.index)

        elif arg.datatype == '&item':
            return self.dyna_String(arg.index)

        # If something bonkers is going on, use the default.
        return self._resolveDefaultValue(arg.defaultValue)

    def uiHints(self, argument, hints):
        """ Set UI hints for a given argument by calling methods
        on the given hints object.
        """
        pass

    def icon(self):
        """ Returns string with icon name for command button.
        """
        return None

    def notifiers(self):
        """ Returns a list of notifiers for a command.

        Should return a list of tuples, for example:
        [('notifier.editAction',''), ("select.event", "item +ldt"), ("tagger.notifier", "")]
        """
        return []

    def setupMode(self):
        """ Sets setup mode for the command.
        
        This will be set at the beginning of execute.
        
        Returns
        -------
        bool or None
            True/False to switch Setup Mode to a given state.
            None to not affect setup mode (this is default).
        """
        return None

    def restoreSetupMode(self):
        """
        Restores setup mode to its previous value once command is executed.

        Returns
        -------
        bool
            Return True to restore setup mode to its state prior to command execution.
        """
        return False

    def preExecute(self):
        """ Called after interact() but before execute block is called.

        Use this if you want to verify the command is ok to run after dialog
        with command arguments was closed by user.

        Returns
        -------
        bool
            False if command should not be executed, True if it should go ahead.
        """
        return True

    def executeStart(self):
        """ Called from within basic_Execute at the very beginning of execution code.

        Use this function to perform actions from within the actual execute block
        but right before execute() is called.
        """
        pass

    def execute(self, msg, flags):
        """ This is the place for main command execution code.
        """
        pass

    def executeEnd(self):
        """ Called from basic_Execute, after execute() was called.

        Typically used for clean up/restore operations.
        """
        pass

    def query(self, argument):
        """ Returns a value based on and argument being queried.
        
        This method can return string, boolean, integer or float."""
        return None

    def enableTimersOn(self):
        """ Enable/disable log output that says how long enable() takes.

        This can help with optimising performance of enable().
        This method should be as fast as possible so it doesn't slow down UI.
    
        Returns
        -------
        bool
            True to enable timers log output.
        """
        return False

    def queryTimersOn(self):
        """ Enable/disable log output that says how long query() method takes.

        This can help with optimising performance of query().
        This method should be as fast as possible so it doesn't slow down UI.

        Returns
        -------
        bool
            True to enable log output.
        """
        return False

    def restoreItemSelection(self):
        """ Restores item selection after command is executed.
        
        Returns
        -------
        bool
            True if item selection should be restored to a state prior to firing the command.
        """
        return False

    def autoFocusItemListWhenDone(self):
        """ Automatically focuses item list on selected items when command execution is over.
        """
        return False
    
    def applyEditActionPre(self):
        """ Applies edit action before the command is executed so there are no 'hanging' edits.
        
        Returns
        -------
        bool
            True if edit action should be applied.
            Default is False.
        """
        return False

    def applyEditActionPost(self):
        """ Applies edit action after the command is executed so there are no 'hanging' edits left.
        
        Returns
        -------
        bool
            True if edit action should be applied.
            Default is False.
        """
        return False

    def dropToolPre(self):
        """
        Drops any active tool before command execution starts.

        Returns
        -------
        bool
            True to drop a tool (if any is active).
        """
        return False

    # --- Private methods, do not touch.

    def cmd_Flags(self):
        """ Command is scene altering, undoable by default.
        """
        return self.flags()

    def cmd_Interact(self):
        result = self.interact()
        if not result:
            msg = lx.object.Message(self.cmd_Message())
            msg.SetCode(lx.symbol.e_ABORT)

    def cmd_PreExecute(self):
        result = self.preExecute()
        if not result:
            msg = lx.object.Message(self.cmd_Message())
            msg.SetCode(lx.symbol.e_ABORT)

    def cmd_Icon(self):
        return self.icon()

    def basic_Enable(self, msg):
        if self.enableTimersOn():
            timeStart = time.clock()
        msgWrap = Message(msg)
        enabled = self.enable(msgWrap)
        if self.enableTimersOn():
            timeEnd = time.clock()
            lx.out("ENABLE (%s) : %f s." % (self.NAME, (timeEnd - timeStart)))
        return enabled

    def basic_ArgType(self, index):
        pass

    def cmd_DialogInit(self):
        """ Sets default values for arguments in command dialogs.
        
        Once this method is implemented MODO's default mechanism for storing
        argument values is not used.
        
        This method is called right before command's dialog pops up.
        
        Note that this method uses command argument's .defaultValue property.
        This property can be a function (or callable as a matter of fact).
        If you set a function as default value it'll always be called to retrieve the
        actual default value and used instead of the stored value in the dialog.
        Sadly, using function as argument, due to the way MODO seems to work (possible bug)
        makes it impossible to set the argument in command string, it will always be
        overridden by what default function returns. 
        """
        arguments = self.arguments()
        for n, argument in enumerate(arguments):

            datatype = argument.datatype
            defaultValue = arguments[n].defaultValue

            # Default value can be a function.
            # If it's a function we always want to call this function
            # to get the default value. This is because sometimes MODO seems
            # to report that the dyna_IsSet() for an argument even if it's not set
            # and should be pulled from default value.
            # In this case we do not want to miss retrieving value from function.
            if hasattr(defaultValue, '__call__'):
                storedValue = defaultValue()            
            else:
                # If we already have a value, use it.
                # This is especially important when a command is run with args
                # via command line or form button.
                if self.dyna_IsSet(n):
                    continue

                storedValue = self._argumentValuesCache[n]

            # If there's no stored value, we're done.
            if not storedValue:
                continue
                
            # The correct attr_Set... method depends on datatype.
            if datatype in Argument.sTYPE_STRINGs + Argument.sTYPE_STRING_vectors:
                self.attr_SetString(n, str(storedValue))

            elif datatype in Argument.sTYPE_INTEGERs + Argument.sTYPE_BOOLEANs:
                self.attr_SetInt(n, int(storedValue))

            elif datatype in Argument.sTYPE_FLOATs:
                self.attr_SetFlt(n, float(storedValue))

    def basic_Execute(self, msg, flags):
        """Stores recent command values for next run and wraps commander_execute
        in a try/except statement with traceback.

        Do NOT override this method. Use commander_execute() instead.

        You should never need to touch this.
        
        CRUCIAL: When turning off listening never just turn it back on!
        Set it to whatever the state was prior to executing this command.
        Otherwise, firing rs command from within other rs command is going
        to mess things up. Listening will be back to True as soon as first
        sub command is done.

        Returns
        -------
        bool, None
            Return False to exit command with ABORT message code.
        """
        scene = modo.Scene()

        self.executeStart()

        if self.dropToolPre():
            run('!tool.drop')

        if self.restoreItemSelection():
            selection = scene.selected

        setupMode = SetupMode()
        if self.restoreSetupMode():
            setupMode.store()

        if self.setupMode() is not None and setupMode.state != self.setupMode():
            setupMode.state = self.setupMode()

        if self.applyEditActionPre():
            TransformUtils.applyEdit()

        msgWrap = Message(msg)

        try:
            cmdResult = self.execute(msgWrap, flags)
        except:
            cmdResult = False
            lx.out(traceback.format_exc())

        if self.applyEditActionPost():
            TransformUtils.applyEdit()
                
        if self.restoreItemSelection():
            scene.select(selection, add=False)

        if self.restoreSetupMode():
            setupMode.restore()

        self.executeEnd()

        if not cmdResult and cmdResult is not None:
            msgWrap.setCode(Message.Code.ABORT)
            return

        # This is executed only when command did not abort
        if self.autoFocusItemListWhenDone():
            ItemUtils.autoFocusItemListOnSelection()

    def cmd_Query(self, index, vaQuery):
        if self.queryTimersOn():
            timeStart = time.clock()

        # Create the ValueArray object
        va = lx.object.ValueArray()
        va.set(vaQuery)
    
        # To keep things simpler for commander users, let them return
        # a value using only an index (no ValueArray nonsense)
        commander_query_result = self.query(self._argumentsList[index])
    
        # Need to add the proper datatype based on result from commander_query
    
        if isinstance(commander_query_result, basestring):
            va.AddString(commander_query_result)
    
        elif isinstance(commander_query_result, int):
            va.AddInt(commander_query_result)
    
        elif isinstance(commander_query_result, float):
            va.AddFloat(commander_query_result)

        elif isinstance(commander_query_result, (modo.Item, lx.object.Item, lxu.object.Item)):
            valRef = lx.object.ValueReference(va.AddEmptyValue())
            valRef.SetObject(commander_query_result)

        if self.queryTimersOn():
            timeEnd = time.clock()
            lx.out("QUERY (%s) : %f s." % (self.NAME, (timeEnd - timeStart)))

        return lx.result.OK

    def arg_UIHints(self, index, hints):
        """Adds pretty labels to arguments in command dialogs. If no label parameter
        is explicitly included, we create a pseudo-label by capitalizing the
        argument name and replacing underscores with spaces.
        Labels can either be literal strings or method/function objects. In the
        latter case, the method or function will be called when needed.
        If any popup fields of type sPresetText are present,
        adds the appropriate hint.
        You should never need to touch this."""

        try:
            arg = self._argumentsList[index]
        except IndexError:
            return

        # If an explicit label is provided, use it.
        if arg.label is not None:
            label = ""
            if isinstance(arg.label, str):
                label = arg.label
            elif type(arg.label) == bool and arg.label:
                label = arg.name.replace("_", " ").title()
            # Labels can be functions. If so, run the function to get the string.
            elif hasattr(arg.label, '__call__'):
                label = label()

            # Apply the label.
            if (label):
                hints.Label(label)

        # If the popup type is sPresetText, apply the appropriate class.
        if arg.valuesListUIType == ArgumentValuesListType.S_PRESET_TEXT:
            hints.Class("sPresetText")
        
        # Allow command implementation to do its custom work.
        self.uiHints(arg, hints)

    def arg_UIValueHints(self, index):
        """Popups and sPresetText arguments fire this method whenever
        they update. Note that the 'hints' parameter can be a literal list
        or tuple, but can also be a method or function.
        For dynamic lists, be sure to pass in the generator method or function object itself,
        not its result. (i.e. pass in 'myGreatFunction', NOT 'myGreatFunction()')
        You should never need to touch this."""
    
        try:
            arg = self._argumentsList[index]
        except IndexError:
            return

        arg_data = None

        # Try to grab the values_list for the argument.
        if arg.valuesList is not None:
            arg_data = arg.valuesList

        # If our values_list is empty, don't bother.
        if not arg_data:
            return

        # If the values_list is a list/tuple, use it as-is.
        if isinstance(arg_data, (list, tuple)):
            values = arg_data

        # This is very hacky here for the time being.
        # It's testing values against being the items popup content object.
        elif isinstance(arg_data, ArgumentItemsContent):
            values = arg_data

        # If the values_list is a method/function, fire it and use the result.
        elif hasattr(arg_data, '__call__'):
            values = arg_data()

        # In some rare cases you may want to manually instantiate your own
        # popup class as a subclass of UIValueHints. In those cases, we
        # ignore the below and just use yours.
        # isinstance(arg_data, type) tests whether arg_data is class
        # TODO: Think whether this logic has the best flow.
        # the return statement here doesn't fit and breaks the flow.
        if isinstance(arg_data, type) and issubclass(arg_data, lxifc.UIValueHints):
            return arg_data()

        # If values is None or "" or someother nonsense, return an empty list.
        if not values:
            values = []

        # Argument can be a normal popup, an sPresetText popup, or a
        # Form Command List. We'll need to return a different class
        # depending on the 'values_list_type'.

        if arg.valuesListUIType == ArgumentValuesListType.POPUP:
            return PopupClass(values)

        elif arg.valuesListUIType == ArgumentValuesListType.S_PRESET_TEXT:
            return PopupClass(values)

        elif arg.valuesListUIType == ArgumentValuesListType.FORM_COMMAND_LIST:
            return FormCommandListClass(values)

        elif arg.valuesListUIType == ArgumentValuesListType.ITEM_POPUP:
            return ItemPopupClass(arg_data)

    def cmd_NotifyAddClient(self, argument, object):
        """Add notifier clients as needed.
        You should never need to touch this."""
        for i, tup in enumerate(self._notifier_tuples):
            if self._notifiers[i] is None:
                self._notifiers[i] = self.not_svc.Spawn (self._notifier_tuples[i][0], self._notifier_tuples[i][1])

            self._notifiers[i].AddClient(object)

    def cmd_NotifyRemoveClient(self, object):
        """Remove notifier clients as needed.
        You should never need to touch this."""
        for i, tup in enumerate(self._notifier_tuples):
            if self._notifiers[i] is not None:
                self._notifiers[i].RemoveClient(object)
                
    # -------- Private methods
    
    def _resolveDefaultValue(self, defaultValue):
        """ Resolves default value in case default value is a function.
        """
        if hasattr(defaultValue, '__call__'):
            return defaultValue()
        return defaultValue
            
    def _setupNotifiers(self):
        # CommandClass can implement the commander_notifiers() method to update
        # FormCommandLists and Popups. If implemented, add the notifiers.
        self.not_svc = lx.service.NotifySys()
        self._notifiers = []
        self._notifier_tuples = tuple([i for i in self.notifiers()])
        for i in self._notifier_tuples:
            self._notifiers.append(None)

    @classmethod
    def _setupArgumentValuesCache(cls):
        """ We manually cache all argument values between command executions during single session.
        """
        try:
            cls._argumentValuesCache
        except AttributeError:
            cls._argumentValuesCache = []

    @classmethod
    def _cacheArgumentDefaultValue(cls, value):
        """Add an argument to the class variable _commander_stored_values.
        You should never need to touch this.
        """
        cls._argumentValuesCache.append(value)
        
    def _setupArguments(self):
        """ Setup command arguments based on arguments() method.

        Parse the list of Argument objects that the arguments method returns.
        """
        arguments = self.arguments()
        
        # The command does not have arguments
        if not arguments:
            return True

        result = True

        if not isinstance(arguments, list):
            arguments = [arguments]

        for argument in arguments:
            if not isinstance(argument, Argument):
                continue
            if not self._addArgument(argument):
                result = False
        return result

    def _addArgument(self, argument):
        if argument.datatype is None or argument.name is None:
            return False

        datatype = self._resolveArgumentDatatype(argument.datatype)
        if not datatype:
            return False
       
        argument.index = len(self._argumentsList)

        self.dyna_Add(argument.name, datatype)

        # This is setting up default value for this argument.
        # If this is the first time running the command, the class variable
        # _argumentValuesCache will be empty. In that case, populate it.
        # This should really go on the argument level, not command class level.
        if argument.index >= len(self._argumentValuesCache):
            # The default value can be a function. If it's a function
            # it will be called each time the command dialog is about to be opened.
            # In such case do not cache the default value, just make it a None.
            if hasattr(argument.defaultValue, '__call__'):
                self._cacheArgumentDefaultValue(None)
            else:
                self._cacheArgumentDefaultValue(argument.defaultValue)
                       
        flags = self._resolveArgumentFlagsList(argument.flags)
        if flags:
            self.basic_SetFlags(argument.index, reduce(operator.ior, flags))

        if argument.hints is not None:
            self.dyna_SetHint(argument.index, argument.hints)

        self._argumentsList.append(argument)
        self._argumentsByName[argument.name] = argument.index
        return True

    def _resolveArgumentDatatype(self, datatype):
        """ Resolve argument datatype into proper string that can be used by raw API.

        Args:
            datatype: (str) one of command argument type constants or
                            one of lx.symbol.sTYPE_ raw API constants.
        """
        try:
            resolvedDatatype = getattr(lx.symbol, 'sTYPE_' + datatype.upper())
        except AttributeError:
            resolvedDatatype = datatype
        return resolvedDatatype

    def _resolveArgumentFlagsList(self, flagsList):
        if not isinstance(flagsList, list):
            flagsList = [flagsList]

        flags = []
        for flag in flagsList:
            if flag is None:
                continue
            try:
                flags.append(getattr(lx.symbol, 'fCMDARG_' + flag.upper()))
            except AttributeError:
                flags.append(flag)
        return flags

    def __init__(self):
        lxu.command.BasicCommand.__init__(self)
        self._name = ""
        self._argumentsList = []
        self._argumentsByName = {}
        
        self._setupArgumentValuesCache()
        self._setupArguments()
        self._setupNotifiers()
        self.init()


class FormCommandListClass(lxifc.UIValueHints):
    """Special class for creating Form Command Lists. This is instantiated
    by CommanderClass objects if an FCL argument provided.
    Expects a list of valid MODO commands to be provided to init.
    NOTE: Any invalid command will crash MODO.
    You should never need to touch this."""

    def __init__(self, items):
        self._items = items

    def uiv_Flags(self):
        return lx.symbol.fVALHINT_FORM_COMMAND_LIST

    def uiv_FormCommandListCount(self):
        return len(self._items)

    def uiv_FormCommandListByIndex(self,index):
        return self._items[index]


class PopupClass(lxifc.UIValueHints):
    """Special class for creating popups and sPresetText fields. Accepts
    either a simple list of values, or a list of (internal, user facing) tuples:
    [1, 2, 3]
    or
    [(1, "The Number One"), (2, "The Number Two"), (3, "The Number Three")]
    You should never need to touch this."""

    def __init__(self, items):
        self._content = ArgumentPopupContent()
        if isinstance(items, (list, tuple)):
            for item in items:

                # If the list item is a list or tuple, assume the format (ugly, pretty)
                if isinstance(item, (list, tuple)):
                    entry = ArgumentPopupEntry(str(item[0]), str(item[1]))
                    self._content.addEntry(entry)
                # Otherwise just use the value for both Ugly and Pretty
                else:
                    entry = ArgumentPopupEntry(str(item), str(item))
                    self._content.addEntry(entry)

        elif isinstance(items, ArgumentPopupContent):
            self._content = items

    def uiv_Flags(self):
        return lx.symbol.fVALHINT_POPUPS

    def uiv_PopCount(self):
        return len(self._content)

    def uiv_PopUserName(self, index):
        return self._content[index].userName

    def uiv_PopInternalName(self,index):
        return self._content[index].internalName

    def uiv_PopIconSize(self):
        if self._content.iconWidth is not None and self._content.iconHeight is not None:
            return(1 ,self._content.iconWidth, self._content.iconHeight)
        lx.notimpl()

    def uiv_PopIconImage(self, index):
        iconImage = self._content[index].iconImage
        if iconImage is not None:
            return iconImage
        lx.notimpl()

    def uiv_PopIconResource(self, index):
        iconResource = self._content[index].iconResource
        if iconResource is not None:
            return iconResource
        lx.notimpl()


class ItemPopupClass(lxu.command.BasicHints):
    """Special class for creating popup with item list.
    """

    def __init__(self, itemContent):
        self._itemContent = itemContent

    def uiv_Flags(self):
        flags = lx.symbol.fVALHINT_ITEMS
        if self._itemContent.noneOption:
            flags |= lx.symbol.fVALHINT_ITEMS_NONE
        return flags

    def uiv_ItemTest(self, item):
        # item comes here as lx.object.Unknown.
        # Cast it to lx.object.Item by default.
        item = lx.object.Item(item)
        if not self._itemContent.testOnRawItems:
            item = modo.Item(item)
        return self._itemContent.itemTestFunction(item)