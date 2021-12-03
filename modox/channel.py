

import lx
import modo


class ChannelUtils(object):

    POS_CHANNELS = ['pos.X', 'pos.Y', 'pos.Z']
    ROT_CHANNELS = ['rot.X', 'rot.Y', 'rot.Z']
    SCALE_CHANNELS = ['scl.X', 'scl.Y', 'scl.Z']

    TRANSFORM_CHANNELS = POS_CHANNELS + ROT_CHANNELS + SCALE_CHANNELS

    @classmethod
    def isUserChannel(cls, channel):
        """ Tests whether given channel is user channel.
        
        Parameters
        ----------
        channel : modo.Channel
        
        Returns
        -------
        boolean
        """
        index = channel.index
        item = channel.item.internalItem
        try:
            package = item.ChannelPackage(index)
        except LookupError:
            return True
        return False

    @classmethod
    def belongsToPackage(cls, channel, packageName):
        """
        Tests if channel belongs to a given package.

        Parameters
        ----------
        packageName : str
            Name of the package to test against.

        Returns
        -------
        bool
        """
        try:
            return channel.item.internalItem.ChannelPackage(channel.index) == packageName
        except LookupError:
            return False
        return False

    @classmethod
    def getPackageName(cls, channel):
        """
        Gets name of the package that given channel belongs to.

        Parameters
        ----------
        channel : modo.Channel

        Returns
        -------
        str, None
            None is returned when channel doesn't belong to any package (is user channel).
        """
        try:
            return channel.item.internalItem.ChannelPackage(channel.index)
        except LookupError:
            pass
        return None

    @classmethod
    def isNumericChannel(cls, channel):
        """ Tests whether given channel is numeric channel.
        
        Parameters
        ----------
        channel : modo.Channel
        
        Returns
        -------
        boolean
        """
        t = channel.type
        return t in [1, 2, 3]

    @classmethod
    def isBooleanChannel(cls, channel):
        """
        Checks whether given channel is of boolean storage type.

        Returns
        -------
        bool
        """
        return channel.storageType == 'boolean'

    @classmethod
    def isDivider(cls, channel):
        """ Tests whether given channel is divider.
        
        Note that this is hacky implementation.
        This could potentially include other non-standard channel types.
        Watch out for this in future.
        """
        t = channel.type
        st = channel.storageType
        return (st is None and t == 5)

    @classmethod
    def getChannelUsername(self, channel):
        """ Gets username of an item channel.
        
        Parameters
        ----------
        channel : modo.Channel

        Returns
        -------
        str
        """
        chanService = lx.service.ChannelUI()
        return chanService.ChannelUserName(channel.item.internalItem, channel.index)

    @classmethod
    def setChannelName(cls, channel, name):
        lx.eval('channel.name channel:{%s:%s} name:{%s}' % (channel.item.id, channel.name, name))

    @classmethod
    def setChannelUsername(cls, channel, name):
        lx.eval('channel.username channel:{%s:%s} username:{%s}' % (channel.item.id, channel.name, name))

    @classmethod
    def getChannelIdent(cls, channel):
        """
        Gets channels string ident as used in MODO commands.

        Returns
        -------
        str
        """
        return channel.item.id + ':' + channel.name

    @classmethod
    def getNumericItemChannels(cls, modoItem):
        """
        Gets a list of numberic channels that are specific to just that item type.
        Only integer, float and gradient channels are supported.

        Returns
        -------
        [modo.Channel]
        """
        rawItem = modoItem.internalItem
        itemType = modoItem.type
        chanCount = rawItem.ChannelCount()
        itemChans = []
        for x in xrange(chanCount):
            # Channel type 1 is integer, 2 is float, 3 is gradient.
            # Check modox.ChannelType for full list.
            if rawItem.ChannelPackage(x) == itemType and rawItem.ChannelType(x) in (1, 2, 3):
                itemChans.append(modo.Channel(x, modoItem))
        return itemChans

    @classmethod
    def getNumericItemChannelNames(cls, modoItem):
        """
        Gets a list of names of channels that are specific to just that item type.
        Only integer, float and gradient channels are supported.
        
        Returns
        -------
        [str]
        """
        rawItem = modoItem.internalItem
        itemType = modoItem.type
        chanCount = rawItem.ChannelCount()
        itemChans = []
        for x in xrange(chanCount):
            # Channel type 1 is integer, 2 is float, 3 is gradient.
            # Check modox.ChannelType for full list.
            if rawItem.ChannelPackage(x) == itemType and rawItem.ChannelType(x) in (1, 2, 3):
                itemChans.append(rawItem.ChannelName(x))
        return itemChans

    @classmethod
    def getRawChannelValue(cls, channel, time=None, action=lx.symbol.s_ACTIONLAYER_EDIT):
        """
        Gets raw channel value.

        This function is only really applicable if you want to always get raw int channel value,
        even if channel has hints defined. Default modo.Channel.get() method will get you
        string hint automatically for int channel if it has hints defined.
        This is not always need - you this function in such case.

        Parameters
        ----------
        channel : modo.Item

        time : float, None
            Pass None for current time.

        action : str
            One of lx.symbol.s_ACTIONLAYER_XXX constants.

        Returns
        -------
        float, int, str, obj
        """
        item = channel.item
        index = channel.index
        chanRead = item.scene.chanRead
        chanRead.set(action, time)
        chanType = chanRead.Type(item, index)

        if chanType == lx.symbol.i_TYPE_FLOAT:
            return chanRead.Double(item, index)

        if chanType == lx.symbol.i_TYPE_INTEGER:
            return chanRead.Integer(item, index)

        if chanType == lx.symbol.i_TYPE_STRING:
            return chanRead.String(item, index)

        return chanRead.ValueObj(item, index)

    @classmethod
    def mirrorChannel(cls, channel):
        """
        Mirrors channel values and slopes.

        This functions works on edit (current) action only.
        Only float and integer channels are supported.

        Parameters
        ----------
        channel : modo.Channel
        """
        # TODO:  This mirroring keys code should be moved to separate KeyframeUtils function one day.
        channelType = channel.type
        if channel.isAnimated:
            key = channel.envelope.Enumerator()

            key.First()

            while True:
                breakFlags, valueSide = key.GetBroken()
                brokenValue = breakFlags & lx.symbol.fKEYBREAK_VALUE

                if channelType == 1:  # integer
                    if brokenValue:
                        valueIn = key.GetValueI(lx.symbol.iENVSIDE_IN) * -1
                        valueOut = key.GetValueI(lx.symbol.iENVSIDE_OUT) * -1
                        # The order of setting values is important here
                        # and depends on valueSide value.
                        if valueSide == lx.symbol.iENVSIDE_IN:
                            key.SetValueI(valueOut, lx.symbol.iENVSIDE_OUT)
                            key.SetValueI(valueIn, lx.symbol.iENVSIDE_IN)
                        elif valueSide == lx.symbol.iENVSIDE_OUT:
                            key.SetValueI(valueIn, lx.symbol.iENVSIDE_IN)
                            key.SetValueI(valueOut, lx.symbol.iENVSIDE_OUT)
                    else:
                        value = key.GetValueI(lx.symbol.iENVSIDE_BOTH) * -1
                        key.SetValueI(value, lx.symbol.iENVSIDE_BOTH)

                elif channelType == 2:  # float
                    if brokenValue:
                        valueIn = key.GetValueF(lx.symbol.iENVSIDE_IN) * -1.0
                        valueOut = key.GetValueF(lx.symbol.iENVSIDE_OUT) * -1.0
                        if valueSide == lx.symbol.iENVSIDE_IN:
                            key.SetValueF(valueOut, lx.symbol.iENVSIDE_OUT)
                            key.SetValueF(valueIn, lx.symbol.iENVSIDE_IN)
                        elif valueSide == lx.symbol.iENVSIDE_OUT:
                            key.SetValueF(valueIn, lx.symbol.iENVSIDE_IN)
                            key.SetValueF(valueOut, lx.symbol.iENVSIDE_OUT)
                    else:
                        value = key.GetValueF(lx.symbol.iENVSIDE_BOTH) * -1.0
                        key.SetValueF(value, lx.symbol.iENVSIDE_BOTH)

                    # Mirror slopes too
                    slopeIn = key.GetSlope(lx.symbol.iENVSIDE_IN) * -1.0
                    key.SetSlope(slopeIn, lx.symbol.iENVSIDE_IN)

                    slopeOut = key.GetSlope(lx.symbol.iENVSIDE_OUT) * -1.0
                    key.SetSlope(slopeOut, lx.symbol.iENVSIDE_OUT)

                try:
                    key.Next()
                except LookupError:
                    break

        else:
            # For static channel we simply get a value and mirror it.
            if channelType == 1:  # integer
                value = channel.get()
                value *= -1
                channel.set(value=value, key=False)
            elif channelType == 2:  # float
                value = channel.get()
                value *= -1.0
                channel.set(value=value, key=False)

    @classmethod
    def setChannelSetupValue(self, channels):
        """ Sets channel's setup value from current channel value.
        
        Note that this should be called with setup mode on.

        Parameters
        ----------
        channel : modo.Channel
        """
        if type(channels) not in (list, tuple):
            channels = [channels]
        
        for channel in channels:
            chanString = "%s:%s" % (channel.item.id, channel.name)
            lx.eval('!channel.setup channel:{%s}' % (chanString))
    
    @classmethod
    def clearAnimation(self, channels):
        """ Clears animation for given channels.
        
        Clearing animation will get channels back to their setup/default values (or to 0).
        NOTE: This wipes out assigned setup values so DO NOT USE THIS
        if you want to preserve assigned setup value on a channel!!!
        The effect is that you loose separate setup/scene values after using this.
        You will be left with just the setup/default value so when you change channel
        on scene action the change will be applied to setup (as there won't be
        assigned setup value that can't be changed anymore).

        Parameters
        ----------
        channels : modo.Channel, list of modo.Channel
        """
        if type(channels) not in (list, tuple):
            channels = [channels]

        for chan in channels:
            chanString = "%s:%s" % (chan.item.id, chan.name)
            # channel.clear will throw an exception when ran on a channel
            # that is not animated.
            try:
                lx.eval('!channel.clear anim:false channel:{%s}' % (chanString))
            except RuntimeError:
                pass
            
    @classmethod
    def removeAnimation(self, channels):
        """ Removes animation from given channels.
        
        Removing animation will delete envelopes but will preserve
        channel values at a current time.
        
        Parameters
        ----------
        channels : modo.Channel, list of modo.Channel
        """
        if type(channels) not in (list, tuple):
            channels = [channels]
        
        for chan in channels:
            chanString = "%s:%s" % (chan.item.id, chan.name)
            try:
                lx.eval('!channel.clear anim:true channel:{%s}' % (chanString))        
            except RuntimeError:
                pass

    @classmethod
    def resetChannelsToDefault(cls, channels):
        """
        Resets given channels to default values.
        In case of user channels a default value for channel is pulled.
        All other channels are reset to their setup action values.

        Parameters
        ----------
        channels : modo.Channel, [modo.Channel]
        """
        if type(channels) not in (list, tuple):
            channels = [channels]

        for chan in channels:
            chanString = "%s:%s" % (chan.item.id, chan.name)
            if cls.isUserChannel(chan):
                val = str(lx.eval('!channel.default channel:{%s} val:?' % chanString))
            else:
                # Reset channel to value from setup.
                val = chan.get(0.0, lx.symbol.s_ACTIONLAYER_SETUP)
            lx.eval('!channel.value %s mode:set channel:{%s}' % (str(val), chanString))

    @classmethod
    def isTransformChannel(self, channel):
        """ Tests whether given channel is a transform channel.
        
        Parameters
        ----------
        channel : modo.Channel
        
        Returns
        -------
        bool
        """
        return channel.name in self.TRANSFORM_CHANNELS
    
    @classmethod
    def isTransformChannelName(self, channelName):
        """ Tests whether given channel name is one of transform channels names.
        
        Paramters
        ---------
        channelName : str
        
        Returns
        -------
        bool
        """
        return channelName in self.TRANSFORM_CHANNELS

    @classmethod
    def removeAllForwardConnections(self, channels):
        """ Removes all forward connections from a given channel.
        
        Parameters
        ----------
        channel : modo.Item
        """
        if type(channels) not in (list, tuple):
            channels = [channels]

        for channel in channels:
            count = channel.fwdCount
            if count == 0:
                return
            for x in xrange(count - 1, -1, -1):
                toChan = channel.forward(x)
                channel << toChan

    @classmethod
    def removeAllReverseConnections(self, channels):
        """ Removes all reverse connections from a given channel(s).
    
        Parameters
        ----------
        channel : modo.Item
        """
        if type(channels) not in (list, tuple):
            channels = [channels]

        for channel in channels:
            count = channel.revCount
            if count == 0:
                return
            for x in xrange(count - 1, -1, -1):
                fromChan = channel.reverse(x)
                fromChan << channel

    @classmethod
    def getSourceDrivingChannel(cls, channel):
        """
        Gets the furthermost channel in the channels graph that drives given channel.

        Returns
        -------
        modo.Channel, None
        """
        count = channel.revCount
        if count == 0:
            return None
        sourceChan = channel.reverse(0)
        while True:
            count = sourceChan.revCount
            if count == 0:
                break
            sourceChan = sourceChan.reverse(0)
        return sourceChan

    @classmethod
    def getInputChannel(cls, channel, index=0):
        """
        Gets channel that is an input for another channel.

        Parameters
        ----------
        channel : modo.Channel

        index : int, optional
            Optional input channel index. 0 by default.
            You only need to give an index when channel can have multiple inputs.

        Returns
        -------
        modo.Channel, None
            None is returned when there is no input at given index.
        """
        count = channel.revCount
        if count == 0:
            return None
        try:
            return channel.reverse(index)
        except IndexError:
            pass
        return None

    @classmethod
    def getOutputChannel(cls, channel, index=0):
        """
        Gets channel that is an output of another channel.

        Parameters
        ----------
        channel : modo.Channel

        index : int, optional
            Optional output channel index. 0 by default.
            You only need to give an index when channel has multiple outputs.

        Returns
        -------
        modo.Channel, None
            None is returned when there is no output at given index.
        """
        count = channel.fwdCount
        if count == 0:
            return None
        try:
            return channel.forward(index)
        except IndexError:
            pass
        return None

    @classmethod
    def getChannelInputItem(cls, channel, index=0):
        """
        Gets the item that contains channel driving given channel.

        Parameters
        ----------
        channel : modo.Item

        index : int, optional
            Optional input connection index, 0 by default.
            
        Returns
        -------
        modo.Item, None
        """
        sourceChan = cls.getInputChannel(channel, index)
        if sourceChan is not None:
            return sourceChan.item
        return None

    @classmethod
    def hasKeyframeOnTimeAndAction(self, channel, time=None, action=lx.symbol.s_ACTIONLAYER_EDIT):
        if time is None:
            time = lx.service.Selection().GetTime()
        scene = lx.object.Scene(channel.item.internalItem.Context())
        chanRead = lx.object.ChannelRead(scene.Channels(action, time))
        
        # IsAnimated can apparently be used as well as it seems to only check on the action
        # channel read was initialised with.
        # return bool(chanRead.IsAnimated(channel.item.internalItem, channel.index))
        try:
            env = lx.object.Envelope(chanRead.Envelope(channel.item.internalItem, channel.index))
        except LookupError:
            return False
        
        key = lx.object.Keyframe(env.Enumerator())
        try:        
            key.Find(time, lx.symbol.iENVSIDE_BOTH)
        except LookupError:
            return False
        
        return True
    