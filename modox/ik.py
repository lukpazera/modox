

import lx
import modo

import const as c
from run import run
from locator import LocatorUtils


class IKUtils(object):

    @classmethod
    def disableIK(cls):
        """
        Disables IK.

        Note that you'll get command failed log output when there are no ik solvers
        in scene or you're not in setup mode.
        """
        run('!ik.disable 1')

    @classmethod
    def enableIK(cls):
        """
        Enables IK back.

        Note that you'll get command failed log output when there are no ik solvers
        in scene or you're not in setup mode.
        """
        run('!ik.disable 0')


class IKSwitchDirection(object):
    TO_FK = "fk"
    TO_IK = "ik"


class IKSetupType(object):
    BAR2 = 1
    BAR3 = 2


class IK23BarSolver(object):
    """ Represents standard IK solver modifier item in modo.
    
    Parameters
    ----------
    modoItem : modo.Item
        The solver modifier item.
    
    Raises
    ------
    TypeError
        When bad item was passed as initialiser.
    """
    
    _SOLVER_ITEM_TYPE = c.ItemType.IK_23BAR_SOLVER
    _CHAN_BLEND = 'blend'
    _CHAN_ANGLE_BIAS = 'weightA'
    _CHAN_SETUP_ANGLE_BIAS = 'weightASet'
    _CHAN_GLOBAL_ORIENT = 'orient'
    _CHAN_LOWER_ORIENT = 'orient2'
    _CHAN_UPPER_ORIENT = 'orient3'
    _CHAN_UPPER_OUT = 'matrixOutput'
    _CHAN_MIDDLE_OUT = 'matrixOutput2'
    _CHAN_LOWER_OUT = 'matrixOutput7'
    _CHAN_END_OUT = 'matrixOutput6'
    _CHAN_ROOT_IN = 'rootWPos'

    Type = IKSetupType

    @property
    def enabled(self):
        """ Tests whether solving is enabled.
        
        Any value greater then 0 considers IK to be enabled.
        """
        blendVal = self._modoItem.channel(self._CHAN_BLEND).get(time=0.0, action=lx.symbol.s_ACTIONLAYER_EDIT)
        if blendVal > 0.0:
            return True
        else:
            return False

    @enabled.setter
    def enabled(self, state):
        """ Sets IK solving on/off.
        
        This really changes the ik blend channel value between 0% and 100%.
        
        Parameters
        ----------
        state : bool
        """
        if state:
            blendVal = 1.0
        else:
            blendVal = 0.0
        self._modoItem.channel(self._CHAN_BLEND).set(blendVal, time=0.0, action=lx.symbol.s_ACTIONLAYER_SETUP)

    @property
    def setupAngleBias(self):
        return self._modoItem.channel(self._CHAN_SETUP_ANGLE_BIAS).get(time=0.0, action=lx.symbol.s_ACTIONLAYER_EDIT)
        
    @setupAngleBias.setter
    def setupAngleBias(self, value):
        """ Gets/sets setup angle bias value.
        """
        # DEV NOTE : It seems to be crucial to store the value on edit action and not setup!
        # Setting it straight to setup action did not work properly.
        # Find out why some day.
        self._modoItem.channel(self._CHAN_SETUP_ANGLE_BIAS).set(value, time=0.0, action=lx.symbol.s_ACTIONLAYER_EDIT)
        
    @property
    def modoItem(self):
        """ Gets ik solver modo item.
        
        Returns
        -------
        modo.Item
        """
        return self._modoItem

    @property
    def goal(self):
        """
        Gets IK's goal item.

        Returns
        -------
        modo.Item, None
        """
        chan = self.modoItem.channel("goalWPos")
        if chan is None:
            return None
        if chan.revCount == 0:
            return None
        return chan.reverse(0).item

    @property
    def type(self):
        """ Gets type of the setup, either 2 bar or 3 bar.

        Returns
        -------
        IK23BarSetup.Type.XXX
        """
        try:
            lowerInputChan = self.modoItem.channel(self._CHAN_LOWER_OUT).forward(0)
        except LookupError:
            return self.Type.BAR2
        return self.Type.BAR3

    @property
    def switchKeyChannels(self):
        """
        Gets a list of channels on solver item that get keyframed during ik/fk switching.

        Returns
        -------
        [modo.Channel]
        """
        if self.type == self.Type.BAR2:
            chanNames = [self._CHAN_BLEND, self._CHAN_GLOBAL_ORIENT]
        else:
            chanNames = [self._CHAN_BLEND,
                         self._CHAN_ANGLE_BIAS,
                         self._CHAN_GLOBAL_ORIENT,
                         self._CHAN_LOWER_ORIENT,
                         self._CHAN_UPPER_ORIENT]
        return [self.modoItem.channel(name) for name in chanNames]

    def backupSetupBlend(self):
        self._blendBkp = self._modoItem.channel(self._CHAN_BLEND).get(time=0.0, action=lx.symbol.s_ACTIONLAYER_SETUP)
        
    def restoreSetupBlend(self):
        try:
            self._modoItem.channel(self._CHAN_BLEND).set(self._blendBkp, time=0.0, action=lx.symbol.s_ACTIONLAYER_SETUP)
        except AttributeError:
            pass

    def resetFromFK(self):
        """ Resets IK chain from FK Rest pose.
        
        Does not reset the goal.
        """
        try:
            lx.eval('!ik.apply Bar23 reset:true item:{%s} resetGoal:false' % self._modoItem.id)
        except RuntimeError:
            lx.out('Resetting IK failed!')

    def switch(self, direction):
        """
        Switches chain to either IK or FK mode using current action and current time.
        Keys are created for all channels that switching will affect.

        Parameters
        ----------
        direction : str
            One of IKFKSwitchDirection constants.
        """
        try:
            lx.eval('!ik.scanIKFKChannels item:{%s} mode:setKey' % self.modoItem.id)
            lx.eval('!ik.switchIKFK item:{%s} mode:{%s}' % (self.modoItem.id, direction))
        except RuntimeError:
            pass

    @property
    def hasUpVector(self):
        """
        Tests whether this IK solver has up transform plugged.

        Returns
        -------
        bool
        """
        chan = self._modoItem.channel('up')
        return chan.revCount > 0

    @property
    def upVectorItem(self):
        """
        Gets up vector item for the solver.

        Returns
        -------
        modo.Item, None
            None is returned if no up transform is plugged into solver.
        """
        chan = self._modoItem.channel('up')
        if chan.revCount < 1:
            return None
        return chan.reverse(0).item

    @upVectorItem.setter
    def upVectorItem(self, modoItem):
        """
        Sets new or clears up transforms for the solver.

        Parameters
        ----------
        modoItem : modo.Item, None
            Up vector item or None to clear up transform connection from solver.
        """
        # Clear connection first.
        chan = self._modoItem.channel('up')
        if chan.revCount > 0:
            inputChan = chan.reverse(0)
            inputChan.deleteLink(chan)

        if modoItem is not None:
            chan = LocatorUtils.getItemWorldPositionMatrixChannel(modoItem)
            chan >> self._modoItem.channel('up')

    # -------- Private methods

    def __init__(self, modoItem):
        if modoItem.type != self._SOLVER_ITEM_TYPE:
            raise TypeError
        self._modoItem = modoItem


