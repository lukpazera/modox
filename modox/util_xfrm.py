

import lx
import modo


class TransformToolsUtils(object):
    """ Utility class for switching transform tools on/off.
    """

    POS_CHANNELS = ['pos.X', 'pos.Y', 'pos.Z']
    ROT_CHANNELS = ['rot.X', 'rot.Y', 'rot.Z']
    SCALE_CHANNELS = ['scl.X', 'scl.Y', 'scl.Z']

    def autoFromChannels(self, xfrmChannels):
        """ Enables transform tools based on given channels list.
        
        If only position or rotation or scale channels are passed
        relevant move/rotate/scale tool will be enabled.
        If channels combine different transforms the item transform
        tool will be enabled.
        
        Parameters
        ----------
        xfrmChannels : list of modo.Channel
        """
        xfrmChanNames = [chan.name for chan in xfrmChannels]

        doMove = self._testChannels(self.POS_CHANNELS, xfrmChanNames)
        doRotate = self._testChannels(self.ROT_CHANNELS, xfrmChanNames)
        doScale = self._testChannels(self.SCALE_CHANNELS, xfrmChanNames)

        transforms = int(doMove) + int(doRotate) + int(doScale)
        if transforms == 1:
            self._setSingleTransformTool(doMove, doRotate, doScale)
        elif transforms > 1:
            self._setTransformItemTool()

    def getToolItemCommandStringFromChannels(self, xfrmChannels):
        """
        Gets a command to put into item command string that will enable transform tool
        based on channels passed as argument.

        This is the same as autoFromChannels() but instead of setting the tool it's evaluating
        command string to set as item command to enable the tool.

        Parameters
        ----------
        xfrmChannels : [modo.Channel]

        Returns
        -------
        str, None
        """
        xfrmChanNames = [chan.name for chan in xfrmChannels]

        doMove = self._testChannels(self.POS_CHANNELS, xfrmChanNames)
        doRotate = self._testChannels(self.ROT_CHANNELS, xfrmChanNames)
        doScale = self._testChannels(self.SCALE_CHANNELS, xfrmChanNames)

        transforms = int(doMove) + int(doRotate) + int(doScale)
        if transforms == 1:
            if doMove:
                return self.getMoveItemCommandString(True)
            elif doRotate:
                return self.getRotateItemCommandString(True)
            elif doScale:
                return self.getScaleItemCommandString(True)
        elif transforms > 1:
            return self.getTransformItemCommandString(True)
        return None

    @property
    def moveItem(self):
        return lx.eval('!tool.set TransformMove ?') == 'on'
    
    @moveItem.setter
    def moveItem(self, state):
        lx.eval('!tool.set TransformMove %d' % int(state))

    def getMoveItemCommandString(self, state):
        return 'eval {tool.set TransformMoveItem %d}' % int(state)

    @property
    def rotateItem(self):
        return lx.eval('!tool.set TransformRotate ?') == 'on'
    
    @rotateItem.setter
    def rotateItem(self, state):
        lx.eval('!tool.set TransformRotate %d' % int(state))

    def getRotateItemCommandString(self, state):
        return 'eval {tool.set TransformRotateItem %s}' % int(state)

    @property
    def scaleItem(self):
        return lx.eval('!tool.set TransformScale ?') == 'on'
    
    @scaleItem.setter
    def scaleItem(self, state):
        lx.eval('!tool.set TransformScale %d' % int(state))

    def getScaleItemCommandString(self, state):
        return 'eval {tool.set TransformScaleItem %s}' % int(state)

    @property
    def transformItem(self):
        return lx.eval('!tool.set Transform ?') == 'on'

    @transformItem.setter
    def transformItem(self, state):
        lx.eval('!tool.set Transform %d' % int(state))

    def getTransformItemCommandString(self, state):
        return 'eval {tool.set TransformItem %d}' % int(state)

    @property
    def childCompensation(self):
        """ Gets child compensation for current transform tool.
        
        Be sure to set the given tool to enabled first.
        
        Returns
        -------
        bool
        """
        return bool(lx.eval('!tool.attr xfrm.transform comp ?'))
    
    @childCompensation.setter
    def childCompensation(self, state):
        """ Sets child compensation for current transform tool.
        
        Make sure the tool is enabled first.
        
        Parameters
        ----------
        state : bool
        """
        lx.eval('!tool.attr xfrm.transform comp %d' % state)
    
    def drop(self):
        lx.eval('tool.drop')

    # -------- Private methods

    def _setSingleTransformTool(self, move, rotate, scale):
        if move:
            if not self.moveItem:
                self.moveItem = True
        elif rotate:
            if not self.rotateItem:
                self.rotateItem = True
        elif scale:
            if not self.scaleItem:
                self.scaleItem = True

    def _setTransformItemTool(self):
        if not self.transformItem:
            self.transformItem = True

    def _testChannels(self, chansToTest, chanList):
        """ Tests if any of given channels to test is on the channel list.
        
        Note that arguments for this method are channel names not channel objects!
        
        Parameters
        ----------
        chansToTest : list of str
            List of names of channels to test against being on the channels list.
        chanList : list of str
            List of names of channels that the other list will be tested against.
        
        Returns
        -------
        bool
        """
        for chanName in chansToTest:
            if chanName in chanList:
                return True
        return False