

import lx
import lxu
import modo


class SetupMode(object):
    """ Manages Setup Mode in current scene.
    """

    @property
    def state(self):
        return self.scene.SetupMode()

    @state.setter
    def state(self, value):
        """Sets setup mode to desired state.

        Setup state is changed only if required state is different from
        the current state.
        This is important because setting setup mode to the same value
        that it already has resets timeline to frame 0.

        Parameters
        ----------
        value : boolean
        """
        currentState = self.scene.SetupMode()
        if currentState != value:
            lx.eval('!anim.setup %d' % int(value))

    def store(self):
        """ Stores setup mode state.
        """
        self.stateBackup = self.scene.SetupMode()

    def restore(self):
        """ Restores Setup Mode state.

        Restore is done only if a state was previously stored
        and the stored state is different from the current one.
        """
        if self.stateBackup is None:
            return False
        if self.scene.SetupMode() == self.stateBackup:
            return False
        
        lx.eval('!anim.setup %d' % self.stateBackup)
        return True

    def __init__ (self):
        self.stateBackup = None
        self.scene = lx.object.Scene(lxu.select.SceneSelection().current())
        