class IK23BarSetup(object):
    """ Represents entire IK setup.
    """
    
    _CHAN_UPPER_OUT = 'matrixOutput'
    _CHAN_MIDDLE_OUT = 'matrixOutput2'
    _CHAN_LOWER_OUT = 'matrixOutput7'
    _CHAN_END_OUT = 'matrixOutput6'
    _CHAN_ROOT_IN = 'rootWPos'
    
    Type = IKSetupType
    
    @classmethod
    def apply(cls, items):
        """ Applies IK over given items.
        
        Items need to form a hierarchy.
        
        Parameters
        ----------
        items : list of modo.Item
        """
        scene = modo.Scene()
        scene.select(items, add=False)
        lx.eval('ik.apply 1') # to apply 23bar ik.
        items = scene.selected
        solver = items[0]
        goal = items[1]
        return cls(solver)
        
    @property
    def chain(self):
        """ Gets ik joints list.
        
        These will be 3 items (2 bar ik) or 4 items (3 bar ik).
        """
        solverItem = self._ikSolver.modoItem
        chain = []
        channels = [self._CHAN_UPPER_OUT,
                    self._CHAN_MIDDLE_OUT,
                    self._CHAN_LOWER_OUT,
                    self._CHAN_END_OUT]
        
        for chan in channels:
            try:
                chain.append(solverItem.channel(chan).forward(0).item)
            except LookupError:
                continue
        return chain
        
    @property
    def type(self):
        """ Gets type of the setup, either 2 bar or 3 bar.
        
        Returns
        -------
        IK23BarSetup.Type.XXX
        """
        return self.solver.type
    
    @property
    def solver(self):
        """ Gets IK solver modifier object.
        
        Returns
        -------
        IK23BarSolver
        """
        return self._ikSolver

    @property
    def rootModoItem(self):
        """ Gets IK setup root item.
        
        Returns
        -------
        modo.Item
        """
        try:
            return self._ikSolver.modoItem.channel(self._CHAN_ROOT_IN).reverse(0).item
        except LookupError:
            return None
        
    def selfDelete(self):
        root = self.rootModoItem
        if root is not None:
            lx.eval('!item.delete child:1 item:{%s}' % root.id)

    # -------- Private methods
    
    def __init__(self, iksolver):
        if not isinstance(iksolver, IK23BarSolver):
            try:
                iksolver = IK23BarSolver(iksolver)
            except TypeError:
                raise
        self._ikSolver = iksolver