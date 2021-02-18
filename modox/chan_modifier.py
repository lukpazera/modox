

import lx
import modo

import select
import item
from run import run


class ChannelModifierUtils(object):

    @classmethod
    def attachModifierToItem(cls, modifierModoItem, hostModoItem):
        """
        Allows for attaching modifier to locator type item.

        Attached item will show up under the locator item in item list
        (you can unfold it with a little plus icons next to item name in item list).
        Attached modifiers are getting deleted together with locator they are attached to.

        Parameters
        ----------
        modifierModoItem : modo.Item
            Modifier item that you want to attach.

        hostModoItem : modo.Item
            Locator type item you want to attach modifier to.
        """
        item.ItemUtils.addForwardGraphConnections(modifierModoItem, hostModoItem, 'chanMods')


class TransformConstraintOperation(object):
    POSITION = 'pos'
    ROTATION = 'rot'
    SCALE = 'scl'


class CMTransformConstraint(object):
    """
    This class represents Transform Constraint channel modifier.

    Parameters
    ----------
    modoItem : modo.Item
        The constraint modo item.
    """
    Operation = TransformConstraintOperation

    @classmethod
    def new(cls, assemblyItem, hostItem, name='TransformConstraint'):
        """
        Adds new transform constraint to the scene.
        
        Parameters
        ----------
        assemblyItem : modo.Item
            This is assembly item to which the constraint will be added.
            Passing this item is mandatory. However, if you don't want to add constraints
            to any assembly pass an item that is not a group.
            This doesn't throw an error and it doesn't add constraint to any groups either.
            
        hostItem : modo.Item
            Constraint can be attached to an item such that it'll be under this item
            in item list. It'll also get deleted when the host item is deleted.

        name : str
            Name for new constraint item.
            
        Returns
        -------
        CMTransformConstraint
        """
        itemSelection = select.ItemSelection()
        itemSelection.clear()

        run('modifier.create "cmTransformConstraint:rot" item:{%s} insert:false' % assemblyItem.id)
        cnsItem = itemSelection.getOfTypeModo("cmTransformConstraint")[0]
        cnsItem.name = name
        ChannelModifierUtils.attachModifierToItem(cnsItem, hostItem)
        return CMTransformConstraint(cnsItem)

    @property
    def operation(self):
        """
        Gets the type of the constraint.

        Returns
        -------
        str
            One of TransformConstraintOperation constants.
        """
        return self._item.channel('operation').get()

    @property
    def inputChannel(self):
        return self._item.channel('matrixInput')

    @property
    def outputChannel(self):
        return self._item.channel('matrixOutput')

    @property
    def isRotationConstraint(self):
        """
        Tests if this is rotation constraint.

        Returns
        -------
        bool
        """
        return self.operation == self.Operation.ROTATION

    @property
    def offset(self):
        """
        Gets the constraint offset vector.

        Returns
        -------
        modo.Vector3
        """
        x = self._item.channel('offset.X').get()
        y = self._item.channel('offset.Y').get()
        z = self._item.channel('offset.Z').get()
        return modo.Vector3(x, y, z)

    @offset.setter
    def offset(self, offsetVec):
        """
        Sets new offset for the constraint.

        Parameters
        ----------
        offsetVec : modo.Vector3
        """
        self._item.channel('offset.X').set(offsetVec[0], 0.0, key=False, action=lx.symbol.s_ACTIONLAYER_SETUP)
        self._item.channel('offset.Y').set(offsetVec[1], 0.0, key=False, action=lx.symbol.s_ACTIONLAYER_SETUP)
        self._item.channel('offset.Z').set(offsetVec[2], 0.0, key=False, action=lx.symbol.s_ACTIONLAYER_SETUP)

    @property
    def modoItem(self):
        return self._item

    # -------- Private methods

    def __init__(self, modoItem):
        if modoItem.type != 'cmTransformConstraint':
            raise TypeError
        self._item = modoItem