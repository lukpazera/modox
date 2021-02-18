

import lx
import modo


class TransformUtils(object):

    @classmethod
    def applyEdit(cls):
        """ Applies edits from edit action.
        
        This needs to be done if you want to edit an action directly
        (such as setup) but have some edits on edit action currently.
        """
        try:
            lx.eval('!edit.apply')
        except RuntimeError:
            pass

    @classmethod
    def convertModoMatrix3ToRawMatrix(cls, matrix3):
        """ Converts modo matrix3 to a raw SDK matrix.
        
        Raw matrix is required by raw SDK methods such as lx.object.Locator.SetRotation().
        
        Returns
        -------
        raw SDK matrix (a list of lists)
        """
        rawMatrix = [[1,0,0], [0,1,0], [0,0,1]]
    
        rawMatrix[0][0] = matrix3.m[0][0]
        rawMatrix[1][0] = matrix3.m[0][1]
        rawMatrix[2][0] = matrix3.m[0][2]
    
        rawMatrix[0][1] = matrix3.m[1][0]
        rawMatrix[1][1] = matrix3.m[1][1]
        rawMatrix[2][1] = matrix3.m[1][2]
    
        rawMatrix[0][2] = matrix3.m[2][0]
        rawMatrix[1][2] = matrix3.m[2][1]
        rawMatrix[2][2] = matrix3.m[2][2]

        return rawMatrix

    @classmethod
    def applyTransform(cls,
        modoItem,
        positionVector=None,
        orientationMat3=None,
        scaleVector=None,
        mode=lx.symbol.iLOCATOR_LOCAL,
        action=lx.symbol.s_ACTIONLAYER_SETUP):
        """ Applies transform to an item using position vector and 3x3 orientation matrix.
        
        Paramters
        ---------
        modoItem : modo.Item
            Modo item to apply the transform to.
        
        positionVector : modo.Vector3
            Position portion of the transform.
            
        orientationMat3 : modo.Matrix3
            Orientation and scale part of the transform.
        
        mode : lx.symbol.iLOCATOR_LOCAL, lx.symbol.iLOCATOR_WORLD
        
        action : lx.symbol.s_ACTIONLAYER_XXX
            Action to store values on.
        """
        scene = modo.Scene().scene
        channelRead = scene.Channels(None, 0.0)
        channelWrite = scene.Channels(action, 0.0)
    
        loc = lx.object.Locator(modoItem.internalItem)

        if positionVector is not None:
            loc.SetPosition(channelRead, channelWrite, positionVector.values, mode, 0)
        
        if orientationMat3 is not None:
            orientation = cls.convertModoMatrix3ToRawMatrix(orientationMat3)
            loc.SetRotation(channelRead, channelWrite, orientation, mode, 0)

        if scaleVector is not None:
            scaleM4 = modo.Matrix4()
            scaleM4.m[0][0] = scaleVector[0]
            scaleM4.m[1][1] = scaleVector[1]
            scaleM4.m[2][2] = scaleVector[2]
            loc.SetScale(channelRead, channelWrite, scaleM4, mode, 0)
        
    @classmethod
    def getRotationOrder(cls, rotationItem):
        """ Gets rotation order for rotation transform item.
        
        Parameters
        ----------
        rotationItem : rotation or modo.Item
            If locator type modo item is passed its primary rotation
            transform item is queried for the order.
            
        Returns
        -------
        str
            Rotation order as text hint ('xyz', 'zxy', etc.)
        """
        if rotationItem.type != 'rotation':
            rotationItem = modo.LocatorSuperType(rotationItem).rotation
        return rotationItem.channel('order').get()
    
    @classmethod
    def linkWorldTransforms(cls, itemSource, itemTarget, linkPos=True, linkRot=True, linkScale=True):
        """ Links world transforms of 2 items.
        
        Parameters
        ----------
        itemSource : modo.Item
            Transforms will go out from this item.
        
        itemTarget : modo.Item
        """
        if linkPos:
            sourcewpos = itemSource.channel('wposMatrix')
            targetwpos = itemTarget.channel('wposMatrix')
            sourcewpos >> targetwpos

        if linkRot:
            sourcewrot = itemSource.channel('wrotMatrix')
            targetwrot = itemTarget.channel('wrotMatrix')
            sourcewrot >> targetwrot

        if linkScale:
            sourcewscl = itemSource.channel('wsclMatrix')
            targetwscl = itemTarget.channel('wsclMatrix')
            sourcewscl >> targetwscl


        



        