

import lx
import modo


class FBIKSolver(object):
    """ Represents Full body IK solver item in modo.
    """
    
    @property
    def enabled(self):
        """ Tests whether solving is enabled.
        
        Any value greater then 0 considers IK to be enabled.
        """
        blendVal = self._modoItem.channel('iksIKFKBlend').get(time=0.0, action=lx.symbol.s_ACTIONLAYER_EDIT)
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
        self._modoItem.channel('iksIKFKBlend').set(blendVal, time=0.0, action=lx.symbol.s_ACTIONLAYER_SETUP)

    def backupSetupBlend(self):
        self._blendBkp = self._modoItem.channel('iksIKFKBlend').get(time=0.0, action=lx.symbol.s_ACTIONLAYER_SETUP)
        
    def restoreSetupBlend(self):
        try:
            self._modoItem.channel('iksIKFKBlend').set(self._blendBkp, time=0.0, action=lx.symbol.s_ACTIONLAYER_SETUP)
        except AttributeError:
            pass

    # -------- Private methods

    def __init__(self, modoItem):
        self._modoItem = modoItem


class FBIKChainItem(object):
    """ Represents an item in the full body ik chain.

    Raises
    ------
    TypeError
        When inappropriate item was passed for initialisation.
    """

    def updateRestPose(self):
        try:
            lx.eval('!ikfb.setRest item:{%s}' % self._modoItem.id)
            lx.out('ik rest pose updated')
        except RuntimeError:
            lx.out("Updating IK rest pose failed.")

    # -------- Private methods

    def __init__(self, modoItem):
        if not modoItem.internalItem.PackageTest('ik.joint'):
            raise TypeError

        self._modoItem = modoItem