

import lx
import modo

import const as c
from item import ItemUtils


class CommandRegionPolygon(object):

    @property
    def gestures(self):
        """
        Gets all gesture items that are connected with this polygon region.

        Returns
        -------
        [CommandRegionGesture]
        """
        items = ItemUtils.getForwardGraphConnections(self._item, c.GraphName.COMMAND_REGION_REGION)
        gestures = []
        for item in items:
            try:
                gestures.append(CommandRegionGesture(item))
            except TypeError:
                pass

        return gestures

    @property
    def opacity(self):
        """
        Gets region opacity value.

        Note that value is read from 0.0 time as we assume this setting to be static.

        Returns
        -------
        float
        """
        return self._item.channel('cr_Color.A').get(0.0, lx.symbol.s_ACTIONLAYER_EDIT)

    @opacity.setter
    def opacity(self, value):
        """
        Sets opacity for the region.

        Note that we assume this setting to be static so the value is set directly on setup action.

        Parameters
        ----------
        value : float
            Opacity value in 0-1.0 range.
        """
        self._item.channel('cr_Color.A').set(value, 0.0, key=False, action=lx.symbol.s_ACTIONLAYER_SETUP)

    @property
    def tooltip(self):
        """
        Reads command region tooltip.

        Returns
        -------
        str
        """
        return self._item.channel('cr_DisplayText').get(0.0, lx.symbol.s_ACTIONLAYER_EDIT)

    @tooltip.setter
    def tooltip(self, tooltipText):
        """
        Sets command region tooltip.

        Parameters
        ----------
        tooltipText : str
        """
        self._item.channel('cr_DisplayText').set(tooltipText, 0.0, key=False, action=lx.symbol.s_ACTIONLAYER_SETUP)

    # -------- Private methods

    def __init__(self, modoItem):
        if modoItem.type != c.ItemType.COMMAND_REGION_POLYGON:
            raise TypeError
        self._item = modoItem


class CommandRegionGesture(object):

    @property
    def commands(self):
        """
        Gets a list of command items that are connected with this gesture.

        Returns
        -------
        [CommandRegionCommand]
        """
        items = ItemUtils.getForwardGraphConnections(self._item, c.GraphName.COMMAND_REGION_GESTURE)
        commands = []
        for item in items:
            try:
                commands.append(CommandRegionCommand(item))
            except TypeError:
                pass

        return commands

    # -------- Private methods

    def __init__(self, modoItem):
        if modoItem.type != c.ItemType.COMMAND_REGION_GESTURE:
            raise TypeError
        self._item = modoItem


class CommandRegionCommand(object):

    @property
    def itemSelection(self):
        """
        Gets a list of items that this command selects.

        Returns
        -------
        [modo.Item]
        """
        return ItemUtils.getReverseGraphConnections(self._item, c.GraphName.COMMAND_REGION_ITEM_SELECTION)

    @property
    def commandString(self):
        """
        Gets the string of the command to be executed.

        Returns
        -------
        str
        """
        return self._item.channel('crc_Command').get(time=0.0, action=lx.symbol.s_ACTIONLAYER_SETUP)

    @commandString.setter
    def commandString(self, commandString):
        """
        Sets command string on the region command node.

        Parameters
        ----------
        commandString : str, None
            Pass None to clear the command out.

        """
        if commandString is None:
            commandString = ''
        self._item.channel('crc_Command').set(commandString, time=0.0, key=False, action=lx.symbol.s_ACTIONLAYER_SETUP)

    @property
    def modoItem(self):
        return self._item

    # -------- Private methods

    def __init__(self, modoItem):
        if modoItem.type != c.ItemType.COMMAND_REGION_COMMAND:
            raise TypeError
        self._item = modoItem
