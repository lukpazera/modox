

import lx
import lxu
import modo


class SceneUtils(object):
    
    @classmethod
    def findItemFast(cls, itemIdent):
        """ Finds an item in current scene using raw python API.
        
        Parameters
        ----------
        itemIdent : str
        
        Returns
        -------
        lxu.object.Item
        
        Raises
        ------
        LookupError
            When item cannot be found.
        """
        rawScene = lxu.select.SceneSelection().current()
        try:
            return rawScene.ItemLookup(itemIdent)
        except LookupError:
            raise


class FrameRange(object):
    SCENE = 'scene'
    CURRENT = 'current'
    WORK = 'work'


class TimeUtils(object):

    FrameRange = FrameRange

    @classmethod
    def getSceneFrameRange(cls, rangeType=FrameRange.CURRENT):
        """
        Gets one of frame ranges set in the scene.

        Returns
        -------
        int, int
        """
        startTime = lx.eval('time.range %s in:?' % rangeType)
        endTime = lx.eval('time.range %s out:?' % rangeType)

        valueService = lx.service.Value()
        startFrame = valueService.TimeToFrame(startTime)
        endFrame = valueService.TimeToFrame(endTime)

        return int(startFrame), int(endFrame)

    @classmethod
    def getChannelsTimeRange(cls, channels, action=lx.symbol.s_ACTIONLAYER_EDIT):
        """ Gets start and end time for a given set of channels.
        
        Parameters
        ----------
        channels : list of modo.Channel
        
        action : lx.symbol.s_ACTIONLAYER_XXX
            Action for which the time range should be calculated.
        
        Returns
        -------
        startTime : float
        endTime : float
        
        Raises
        ------
        ValueError
            When none of the channels is animated and has any time range.
        """
        startTime = 1000000.0
        endTime = -1000000.0
        animatedChannels = False
        
        for channel in channels:
            # Get envelope in the read only format set to a given action.
            # Can't user TD SDK for that as the envelope is always set
            # write access on edit action.
            chanRead = channel.item.Context().Channels(action, 0.0)
            if not chanRead.IsAnimated(channel.item, channel.index):
                continue
            rawEnv = chanRead.Envelope(channel.item, channel.index)
            env = modo.Envelope(rawEnv)

            animatedChannels = True
            keyframes = modo.Keyframes(env)
            keyframes.first()
            firstTime = keyframes.time
            keyframes.last()
            lastTime = keyframes.time
            
            if firstTime < startTime:
                startTime = firstTime
            
            if lastTime > endTime:
                endTime = lastTime
        
        if not animatedChannels:
            raise ValueError
        
        return startTime, endTime

    @classmethod
    def getChannelsFrameRange(cls, channels, action=lx.symbol.s_ACTIONLAYER_EDIT):
        """ Gets start and end frame for a given set of channels.

        Parameters
        ----------
        channels : list of modo.Channel

        action : lx.symbol.s_ACTIONLAYER_XXX
            Action for which the time range should be calculated.

        Returns
        -------
        startFrame : integer
        endFrame : integer

        Raises
        ------
        ValueError
            When none of the channels is animated and has any frame range.
        """
        try:
            startTime, endTime = cls.getChannelsTimeRange(channels, action)
        except ValueError:
            raise
        
        valueService = lx.service.Value()
        startFrame = valueService.TimeToFrame(startTime)
        endFrame = valueService.TimeToFrame(endTime)
        
        return startFrame, endFrame
