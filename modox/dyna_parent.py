
import lx
import modo
import modox

from item import ItemUtils
from channel import ChannelUtils
from run import run


class DynamicParentSetup(object):
    """ This class allows for setting up dynamic parenting.
    
    It replicates standard MODO setup but provides more control and managment
    over created modifiers.
    
    Parameters
    ----------
    setupItem : modo.Item
        Child tem of the setup.
        
    Raises
    ------
    TypeError:
        When trying to initialise with item that is not child in dynamic
        parenting setup.
    """

    DYNA_PARENT_CHANNELS = [
        'parent',
        'offsetPos.X',
        'offsetPos.Y',
        'offsetPos.Z',
        'offsetRot.X',
        'offsetRot.Y',
        'offsetRot.Z',
        'offsetScl.X',
        'offsetScl.Y',
        'offsetScl.Z']

    DEFAULT_OFFSET = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0]

    @classmethod
    def new(cls, childItem, parentItem=None, name=None, compensation=True):
        """ Creates new setup between two items.
        
        Parameters
        ----------
        childItem : modo.Item
            This is the item that will be parented.

        parentItem : modo.Item, optional
            If parent item is set full dynamic parenting setup will be built.
            If parent is None only dynamic parent modifier will be added and
            linked to the childItem. It will not be complete setup but one
            that MODO already recognises (basically the only choice will be world parent).

        name : str
            Name for the dynamic parent modifier.
            A suffix will be added to modifier items automatically.
        """
        # Store the offset here before creating dynamic parenting setup.
        # I need to do it manually because when dynamic parenting modifier is added
        # parent space is overriden.
        if parentItem is not None and compensation:
            offset = cls._calculateCompensationOffset(childItem, parentItem)

        dynaParent = cls._addDynamicParentModifier(childItem, name)
        newSetup = cls(childItem)
        newSetup._setDynamicParentRestValues()

        if parentItem is not None:
            # Add parent without compensation, offset will be applied manually
            newSetup.addParent(parentItem, compensation=compensation)

        # Apply precalculated offset if compensation is set to True.
        if parentItem is not None and compensation:
            cls._applyDynamicParentSetupValues(dynaParent, 1, offset, action=lx.symbol.s_ACTIONLAYER_SETUP)

        return newSetup

    # -------- Public methods

    def addParent(self,
                  parentItem,
                  compensation=True,
                  time=0.0,
                  key=False,
                  action=lx.symbol.s_ACTIONLAYER_SETUP):
        """ Adds new parent to the setup.
        
        Parameters
        ----------
        parentItem : modo.Item
            New parent item.
        
        compensation : bool, optional
        
        time : float, None, optional
            None means current time, default time is 0.0.
        
        key : bool
            Whether to set a key for new parent or not.
            Not relevant in Setup Mode (always off).
        
        action : str
            One of lx.symbol.s_ACTION_XXX or name of the action to change parent on.

        Returns
        -------
        int
            Index of new parent.
        """

        matrixCompose = self._addMatrixCompose(parentItem)
        if matrixCompose is None:
            return False
        
        chanTo = self._dynaParent.channel('matrixInput')
        chanFrom = matrixCompose.channel('matrixOutput')
        chanFrom >> chanTo
        
        # When the connection is made we also change parent to new one.
        # Remember that parent 0 is world.
        # So parent indexes start from 1, link 0 is parent 1, link 1 is parent 2, etc.
        newParentIndex = chanTo.revCount
        self.setParent(newParentIndex,
                       compensation=compensation,
                       time=time,
                       action=action,
                       key=key)

    def setParent(self,
                  itemOrIndex,
                  compensation=True,
                  time=None,
                  action=lx.symbol.s_ACTIONLAYER_EDIT,
                  key=False):
        """ Switches to given parent on a given action.
        
        Note that switching parent on setup action will also set the same values on scene
        if dynamic parenting setup is not animated yet.

        Parameters
        ----------
        itemOrIndex : int, modo.Item, None
            Either an index of parent to switch to or parent modo item.
            The item has to be a dynamic parent already.
            itemOrIndex 0 or None means parenting to world.
        
        compensation : bool, optional
        
        time : float, None, optional
            Use None for current time. Not relevant with setup action.
        
        action : lx.symbol.s_ACTIONLAYER_XXX or str
            Name of the action to switch parent on.
        
        key : bool
            Whether to keyframe parent change, not relevant in setup mode.
        """
        if type(itemOrIndex) in (int, long):
            index = itemOrIndex
            
            if index < 1:
                parentItem = None
            else:
                parentItem = self.getParentItem(index)
        else:
            if itemOrIndex is not None:
                parentItem = itemOrIndex
                index = self.getParentIndex(parentItem)
            else:
                parentItem = None
                index = 0

        if compensation:
            offset = self._calculateCompensationOffset(self._item, parentItem)
        else:
            offset = self.DEFAULT_OFFSET

        self._applyDynamicParentSetupValues(self._dynaParent, index, offset, action)

    def getParentItem(self, index):
        """ Gets parent item at a given index.
        
        Parameters
        ----------
        index : int
            Parent index the same as in the dynamic parent modifier.
            This means that 0 is world parent (no parent) and parent links
            start counting from 1.
        
        Returns
        -------
        modoItem, None
            None will be returned for parent index of 0 - which is world.
        
        Raises
        ------
        LookupError
            When parent cannot be found.
        """
        if index == 0:
            return None
        
        try:
            matrixCompose = self.getMatrixComposeModifier(index)
        except IndexError:
            raise LookupError
        parentItem = self._getParentItemFromMatrixCompose(matrixCompose)
        if parentItem is None:
            raise LookupError
        return parentItem
        
    def getParentIndex(self, modoItem):
        """ Gets index of a given parent item.
        
        Returns
        -------
        int
            Parent index the same as used in the dynamic parent modifier
            which means that indexing starts from 1 as 0 is world (no parent).
        
        Raises
        ------
        LookupError
            When parent cannot be found.
        """
        # TODO: Add reading this channel for specific action!
        parentCount = self._dynaParent.channel('parent').get()
        for x in xrange(parentCount):
            index = x + 1 # remember about counting parent indexes from 1
            parentItem = self.getParentItem(index) 
            if parentItem == modoItem:
                return index
        raise LookupError
    
    def selfDelete(self):
        """ Removes dynamic parenting setup.
        
        This simply deletes dynamic parent modifier.
        If matrix compose plugged into modifier is not used by anything else but dynamic parent
        setup the matrix compose is automatically removed by MODO.
        """
        run('!item.delete child:0 item:{%s}' % self._dynaParent.id)
    
    @property
    def isFullSetup(self):
        """ Returns whether this dynamic parent setup is a full one or not.
        
        Full setup includes dynamic parent modifier and at least one parent
        item plugged into it.
        """
        if not self._dynaParent:
            return False
        if len(self.matrixComposerModifiers) > 0:
            return True
        return False

    @property
    def animatedChannels(self):
        """ Gets a list of dynamic parent modifier animated channels.
        
        These are the channels that get keyed when parent is changed.
        
        Returns
        -------
        list of modo.Channel
        """        
        channels = []
        for chanName in self.DYNA_PARENT_CHANNELS:
            channels.append(self._dynaParent.channel(chanName))
        return channels
    
    @property
    def dynamicParentModifier(self):
        """ Gets the dynamic parenting modifier for the dynamic space setup on controller's side.
        
        Returns
        -------
        modo.Item
        """
        return self._dynaParent

    @property
    def matrixComposerModifiers(self):
        """ Gets all the matrix compose modifiers that connect to the dynamic parent modifier.
        
        Returns
        -------
        list of modo.Item
        """
        modifiers = []
        inputChan = self._dynaParent.channel('matrixInput')
        for x in xrange(inputChan.revCount):
            modifiers.append(inputChan.reverse(x).item)
        return modifiers

    def getMatrixComposeModifier(self, parentIndex):
        """ Gets matrix compose modifier for a given parent.
        
        Parameters
        ----------
        parentIndex : int
            Remember that parent indexing needs to start from 1 to be in line with
            dynamic parent modifier indexing!
        
        Returns
        -------
        modo.Item, None
            None is returned for index 0 which is world parent.
        
        Raises
        ------
        IndexError
            When bad index was provided.
        """
        if parentIndex < 1:
            return None
        inputChan = self._dynaParent.channel('matrixInput')
        if parentIndex > inputChan.revCount:
            raise IndexError
        linkIndex = parentIndex - 1
        return inputChan.reverse(linkIndex).item

    @property
    def setupItems(self):
        """ Gets all the items that are in the dynamic parenting setup.
        
        This includes compose modifiers for all linked parents.
        
        Returns
        -------
        list of modo.Item
        """
        setupItems = [self._dynaParent]
        parentChan = self._dynaParent.channel('matrixInput')
        parentCount = parentChan.revCount
        if parentCount == 0:
            return setupItems
        
        for x in xrange(parentCount):
            setupItems.append(self.getMatrixComposeModifier(x + 1))
        return setupItems

    @property
    def isAnimated(self):
        """ Tests whether the setup is already animated.
        
        It's considered animated when parent channel has an envelope on a current action.
        
        Returns
        -------
        bool
        """
        parentChan = self._dynaParent.channel('parent')
        return parentChan.isAnimated

    @isAnimated.setter
    def isAnimated(self, state):
        """ Adds/removes envelope for dynamic animation space setup.
        
        When an envelope is set it defaults to the rig space (parent 1).
        TODO: This needs to be solved for master controller which needs
        to be able to be dynamic but is the rig space itself.
        Should this simply take current parent?
        
        Parameters
        ----------
        state : bool
        """
        if state == self.isAnimated:
            return

        if state:
            run('!constraintParent.set 1 comp:true item:{%s}' % self._item.id)
        else:
            ChannelUtils.removeAnimation(self.animatedChannels)

    @property
    def draw(self):
        # Note that when you get channel with hints you will get string hint
        # rather then the int value.
        draw = self._dynaParent.channel('draw').get()
        if draw == 'off':
            return False
        return True
    
    @draw.setter
    def draw(self, value):
        """ Toggles drawing for dynamic parenting links.
        
        Toggling goes between Off and Selected.

        Parameters
        ----------
        draw : boolean
        """
        if not value:
            draw = 0 # off
        else:
            draw = 2 # selected
        self._dynaParent.channel('draw').set(draw, 0.0, False, lx.symbol.s_ACTIONLAYER_SETUP)
        
    # -------- Private methods

    @classmethod
    def _addDynamicParentModifier(self, childItem, name):
        """ Adds dynamic parent modifier to a given item.
        
        If dynamic parent modifier is already linked with the item
        new one is not added and the current one is returned instead.
        
        Parameters
        ----------
        childItem : modo.Item
        
        Returns
        -------
        modo.Item
            Dynamic parent modifier that was either created or found linked
            to the child item already.
        """
        dynaParent = ItemUtils.getParentConstraintItem(childItem)
        if dynaParent is not None:
            return dynaParent

        if name is None:
            name = childItem.name.replace(' ', '_')

        scene = modo.Scene()
        dynaParent = scene.addItem('cmDynamicParent', name + '_dynaParent')
        
        chanTo = childItem.channel('parentMatrix')
        chanFrom = dynaParent.channel('matrixOutput')
        chanFrom >> chanTo
        
        # Adding chanMods link is crucial for the dynamic parenting setup
        # to be seen properly by MODO.
        ItemUtils.addForwardGraphConnections(dynaParent, childItem, 'chanMods')
        return dynaParent

    @classmethod
    def _applyDynamicParentSetupValues(cls, dynaParentModoItem, index, offset, action):
        """
        Applies a set of values defining dynamic parent setup.
        """
        values = [index]
        values.extend(offset)
        actions = [action]

        # Setting on setup action is a special case.
        # We don't want to create keys and want to be on time 0.0
        # If channel is not animated yet we also set values on the scene action as well!
        # This is a hack, seems like setting parent on setup is causing strange issues
        # with the scene action. The proper solution would be clear values on scene action
        # reset them to setup but it can't be easily done via SDK and from setup mode.
        # For now we do this hack of copying setup values over to scene.
        if action == lx.symbol.s_ACTIONLAYER_SETUP:
            key = False
            time = 0.0
            dmod = DynamicParentModifier(dynaParentModoItem)
            if not dmod.parentChannel.isAnimated:
                actions.append(lx.symbol.s_ACTIONLAYER_ANIM)

        for action in actions:
            for x in xrange(len(cls.DYNA_PARENT_CHANNELS)):
                chan = dynaParentModoItem.channel(cls.DYNA_PARENT_CHANNELS[x])
                chan.set(values[x], time=time, key=key, action=action)

    @classmethod
    def _addMatrixCompose(self, parentItem):
        """ Adds matrix compose coming out from a given parent item.
        
        Returns
        -------
        modo.Item
            The matrix compose item. If the item did not exist it is added
            automatically.
        """
        matrixCompose = ItemUtils.getWorldMatrixComposeModifier(parentItem)
        
        if matrixCompose is None:

            scene = modo.Scene()
            matrixCompose = scene.addItem('cmMatrixCompose', 'Master Matrix Compose')
            ItemUtils.addForwardGraphConnections(matrixCompose, parentItem, 'chanMods')
                
            wpos = parentItem.channel('wposMatrix')
            wrot = parentItem.channel('wrotMatrix')
            wscl = parentItem.channel('wsclMatrix')
            mtxInput = matrixCompose.channel('matrixInput')
            
            # Create links to matrix Compose in the order in which
            # transforms should be evaluated.
            wscl >> mtxInput
            wrot >> mtxInput
            wpos >> mtxInput

        return matrixCompose

    def _setDynamicParentRestValues(self):
        channels = self.animatedChannels
        for chan in channels:
            ChannelUtils.setChannelSetupValue(chan)

    def _getParentItemFromMatrixCompose(self, matrixCompose):
        """ Gets parent item from a given matrix compose item.
        
        Returns
        -------
        modo.Item, None
            None is returned when matrix compose doesn't have any inputs coming from a parent item.
        """
        mtxInput = matrixCompose.channel('matrixInput')
        if mtxInput.revCount < 1:
            return None
        return mtxInput.reverse(0).item

    @classmethod
    def _calculateCompensationOffset(cls, childItem, parentItem=None):
        """ Calculates offset required for compensating an item for new dynamic parent.
        
        Note that this method works correctly with uniform scale only.
        
        Paramters
        ---------
        childItem : modo.Item
        
        parentItem : modo.Item, None, optional
            When parentItem is None world space is assumed.

        Returns
        -------
        list of 9 floats that constitute the offset:
           3 floats for position,
           3 floats for rotation angles in radians,
           3 floats for scale.
        """
        childLocalXfrm = modox.LocatorUtils.getItemLocalTransform(childItem)  # m4

        if parentItem is not None:
            parentWorldXfrm = modox.LocatorUtils.getItemWorldTransform(parentItem)  # m4
        else:
            parentWorldXfrm = modo.Matrix4()

        # Offset world is the world transform of child item as parented to new parent
        # without any compensation.
        # We need to invert this matrix and multiply child target world transform by this
        # inverted offset - this gives us the offset from new parent need to get child
        # item to its original world transform.
        offsetWorld = parentWorldXfrm * childLocalXfrm
        invOffsetWorld = offsetWorld.inverted()
        offsetMtx = childLocalXfrm * invOffsetWorld

        offsetValues = []
        offsetValues.extend(offsetMtx.position) 
        offsetValues.extend(offsetMtx.asEuler(degrees=False, order='xyz'))
        offsetValues.extend(offsetMtx.scale().values)  # scale returns modo.Vector3 for some reason

        return offsetValues

    def _fixParentConstraintInSetup(self):
        """ Fixes parent constraint in setup mode when parent was changed (Not used anymore).
        
        If you change parent constraint parent in setup mode MODO
        will still create a key on edit action. So it'll all work until edits are applied.
        At that moment the edits are applied NOT to setup (because you can't have keys there)
        but to scene or other current action. This breaks things up in setup mode.
        We solve this by reading all affected channel values right after switching parent,
        then clearing all the channels from animation and then reapplying values as static ones
        on setup action, meaning without creating keys for them.
        
        So this method HAS to be used on a constraint if the parent choice was switched
        in setup mode and the effect needs to be applied in setup correctly.
        This also HAS to be done before edits done to constraint channels by parent switching
        are applied!
        """
        parentConstraint = self.dynamicParentModifier
        if parentConstraint is None:
            return
        for channelName in self.DYNA_PARENT_CHANNELS:
            channel = parentConstraint.channel(channelName)
            value = channel.get(time=None, action=lx.symbol.s_ACTIONLAYER_EDIT)
            lx.eval('!channel.clear channel:{%s:%s}' % (parentConstraint.id, channelName))
            channel.set(value, 0.0, key=False, action=lx.symbol.s_ACTIONLAYER_SETUP)

    def __init__(self, childItem):
        dynaParent = ItemUtils.getParentConstraintItem(childItem)
        if dynaParent is None:
            raise TypeError
        self._dynaParent = dynaParent
        self._item = childItem


class DynamicParentModifier(object):
    
    @property
    def children(self):
        """ Gets a list of items that are driven by modifier.
        """
        outchan = self._item.channel('matrixOutput')
        items = [chan.item for chan in outchan.fwdLinked]
        return items

    @property
    def parentChannel(self):
        """ Gets the parent channel of the modifier.
        """
        return self._item.channel('parent')

    # -------- Private methods
    
    def __init__(self, modifierItem):
        self._item = modifierItem