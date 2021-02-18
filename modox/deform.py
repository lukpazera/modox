

import lx
import modo

import const as c
import item
from item import ItemUtils


GRAPH_DEFORMERS = 'deformers'
GRAPH_DEFORM_TREE = 'deformTree'


class DeformersStack(object):

    @classmethod
    def getDeformTree(cls, rootItem, includeRoot=False):
        """ Gets deformers tree starting from a given root item.

        Returns
        -------
        list(modo.Item)
        """
        treeItems = []
        if includeRoot:
            treeItems.append(rootItem)
        
        queue = rootItem.itemGraph(GRAPH_DEFORM_TREE).reverse()
        
        while queue and len(queue) > 0:
            # The 0 index for pop() is crucial to get hierarchy that is in right order!
            # Or at least in the order in which it appears in deformers list.
            i = queue.pop(0)
            treeItems.append(i)
            subItems = i.itemGraph(GRAPH_DEFORM_TREE).reverse()
            if subItems and len(subItems) > 0:
                queue += subItems
        
        return treeItems

    @classmethod
    def isInTree(cls, modoItem, modoRootItem):
        """ Tests whether given item is under given root item in the deform tree hierarchy.
        """
        result = False
        while modoItem is not None:
    
            graph = modoItem.itemGraph(GRAPH_DEFORM_TREE)
            if not graph:
                break
        
            try:
                item = graph.forward(0)
            except LookupError:
                break
    
            if item == modoRootItem:
                result = True
                break
    
            modoItem = item
            
        return result

    @classmethod
    def getParent(cls, modoItem):
        """ Gets parent item to a given item in the deformers tree.

        Returns
        -------
        modo.Item, None
        """
        graph = modoItem.itemGraph(GRAPH_DEFORM_TREE)
    
        try:
            item = graph.forward(0)
        except LookupError:
            return None

        return item

    @classmethod
    def setParent(cls, modoItem, parentModoItem):
        """
        Parents one item to another in the deformers stack.

        Parameters
        ----------
        modoItem : modo.Item
            Item to parent to the tree.

        parentModoItem : modo.Item
            Parent item already in the tree.
        """
        ItemUtils.addForwardGraphConnections(modoItem, parentModoItem, GRAPH_DEFORM_TREE)

    @classmethod
    def unparent(cls, modoItem):
        """
        Removes item from deformers tree. It'll get moved to root level.
        """
        ItemUtils.clearForwardGraphConnections(modoItem, GRAPH_DEFORM_TREE)
        sceneItem = modoItem.scene.sceneItem
        ItemUtils.addForwardGraphConnections(modoItem, sceneItem, GRAPH_DEFORM_TREE)


class NormalizingFolder(object):

    def bakeWeights(self):
        """ Wrapper around MODO's native Bake Weights command.

        MODO's bake weights works if normalizing folder contains vertex map deformers only.
        It won't work if there are deform folders in there and deformers are under deform
        folders. All deformers have to be in flat hierarchy under the normalizing folder item
        and there can be no other items in the folder.

        The wrapper makes sure that normalizing folder is prepared like that
        for the MODO command to run and then the original setup is restored.
        """
        self._backupAndFlattenHierarchy()
        modo.Scene().select(self._item, add=False)
        lx.eval('!deformGroup.bakeWeights')
        self._restoreHierarchy()

    def addDeformers(self, deformerModoItems):
        """
        Adds given deformers to the normalizing folder.

        Parameters
        ----------
        deformerModoItems : modo.Item, list of modo.Item
        """
        if type(deformerModoItems) not in [list, tuple]:
            deformerModoItems = [deformerModoItems]
        for deformerModoItem in deformerModoItems:
            lx.eval('!deformer.setGroup deformer:{%s} group:{%s}' % (deformerModoItem.id, self._item.id))

    # -------- Private methods

    def _backupAndFlattenHierarchy(self):
        self._parentingCache = []
        allItems = DeformersStack.getDeformTree(self._item, includeRoot=False)
        for modoItem in allItems:
            self._parentingCache.append((modoItem, DeformersStack.getParent(modoItem)))

        for modoItem in allItems:
            if modoItem.type == c.ItemType.DEFORM_FOLDER:
                DeformersStack.unparent(modoItem)
            else:
                DeformersStack.setParent(modoItem, self._item)

    def _restoreHierarchy(self):
        for entry in self._parentingCache:
            child = entry[0]
            parent = entry[1]
            if parent is None:
                continue
            DeformersStack.setParent(child, parent)

    # -------- Private methods

    def __init__(self, modoItem):
        self._item = modoItem


