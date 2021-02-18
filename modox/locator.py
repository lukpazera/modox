

import lx
import modo
import const as c


class TransformItemType(object):
    POSITION = 'translation'
    ROTATION = 'rotation'
    SCALE = 'scale'


class LocatorUtils(object):
    """ Various utility functions that act on locator type items.
    """

    TransformType = TransformItemType

    def hasAnyZeroTransforms(self, modoItem):
        """ Tests whether given item has any zero transforms in the stack.

        Parameters
        ----------
        modoItem : modo.Item
        
        Returns
        -------
        bool
        """
        return (self._testForZeroTransformsOfType(modoItem, self.TransformType.POSITION) or
                self._testForZeroTransformsOfType(modoItem, self.TransformType.ROTATION))

    def mergeAllZeroTransforms(self, modoItem, removeZeroXfrmItems=True):
        """ Merges position and rotation zero transforms with their primary transforms.
        
        Essentially, on a standard setup with zeroed transforms this clears
        zero transform values.
        
        NOTE: Merging scale transforms is not supported, does not work properly in MODO.
        NOTE: This method should best be called when in setup mode.
        Also, this method modifies item selection and it uses a command that requires
        transform items to be selected.
        
        Parameters
        ----------
        modoItem : modo.Item
            Item to perform merge on.
            
        removeZeroXfrmItems : bool, optional
            When set to true the cleared out zero transform items will be removed
            from scene.
        """
        self.mergePositionZeroTransform(modoItem, removeZeroXfrmItems)
        self.mergeRotationZeroTransform(modoItem, removeZeroXfrmItems)

    def mergePositionZeroTransform(self, modoItem, removeZeroXfrmItem=True):
        self._mergeTransformsOfType(modoItem, self.TransformType.POSITION, removeZeroXfrmItem)

    def mergeRotationZeroTransform(self, modoItem, removeZeroXfrmItem=True):
        self._mergeTransformsOfType(modoItem, self.TransformType.ROTATION, removeZeroXfrmItem)

    @classmethod
    def getItemWorldPosition(self, locItem):
        """ Gets world position of a given item as a tuple of 3 values.
        
        Paramters
        ---------
        modo.Item
            The item to get world position of.

        Returns
        -------
        tuple
        """
        mtx = self.getItemWorldTransform(locItem)
        return mtx.position

    @classmethod
    def getItemWorldPositionVector(self, locItem):
        """ Gets world position of a given item as a modo.Vector.
        
        Paramters
        ---------
        modo.Item
            The item to get world position of.

        Returns
        -------
        modo.Vector3
        """
        v = self.getItemWorldPosition(locItem)
        return modo.Vector3(v[0], v[1], v[2])

    @classmethod
    def hasWorldTransform(self, modoItem):
        """ Tests whether an item has world transforms applied.
        
        Returns
        -------
        bool
        """
        wmtx = self.getItemWorldTransform(modoItem)
        return wmtx != modo.Matrix4()

    @classmethod
    def hasLocalScale(cls, modoItem):
        """
        Tests whether the item is scaled with local transforms.
        """
        mtx = cls.getItemLocalTransform(modoItem)
        scale = mtx.scale()
        return scale != modo.Vector3(1.0, 1.0, 1.0)

    @classmethod
    def getItemWorldTransform(self, modoItem):
        """ Gets item world transform for current time.

        Paramters
        ---------
        modo.Item
            The item to get world transform of.

        Returns
        -------
        modo.Matrix4
        """
        mtxObject = modoItem.channel('worldMatrix').get() # this gets lx.unknown
        return modo.Matrix4(mtxObject)

    @classmethod
    def getItemWorldPositionMatrixChannel(cls, modoItem):
        """
        Gets item's world position matrix channel.

        Returns
        -------
        modo.Channel, None
            None is returned when channel cannot be found.
        """
        return modoItem.channel('wposMatrix')

    @classmethod
    def getItemWorldRotation(self, modoItem, transpose=True):
        """ Gets item world rotation for current time.

        Paramters
        ---------
        modo.Item
            The item to get world rotation of.

        transpose : bool
            There is legacy issue in MODO where 3x3 rotation matrices have
            different order (rows/columns switched) then 4x4 ones.
            If you want to keep calling methods on this matrix such as asEuler()
            don't transpose this matrix.
            If you want to pass this matrix to modox.TransformUtils.applyTransform for example
            it has to be transformed to be in line with 4x4 matrix.
            Transpose is True by default and this is for ACS3 legacy reasons this time.

        Returns
        -------
        modo.Matrix3
        """
        mtxObject = modoItem.channel('wrotMatrix').get() # this gets lx.unknown
        worldMtx3 = modo.Matrix3(mtxObject)
        # The matrix HAS TO BE TRANSPOSED to be the correct modo.Matrix3.
        # This is some legacy issue in MODO itself where rotation matrices have
        # different order then transform ones.
        # This is also true when getting the world transform matrix.
        if transpose:
            worldMtx3.transpose()
        return worldMtx3

    @classmethod
    def getItemWorldRotationMatrixChannel(cls, modoItem):
        """
        Gets item's world rotation matrix channel.

        Returns
        -------
        modo.Channel, None
            None is returned when channel cannot be found.
        """
        return modoItem.channel('wrotMatrix')

    @classmethod
    def getItemWorldScaleVector(cls, modoItem):
        """
        Gets item world scale as a vector.

        Paramters
        ---------
        modo.Item
            The item to get world scale of.

        Returns
        -------
        modo.Vector3
        """
        mtxObject = modoItem.channel('wsclMatrix').get() # this gets lx.unknown
        return modo.Matrix4(mtxObject).scale()

    @classmethod
    def getItemLocalTransform(self, modoItem):
        """ Gets item local transform for current time.

        Paramters
        ---------
        modo.Item
            The item to get local transform of.

        Returns
        -------
        modo.Matrix4
        """
        mtxObject = modoItem.channel('localMatrix').get() # this gets lx.unknown
        return modo.Matrix4(mtxObject)

    @classmethod
    def getItemPosition(self, modoItem, time=0.0, action=lx.symbol.s_ACTIONLAYER_EDIT):
        """ Gets item local position.
        
        Position is read from primary transform item channels directly.
        
        Returns
        -------
        modo.Vector3
        """
        if action==lx.symbol.s_ACTIONLAYER_SETUP:
            time = 0.0
        loc = modo.LocatorSuperType(modoItem.internalItem)
        return modo.Vector3(loc.position.get(time, action))

    @classmethod
    def setItemPosition(self, modoItem, newPos, time=0.0, key=False, action=lx.symbol.s_ACTIONLAYER_SETUP):
        """ Sets new item local position.
        
        Position is set on a primary transform item directly.
        It does not account for any extra transforms that might be added to an item
        (such as zero transforms).
        
        Parameters
        ----------
        newPos : modo.Vector3
        """
        if action == lx.symbol.s_ACTIONLAYER_SETUP:
            key = False
            time = 0.0
    
        loc = modo.LocatorSuperType(modoItem.internalItem)
        loc.position.set((newPos.x, newPos.y, newPos.z), time=time, key=key, action=action)
    
    @classmethod
    def setZeroPosition(self, modoItem, pos, time=0.0, key=False, action=lx.symbol.s_ACTIONLAYER_SETUP):
        """ Sets zero position for an item.
        
        This really just sets position on a position transform item that's one step up
        the transforms stack from the primary transform item.
        
        Parameters
        ----------
        pos : modo.Vector3
        """
        if action == lx.symbol.s_ACTIONLAYER_SETUP:
            key = False
            time = 0.0

        zeroPos = self._getZeroTransformOfType(modoItem, self.TransformType.POSITION)
        if zeroPos is not None:
            zeroPos.set((pos.x, pos.y, pos.z), time=time, key=key, action=action)
        
    @classmethod
    def getItemRotation(self, modoItem, time=0.0, action=lx.symbol.s_ACTIONLAYER_EDIT):
        """ Gets item's local rotation.
        
        Rotation is read from primary transform item channels directly.
    
        Returns
        -------
        modo.Vector3
            Rotation angles in radians.
        """
        if action==lx.symbol.s_ACTIONLAYER_SETUP:
            time = 0.0

        loc = modo.LocatorSuperType(modoItem.internalItem)
        return modo.Vector3(loc.rotation.get(time, action))
    
    @classmethod
    def setItemRotation(self, modoItem, newRot, time=0.0, key=False, action=lx.symbol.s_ACTIONLAYER_SETUP):
        """ Sets item in radians.

        This really just sets rotation on a primary rotation transform item without
        accounting for any other rotations transforms that might be in the stack.
        
        Parameters
        ----------
        newRot : modo.Vector3
            Euler angles in radians.
        """
        if action == lx.symbol.s_ACTIONLAYER_SETUP:
            key = False
            time = 0.0
    
        loc = modo.LocatorSuperType(modoItem.internalItem)
        loc.rotation.set((newRot.x, newRot.y, newRot.z), time=time, key=key, action=action)

    @classmethod
    def getItemScale(self, modoItem, time=0.0, action=lx.symbol.s_ACTIONLAYER_EDIT):
        """ Gets item's local scale.

        Scale is read from primary transform item channels directly.

        Returns
        -------
        modo.Vector3
            Scale values as vector.
        """
        if action == lx.symbol.s_ACTIONLAYER_SETUP:
            time = 0.0

        loc = modo.LocatorSuperType(modoItem.internalItem)
        return modo.Vector3(loc.scale.get(time, action))

    @classmethod
    def setItemScale(self, modoItem, newScale, time=0.0, key=False, action=lx.symbol.s_ACTIONLAYER_SETUP):
        """ Sets item in radians.

        This really just sets rotation on a primary rotation transform item without
        accounting for any other rotations transforms that might be in the stack.

        Parameters
        ----------
        newScale : modo.Vector3
            Scale as a vector.
        """
        if action == lx.symbol.s_ACTIONLAYER_SETUP:
            key = False
            time = 0.0

        loc = modo.LocatorSuperType(modoItem.internalItem)
        loc.scale.set((newScale.x, newScale.y, newScale.z), time=time, key=key, action=action)

    @classmethod
    def setZeroRotation(self, modoItem, rot, time=0.0, key=False, action=lx.symbol.s_ACTIONLAYER_SETUP):
        """ Sets zero rotation for an item.
        
        This really just sets rotation on a rotation transform item that's one step up
        the transforms stack from the primary rotation transform item.
        
        Parameters
        ----------
        rot : modo.Vector3
        """
        if action == lx.symbol.s_ACTIONLAYER_SETUP:
            key = False
            time = 0.0

        zeroRot = self._getZeroTransformOfType(modoItem, self.TransformType.ROTATION)
        if zeroRot is not None:
            zeroRot.set((rot.x, rot.y, rot.z), time=time, key=key, action=action)
        
    @classmethod
    def getItemParentWorldTransform(self, modoItem):
        """ Gets item's parent world transform for current time.

        Paramters
        ---------
        modo.Item
            The item to get parent world transform of.

        Returns
        -------
        modo.Matrix4
        """
        mtxObject = modoItem.channel('wParentMatrix').get() # this gets lx.unknown
        return modo.Matrix4(mtxObject)

    @classmethod
    def getItemParentWorldScaleVector(cls, modoItem):
        """
        Gets item's parent world scale vector.

        This vector says how much the item is scaled by its parent space.

        Returns
        -------
        modo.Vector3
        """
        mtxObject = modoItem.channel('wParentMatrix').get() # this gets lx.unknown
        return modo.Matrix4(mtxObject).scale()

    @classmethod
    def getItemParentWorldPosition(self, modoItem):
        """ Gets world position of a given item's parent space as a tuple of 3 values.
        
        Paramters
        ---------
        modo.Item
            The item which parent space world position will be returned.

        Returns
        -------
        tuple
        """
        xfrm = self.getItemParentWorldTransform(modoItem)
        return xfrm.position

    @classmethod
    def getItemParentWorldOrientation(self, modoItem):
        """ Gets item parent world orientation for current time.

        Paramters
        ---------
        modo.Item
            The item to get parent world rotation of.

        Returns
        -------
        modo.Matrix3
        """
        mtxObject = modoItem.channel('wParentMatrix').get() # this gets lx.unknown
        worldMtx3 = modo.Matrix3(mtxObject)
        worldMtx3.transpose()
        return worldMtx3

    @classmethod
    def parentInPlace(self, modoItem, parentModoItem, index=-1):
        """ Parent an item to another in place.
        
        Note that this is just using MODO's command and will not work for animated items properly.
        
        Parameters
        ----------
        index : int
            Child index after parenting.
        """
        lx.eval('!item.parent {%s} {%s} %d inPlace:1 duplicate:0' % (modoItem.id, parentModoItem.id, index))

    @classmethod
    def getTransformItem(cls, modoItem, transformType):
        """
        Gets the main transform item for locator super type item.

        Returns
        -------
        modo.TransformItem
        """
        loc = modo.LocatorSuperType(modoItem.internalItem)
        if transformType == c.TransformType.POSITION:
            return loc.position
        elif transformType == c.TransformType.ROTATION:
            return loc.rotation
        elif transformType == c.TransformType.SCALE:
            return loc.scale

        return None

    @classmethod
    def freezeTransforms(cls, modoItem, position=False, rotation=False, scale=False):
        modoItem.select(replace=True)
        if position:
            lx.eval('!transform.freeze translation')
        if rotation:
            lx.eval('!transform.freeze rotation')
        if scale:
            lx.eval('!transform.freeze scale')

    # -------- Private methods

    def _mergeTransformsOfType(self, modoItem, xfrmType, removeZeroXfrmItem=True):
        loc = modo.LocatorSuperType(modoItem)
        if len(loc.transforms) < 2:
            return
        
        if xfrmType == self.TransformType.POSITION:
            mainXfrmItem = loc.position
        elif xfrmType == self.TransformType.ROTATION:
            mainXfrmItem = loc.rotation

        # Need to reverse transforms list to walk the stack
        # from bottom up.
        transformsStack = [xfrm for xfrm in loc.transforms]
        transformsStack.reverse()

        zeroXfrmItem = self._getZeroTransformFromTheStack(transformsStack, mainXfrmItem)
        if zeroXfrmItem is not None:
            self._scene.select([zeroXfrmItem, mainXfrmItem])
            lx.eval('!transform.merge rem:%d' % int(removeZeroXfrmItem))

    @classmethod
    def _getZeroTransformOfType(self, modoItem, xfrmType):
        """
        Gets zero transform item of a given type.

        Returns
        -------
        modo.Item, None
            None is returned when no zero transform was found.
        """
        loc = modo.LocatorSuperType(modoItem)
        transforms = loc.transforms
        if len(transforms) < 2:
            return None
        
        if xfrmType == self.TransformType.POSITION:
            mainXfrmItem = loc.position
        elif xfrmType == self.TransformType.ROTATION:
            mainXfrmItem = loc.rotation

        # Need to reverse transforms list to walk the stack
        # from bottom up.
        transformsStack = [xfrm for xfrm in transforms]
        transformsStack.reverse()
        return self._getZeroTransformFromTheStack(transformsStack, mainXfrmItem)

    def _testForZeroTransformsOfType(self, modoItem, xfrmType):
        """
        Tests whether an item has zero transforms of a given type.
        """
        return self._getZeroTransformOfType(modoItem, xfrmType) is not None

    @classmethod
    def _getZeroTransformFromTheStack(cls, transformsStack, mainXfrmItem):
        """
        Gets zero transform item given transform stack and the main transform item
        to start scanning from.

        This is using proper zero transform item identification that is not exposed
        in SDK but is used by MODO internally.
        Zero transform item 'type' integer channel has value of 21 on zero transform items.

        Returns
        -------
        modo.Item, None
            None is returned if there's no zero transform item for an item.
        """
        scanIndex = -1
        for x in xrange(len(transformsStack) - 1):
            if transformsStack[x] == mainXfrmItem:
                scanIndex = x
                break

        if scanIndex < 0:
            return None

        offset = 1
        zeroXfrmItem = None
        while True:
            try:
                upXfrmItem = transformsStack[scanIndex + offset]
            except IndexError:
                break
            if upXfrmItem.type != mainXfrmItem.type:
                break

            # This channel has hints so TD SDK reading comes back as str
            # This is why even if we're after int number we still test it as a string.
            valString = upXfrmItem.channel('type').get(None, lx.symbol.s_ACTIONLAYER_SETUP)
            if valString == '21':
                zeroXfrmItem = upXfrmItem
                break

            offset += 1
        return zeroXfrmItem

    def __init__(self, modoScene=None):
        if modoScene is None:
            modoScene = modo.Scene()
        self._scene = modoScene