class Effector(object):
    """ Effector is an item that drives deformation with its transforms.
    
    Parameters
    ----------
    modoItem : modo.Item
    """

    @property
    def drivesGeneralInfluence(self):
        """ Checks whether this effector drives an influence or not.
        
        Returns
        -------
        bool
        """
        if self.generalInfluences:
            return True
        return False

    @property
    def deformers(self):
        """ Gets a list of deformers driven by this effector.
        
        Returns
        -------
        list of modo.Item
        """
        deformGraph = modo.ItemGraph(self._item, GRAPH_DEFORMERS)
        if deformGraph is None:
            return []
        return deformGraph.forward()

    def setDeformers(self, deformerModoItems, replace=True):
        """ Sets deformers that the effector will drive.

        Parameters
        ----------
        deformerModoItems : modo.Item, list of modo.Item, None
            Pass None to clear

        replace : bool
            Replace all links (True) or add new ones (False).
            True is default.
        """
        if deformerModoItems is None or replace:
            item.ItemUtils.clearForwardGraphConnections(self._item, GRAPH_DEFORMERS)

        if deformerModoItems is not None:
            item.ItemUtils.addForwardGraphConnections(self._item, deformerModoItems, GRAPH_DEFORMERS)

    @property
    def isEffector(self):
        """ Tests whether this item is an effector for deformer(s).
        
        Returns
        -------
        bool
        """
        graph = lx.object.ItemGraph(self._item.Context().GraphLookup(GRAPH_DEFORMERS))
        return graph.FwdCount(self._item) > 0
    
    @property
    def generalInfluences(self):
        """ Gets just general influences driven by this effector.
        
        This is more specific then deformers property.
        
        Returns
        -------
        list of GeneralInfluenceDeformer
        """
        deformers = self.deformers
        geninfs = []
        for connectedItem in deformers:
            if connectedItem.type == 'genInfluence':
                geninfs.append(connectedItem)
        return geninfs
    
    # -------- Private methods

    def __init__(self, modoItem):
        self._item = modoItem


class DeformFolder(object):
    
    def addDeformer(self, modoItem):
        """ Adds new item to the folder.

        It doesn't need to be deformer, can be weight container too.
        """
        folderDeformTreeGraph = self._item.itemGraph(GRAPH_DEFORM_TREE)
        itemDeformTreeGraph = modoItem.itemGraph(GRAPH_DEFORM_TREE)
        
        itemDeformTreeGraph >> folderDeformTreeGraph
    
    # -------- Private methods

    def __init__(self, modoItem):
        self._item = modoItem


class DeformedItem(object):
    
    @property
    def isDeformed(self):
        """ Tests whether this item is being deformed.
        """
        # This is simply testing if there are any links on deformers graph
        graph = lx.object.ItemGraph(self._item.Context().GraphLookup(GRAPH_DEFORMERS))
        return graph.RevCount(self._item) > 0

    @property
    def deformers(self):
        """ Gets a list of deformers that affect this deformed item.
        
        Returns
        -------
        list of modo.Item
        """
        deformers = []
        allConnections = item.ItemUtils.getReverseGraphConnections(self._item, GRAPH_DEFORMERS)
        for modoItem in allConnections:
            # If we're dealing with weight container we need to get deformer from container.
            if modoItem.type == c.ItemType.WEIGHT_CONTAINER:
                itemsToTest = WeightContainer(modoItem).deformerModoItems
            else:
                itemsToTest = [modoItem]
            # We're checking wheter this item has deformer flags on it.
            # If it has - it is assumed to be deformer.
            for modoItem in itemsToTest:
                try:
                    Deformer(modoItem)
                except TypeError:
                    continue
                deformers.append(modoItem)
        return deformers
    
    def setDeformers(self, deformerModoItems, replace=False):
        """ Connect deformers to this deformed item.
        
        Parameters
        ----------
        deformerModoItems : modo.Item, list of modo.Item, None
            Pass None to clear deformers affecting this item.
        
        replace : bool
            When True all current deformers will be disconnected from the deformed item first.
        """
        if deformerModoItems is None or replace:
            item.ItemUtils.clearReverseGraphConnections(self._item, GRAPH_DEFORMERS)

        if deformerModoItems is not None:
            item.ItemUtils.addReverseGraphConnections(self._item, deformerModoItems, GRAPH_DEFORMERS)
        
    def disconnectDeformers(self, specificDeformers=[]):
        """ Disconnects all deformers from this item.
        
        Parameters
        ----------
        specificDeformers : modo.Item, [modo.Item], optional
            If you want to only disconnect specific deformer item pass as optional list argument.
        """
        item.ItemUtils.clearReverseGraphConnections(self._item, GRAPH_DEFORMERS, specificItems=specificDeformers)

    # -------- Private methods
    
    def __init__(self, modoItem):
        self._item = modoItem
    
    
class Deformer(object):
    """ General deformer class.
    
    Raises
    ------
    TypeError
        When descModoItemType is set and the item type doesn't match that.
        When MODO does not recognize the item as deformer.
    """
    
    descModoItemType = None
    
    @property
    def meshes(self):
        """ Gets a list of meshes that are being deformed by this deformer.
        """
        return modo.Deformer(self._item).meshes

    @meshes.setter
    def meshes(self, meshes):
        """ Connect a list of meshes to the deformer.
        
        Note that this does not disconnect any meshes so this works
        in the 'add' mode.
        
        Parameters
        ----------
        meshes : modo.Item, list of modo.Item
        """
        if type(meshes) not in (list, tuple):
            meshes = [meshes]

        for mesh in meshes:
            meshGraph = mesh.itemGraph(GRAPH_DEFORMERS)
            deformerGraph = self._item.itemGraph(GRAPH_DEFORMERS)
            deformerGraph >> meshGraph
    
    @property
    def weightContainers(self):
        """ Gets a list of weight containers plugged into this deformer.
        
        Returns
        -------
        list of modo.Item
            Empty list is returned when there are no containers connected.
        """
        # Weight containers 
        deformersGraph = self._item.itemGraph(GRAPH_DEFORMERS)
        geoItems = deformersGraph.forward()
        if not geoItems:
            return []
        
        containers = []
        for modoItem in geoItems:
            if modoItem.type == c.ItemType.WEIGHT_CONTAINER:
                containers.append(modoItem)
        
        return containers
    
    @property
    def mapName(self):
        """ Returns name of the weight map used by deformer (if applicable).
        
        If deformer effect can be modulated by a weight map this property should return
        the name of the weight map. By default it's simply trying to use
        lx.object.WeightMapDeformerItem().
        If there's a different method to get weight map name it should be implemented
        by inheriting classes.
        
        Returns
        -------
        str, None
            None is returned when this deformer does not use a weight map
            Empty string should be returned weight map is supported
            by is not currently assigned.
        """
        try:
            weightMapDeformerItem = lx.object.WeightMapDeformerItem(self._item)
        except TypeError:
            return None
        # Even if the interface is right LookupError is thrown when weight map is not assigned.
        try:
            return weightMapDeformerItem.GetMapName(self._item.scene.chanRead)
        except LookupError:
            pass
        return None

    @property
    def parentFolder(self):
        """ Gets group deformer that this deformer is under.
        
        It can be normalised folder or regular deform folder.
        
        Returns
        -------
        modo.Item, None
        """
        deformTreeGraph = self._item.itemGraph(GRAPH_DEFORM_TREE)
        try:
            return deformTreeGraph.forward(0)
        except LookupError:
            pass
        return None

    @property
    def effector(self):
        """ Returns an item that acts as effector (transforms source) for the deformer.
        
        Returns
        -------
        modo.Item, None
            None is returned when there is no effector.
        """
        return item.ItemUtils.getFirstReverseGraphConnection(self._item, GRAPH_DEFORMERS)
    
    @property
    def weightMapNames(self):
        """ Gets a list of all weight map names that are related to this deformer.
        
        This method first checks on weight containers plugged to the deformer.
        If there are weight containers plugged - their corresponding weight map names
        are returned.
        
        If not, an attempt is made to get weight map setting directly (if it exists on deformer).
        
        Returns
        -------
        list of str
        """
        mapsList = []
        weightContainers = self.weightContainers
        if weightContainers:
            for wc in weightContainers:
                mapsList.append("__item_" + wc.id)
        else:
            mapName = self.mapName
            if mapName:
                mapsList.append(mapName)
        return mapsList

    # -------- Private methods

    def __init__(self, modoItem):
        if issubclass(modoItem.__class__, modo.Item):
            modoItem = modo.Item(modoItem.internalItem)
        self._item = modoItem

        if self.descModoItemType is not None:
            if self._item.type != self.descModoItemType:
                raise TypeError

        # We're checking wheter this item has deformer flags on it.
        # If it has - it is assumed to be deformer.
        deformerService = lx.service.Deformer()
        try:
            deformerService.DeformerFlags(self._item.internalItem)
        except LookupError:
            raise TypeError


class WeightContainer(object):

    @property
    def meshes(self):
        deformersGraph = self._item.itemGraph(GRAPH_DEFORMERS)
        return deformersGraph.forward()

    @meshes.setter
    def meshes(self, meshes):
        """ Gets/connects a list of meshes to the deformer.
        
        Note that connecting meshes does not disconnect any meshes
        that are already connected so this works in the 'add' mode.
        """
        if type(meshes) not in (list, tuple):
            meshes = [meshes]

        for mesh in meshes:
            meshGraph = mesh.itemGraph(GRAPH_DEFORMERS)
            deformerGraph = self._item.itemGraph(GRAPH_DEFORMERS)
            deformerGraph >> meshGraph

    @property
    def weightMapName(self):
        """ Gets name of weight map corresponding to this weight container.
        
        Returns
        -------
        str
        """
        return "__item_%s" % self._item.id

    @property
    def deformers(self):
        """ Gets a list of deformers that use this weight container.
        
        Returns
        -------
        list of modox.Deformer
        """
        allConnections = item.ItemUtils.getReverseGraphConnections(self._item, GRAPH_DEFORMERS)
        deformers = []
        for modoItem in allConnections:
            try:
                deformers.append(Deformer(modoItem))
            except TypeError:
                pass
        return deformers

    @property
    def deformerModoItems(self):
        """ Gets a list of modo.Item deformers that use this weight container.
        
        Returns
        -------
        list of modo.Item
        """
        allConnections = item.ItemUtils.getReverseGraphConnections(self._item, GRAPH_DEFORMERS)
        deformers = []
        for modoItem in allConnections:
            try:
                Deformer(modoItem)
            except TypeError:
                continue
            deformers.append(modoItem)
        return deformers
        
    # -------- Private methods

    def __init__(self, modoItem):
        if issubclass(modoItem.__class__, modo.Item):
            modoItem = modo.Item(modoItem.internalItem)
        self._item = modoItem


class GeneralInfluenceType(object):
    ALL = 'all'
    WEIGHT_MAP = 'mapWeight'
    VERTEX_SELECTION_SET = 'mapPick'
    MATERIAL = 'ptagMaterial'
    PART = 'ptagPart'
    POLYGON_SELECTION_SET = 'ptagPick'
    
    
class GeneralInfluence(Deformer):
    """ Represents general influence item.
    """
    
    InfluenceType = GeneralInfluenceType

    descModoItemType = "genInfluence"

    @property
    def mapName(self):
        """ Gets weight map name that this influence is using.
        
        Returns
        -------
        str, None
        """
        try:
            return modo.GeneralInfluenceDeformer(self._item).mapName
        except LookupError:
            return None

    @mapName.setter
    def mapName(self, name):
        """ Sets new weight map name for the influence.
        
        Parameters
        ----------
        name : str
        """ 
        self._item.channel('name').set(name, time=0.0, key=False, action=lx.symbol.s_ACTIONLAYER_SETUP)
    
    @property
    def influenceType(self):
        return self._item.channel('type').get(time=0.0, action=lx.symbol.s_ACTIONLAYER_EDIT)
    
    @influenceType.setter
    def influenceType(self, value):
        """ Gets/sets type of influence: entire mesh, weight map, etc.
        
        Parameters
        ----------
        value : str
            One of InfluenceType.XXX constants.
        """
        self._item.channel('type').set(value, time=0.0, key=False, action=lx.symbol.s_ACTIONLAYER_SETUP)

    def resetSettingsIfNotDeforming(self):
        """
        Resets general influence settings if general influence does not affect any mesh.
        """
        if self.meshes:
            return
        self.influenceType = self.InfluenceType.ALL
        self.mapName = ''
