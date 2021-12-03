

import lx
import lxu
import modo
from run import run


class SelectionMode(object):
    REPLACE = 1
    ADD = 2
    SUBSTRACT = 3


class ItemSelection(object):
    """ Item selection class focused on performance.
    
    It doesn't use modo module but raw SDK (lxu).
    """
    
    def getRaw(self):
        """ Gets currently selected items.

        Returns
        -------
        list of lxu.object.Item
        """
        a = []
        for pkt in self._pkt_list():
            item = lxu.object.Item(self._itemPacketTranslation.Item(pkt))
            a.append(item)

        return a
    
    def getLastRaw(self):
        """ Gets last item in the item selection.
        
        Returns
        -------
        lxu.object.Item, None
            None is returned when there is no selection.
        """
        count = self._selectionService.Count(self._itemSelTypeCode)
        if count == 0:
            return None

        packet = self._selectionService.ByIndex(self._itemSelTypeCode, count - 1)
        return lxu.object.Item(self._itemPacketTranslation.Item(packet))
    
    def getLastModo(self):
        """ Gets last selected item as generic modo.Item.

        Returns
        -------
        modo.Item, None
            None is returned when there is no selection.
        """
        rawItem = self.getLastRaw()
        if rawItem is not None:
            return modo.Item(rawItem)
        return None

    def getLastOfTypeRaw(self, itemType):
        """ Gets last selected raw item of a given item type.
        
        Parameters
        ----------
        itemType : str, int, long
            Either item type string or int code.
            Passing int code is faster.
            
        Returns
        -------
        lxu.object.Item, None
            None is returned when there is no selection.
        """
        count = self._selectionService.Count(self._itemSelTypeCode)
        if count == 0:
            return None
        
        if isinstance(itemType, str):
            itemType = self._sceneService.ItemTypeLookup(itemType)
            
        for x in xrange(count - 1, -1, -1):
            packet = self._selectionService.ByIndex(self._itemSelTypeCode, x)
            rawItem = lxu.object.Item(self._itemPacketTranslation.Item(packet))
            if rawItem.Type() == itemType:
                return rawItem
        return None
    
    def getLastOfTypeModo(self, itemType):
        """ Gets last selected modo item of a given item type.
        
        Parameters
        ----------
        itemType : str, int, long
            Either item type string or int code.
            Passing int code is faster.
            
        Returns
        -------
        modo.Item, None
            Returned modo item will always be of generic modo.Item type.
            None is returned when there is no selection.
        """
        rawItem = self.getLastOfTypeRaw(itemType)
        if rawItem is None:
            return None
        return modo.Item(rawItem)

    def getOfTypeRaw(self, itemType):
        """ Gets a list of selected raw items of a given item type.
        
        Parameters
        ----------
        itemType : str, int, long
            Either item type string or int code.
            Passing int code is faster.
            
        Returns
        -------
        list of lxu.object.Item
        """        
        count = self._selectionService.Count(self._itemSelTypeCode)
        if count == 0:
            return []
        
        if isinstance(itemType, str):
            itemType = self._sceneService.ItemTypeLookup(itemType)
        
        rawItems = []
        for x in xrange(count):
            packet = self._selectionService.ByIndex(self._itemSelTypeCode, x)
            rawItem = lxu.object.Item(self._itemPacketTranslation.Item(packet))
            if rawItem.Type() == itemType:
                rawItems.append(rawItem)
        return rawItems
    
    def getOfTypeModo(self, itemType):
        """ Gets a list of selected modo items of a given item type.
        
        Parameters
        ----------
        itemType : str, int, long
            Either item type string or int code.
            Passing int code is faster.
            
        Returns
        -------
        list of modo.Item
            Returned modo items will always be of generic modo.Item type.
        """            
        rawItems = self.getOfTypeRaw(itemType)
        return [modo.Item(rawItem) for rawItem in rawItems]
    
    @property
    def size(self):
        """ Gets size of item selection.
        
        Returns
        -------
        int
        """
        return self._selectionService.Count(self._itemSelTypeCode)
    
    def getRawByIndex(self, index):
        """ Gets raw selected item by its index in selection.
        
        Parameters
        ----------
        index : int
            Index into selection at which required item is.
            For performance reasons index is not checked to be valid!
        
        Returns
        -------
        lxu.object.Item
        """
        packet = self._selectionService.ByIndex(self._itemSelTypeCode, index)
        return lxu.object.Item(self._itemPacketTranslation.Item(packet))

    def set(self, itemList, selMode=SelectionMode.REPLACE, batch=True):
        """ Select items passed in a list.

        Pass None and set selection to replace to clear selection.

        Parameters
        ----------
        itemList : [modo.Item], [lx.object.Item], modo.Item, lx.object.Item

        selMode : int
            One of SelectionMode.XXX constants.

        batch : bool
            When True batch mode will be set for selection when selection is larget then 1 item.
        """
        if selMode == SelectionMode.REPLACE:
            self._selectionService.Clear(self._itemSelTypeCode)

        if not itemList:
            return False
        if not isinstance(itemList, list):
            itemList = [itemList]

        if len(itemList) > 1 and batch:
            self._selectionService.StartBatch()

        if selMode == SelectionMode.SUBSTRACT:
            for item in itemList:
                selection_packet_pointer = self._itemPacketTranslation.Packet(item)
                self._selectionService.Deselect(self._itemSelTypeCode, selection_packet_pointer)
        else:
            for item in itemList:
                selection_packet_pointer = self._itemPacketTranslation.Packet(item)
                self._selectionService.Select(self._itemSelTypeCode, selection_packet_pointer)

        if len(itemList) > 1 and batch:
            self._selectionService.EndBatch()
        return True

    def selectByName(self, itemID, add=False):
        """ Selects an item by ID or name.

        Parameters
        ----------
        itemID : str
            Name or ID of item to select.
        
        add : bool
            Add to current selection or replace, default = replace
        """
        scene = lxu.select.SceneSelection().current()
        item = scene.ItemLookup(itemID)
        if not add:
            self._selectionService.Clear(self._itemSelTypeCode)
        sPacket = self._itemPacketTranslation.Packet(item)
        self._selectionService.Select(self._itemSelTypeCode, sPacket)

    def drop(self):
        """Drop the selection, changing the selection mode.

        """
        self._selectionService.Drop(self._itemSelTypeCode)

    def clear(self):
        """Drop the selection without changing the selection mode.

        """
        self._selectionService.Clear(self._itemSelTypeCode)

    # -------- Private methods

    def _pkt_list(self):
        """Return a list of raw selection packets.

        """
        a = []
        for i in range(self._selectionService.Count(self._itemSelTypeCode)):
            a.append(self._selectionService.ByIndex(self._itemSelTypeCode, i))

        return a

    def __init__(self):
        self._selectionService = lx.service.Selection()
        self._sceneService = lx.service.Scene()
        self._itemSelectionType = lx.symbol.sSELTYP_ITEM
        self._itemSelTypeCode = self._selectionService.LookupType(self._itemSelectionType)
        self._itemPacketTranslation = lx.object.ItemPacketTranslation(self._selectionService.Allocate(lx.symbol.sSELTYP_ITEM))


class ChannelSelection(object):
    """ Handles channel selection.
    """

    def clear(self):
        """ Clears channel selection.
        """
        self._selectionService.Clear(self._chanSeltypeCode)

    @property
    def selected(self):
        """ Returns currently selected channels.
        
        Returns
        -------
        list of modo.Channel
        """
        chans = []
        chanCount = self._selectionService.Count(self._chanSeltypeCode)

        for x in xrange(chanCount):
            packetPointer = self._selectionService.ByIndex(self._chanSeltypeCode, x)
            if not packetPointer:
                continue
            
            index = self._chanTranspacket.Index(packetPointer)
            item = modo.Item(lx.object.Item(self._chanTranspacket.Item(packetPointer)))
            chans.append(modo.Channel(index, item))

        return chans

    def set(self, chanList, selMode=SelectionMode.REPLACE):
        """
        Sets channels selection.

        Parameters
        ----------
        chanList: modo.Channel
            Single channel or a list of channels to select.

        selMode: int
            One of SelectionMode constants.
        """
        if selMode == SelectionMode.REPLACE:
            self.clear()

        if not chanList:
            return False
        if type(chanList) not in (list, tuple):
            chanList = [chanList]

        if selMode == SelectionMode.SUBSTRACT:
            for channel in chanList:
                selectionPacketPointer = self._chanTranspacket.Packet(channel.item.internalItem, channel.index)
                self._selectionService.Deselect(self._chanSeltypeCode, selectionPacketPointer)
        else:
            for channel in chanList:
                selectionPacketPointer = self._chanTranspacket.Packet(channel.item.internalItem, channel.index)
                self._selectionService.Select(self._chanSeltypeCode, selectionPacketPointer)
        return True

    # -------- Private methods

    def __init__(self):
        self._scene = lxu.select.SceneSelection().current()

        self._selectionService = lx.service.Selection()
        self._chanSeltypeCode = self._selectionService.LookupType(lx.symbol.sSELTYP_CHANNEL)
        self._chanTranspacket = lx.object.ChannelPacketTranslation(self._selectionService.Allocate(lx.symbol.sSELTYP_CHANNEL))
        

class VertexMapSelection:
    """ Utility class for handling vertex map selections.
    """

    SELMODE_STRINGS = {
        SelectionMode.REPLACE: 'replace',
        SelectionMode.ADD: 'add',
        SelectionMode.SUBSTRACT: 'remove'}

    VMAPTYPE_STRINGS = {
        lx.symbol.i_VMAP_MORPH: 'morf',
        lx.symbol.i_VMAP_WEIGHT: 'wght',
        lx.symbol.i_VMAP_TEXTUREUV: 'txuv'}

    def store(self, weight=True, morph=True, uv=True):
        """ Stores current selection. It can be restored with restore() afterwards.
        Stores weight, morph and uvmaps for now only.
        # TODO: Seems a bit unreliable on modo's side?
        # I'm getting weird selections sometimes
        """
        self._storeWeight = None
        self._storeMorph = None
        self._storeTexuv = None

        if weight:
            self._storeWeight = self.get([lx.symbol.i_VMAP_WEIGHT])

        if morph:
            self._storeMorph = self.get([lx.symbol.i_VMAP_MORPH])

        if uv:
            self._storeTexuv = self.get([lx.symbol.i_VMAP_TEXTUREUV])

    def restore(self):
        """ Restores backed up selection.
        """
        if self._storeWeight is not None:
            self.set(self._storeWeight, lx.symbol.i_VMAP_WEIGHT, SelectionMode.REPLACE)

        if self._storeMorph is not None:
            self.set(self._storeMorph, lx.symbol.i_VMAP_MORPH, SelectionMode.REPLACE)

        if self._storeTexuv is not None:
            self.set(self._storeTexuv, lx.symbol.i_VMAP_TEXTUREUV, SelectionMode.REPLACE)

    def restoreByCommand(self):
        """
        Restores backed up selection using selection commands rather then SDK.
        """
        if self._storeWeight is not None:
            self.setByCommand(self._storeWeight, lx.symbol.i_VMAP_WEIGHT, SelectionMode.REPLACE)

        if self._storeMorph is not None:
            self.setByCommand(self._storeMorph, lx.symbol.i_VMAP_MORPH, SelectionMode.REPLACE)

        if self._storeTexuv is not None:
            self.setByCommand(self._storeTexuv, lx.symbol.i_VMAP_TEXTUREUV, SelectionMode.REPLACE)

    def clear(self):
        """ Clears vertex map selection.
        
        All map types are cleared.
        """
        self._selectService.Clear(self._vmapSeltypeCode)

    def get(self, vmapTypes=None):
        """ Returns a list of selected vertex map (internal) names.
        
        Parameters
        ----------
        vmap_types : list of lx.symbol.i_VMAP_XXX
            Allows for filtering selection by vertex map type.

        Returns
        -------
        list[str]
        """
        vmaps = []
        vmaps_n = self._selectService.Count(self._vmapSeltypeCode)

        if not vmaps_n:
            return vmaps

        if type(vmapTypes) not in (list, tuple):
            vmapTypes = [vmapTypes]

        for x in xrange(vmaps_n):
            packet_pointer = self._selectService.ByIndex(self._vmapSeltypeCode, x)
            if not packet_pointer:
                continue
            if vmapTypes and not self._vmapTranspacket.Type(packet_pointer) in vmapTypes:
                continue
            vmaps.append(self._vmapTranspacket.Name(packet_pointer))
        return vmaps

    def set(self, vmapList, vmapType, mode=SelectionMode.REPLACE):
        """ Sets vertex map selection according to the list.
        
        NOTE: Setting selection can get MODO in a bad state somehow.
        It still all works but if you try to undo or close the scene before
        changing vertex map selection via UI (meaning via command)
        MODO will crash.

        Parameters
        ----------
        vmapList : list of str
        
        vmapType : lx.symbol.i_VMAP_XXX
        """
        if mode == SelectionMode.REPLACE:
            self._selectService.Clear(self._vmapSeltypeCode)

        if not vmapList:
            return
        if isinstance(vmapList, list) == False:
            vmapList = [vmapList]

        if len(vmapList) > 1:
            self._selectService.StartBatch()

        if mode == SelectionMode.SUBSTRACT:
            for vmapName in vmapList:
                selection_packet_pointer = self._vmapTranspacket.Packet(vmapType, vmapName)
                self._selectService.Deselect(self._vmapSeltypeCode, selection_packet_pointer)
        else:
            for vmapName in vmapList:
                selection_packet_pointer = self._vmapTranspacket.Packet(vmapType, vmapName)
                self._selectService.Select(self._vmapSeltypeCode, selection_packet_pointer)
    
        if len(vmapList) > 1:
            self._selectService.EndBatch()

    def setByCommand(self,
                     vmapList,
                     vmapType,
                     mode=SelectionMode.REPLACE,
                     clearAll=False):
        """ Set vertex map selection using commands.

        It's a bit different, allows for replacing selection only for given type of vertex maps
        rather then clearing vertex maps of all types.

        Parameters
        ----------
        sel_mode --- replaces only vmaps of given type
        clearAll : bool
            Clears ALL selection, like replace mode in the Set method.
        """
        if clearAll:
            self._selectService.Clear(self._vmapSeltypeCode)

        try:
            selModeString = self.SELMODE_STRINGS[mode]
        except KeyError:
            selModeString = self.SELMODE_STRINGS[SelectionMode.REPLACE]

        try:
            vmapTypeString = self.VMAPTYPE_STRINGS[vmapType]
        except KeyError:
            vmapTypeString = self.VMAPTYPE_STRINGS[lx.symbol.i_VMAP_WEIGHT]

        if mode == SelectionMode.REPLACE:
            run('!select.vertexMap name:{} type:{%s} mode:remove' % vmapTypeString)

        if not vmapList:
            return
        if not isinstance(vmapList, list):
            vmapList = [vmapList]

        for vmapName in vmapList:
            run('!select.vertexMap name:{%s} type:{%s} mode:{%s}' % (vmapName, vmapTypeString, selModeString))

    # -------- Private methods

    def __init__ (self):
        self._scene = lxu.select.SceneSelection().current()

        self._selectService = lx.service.Selection()
        self._vmapSeltypeCode = self._selectService.LookupType(lx.symbol.sSELTYP_VERTEXMAP)
        self._vmapTranspacket = lx.object.VMapPacketTranslation(self._selectService.Allocate(lx.symbol.sSELTYP_VERTEXMAP))

        self._storeWeight = None
        self._storeMorph = None
        self._storeTexuv = None


class MeshComponentSelection:
    """ Base class for handling mesh component selections.
    
    Raises
    ------
    TypeError
        When trying to initialise class that was not properly implemented.
    """

    # -------- Public interface to implement
    @property
    def componentType(self):
        """ Needs to return type of the mesh component.
        
        Returns
        -------
        lx.symbol.sSELTYP_VERTEX, lx.symbol.sSELTYP_EDGE, lx.symbol.sSELTYP_POLYGON
        """
        pass

    @property
    def packetTranslationClass(self):
        pass

    def initModoObject(self, packetPointer):
        pass
        
    # -------- Implementation

    def clear(self):
        """ Clears vertex selection.
        """
        self._selectionService.Clear(self._compSeltypeCode)

    @property
    def size(self):
        """ Gets size of item selection.

        Returns
        -------
        int
        """
        return self._selectionService.Count(self._compSeltypeCode)

    def get(self):
        """ Gets current vertex selection.
        
        Returns
        -------
        list of tuples (modo.Mesh, modo.MeshVertex)
        """
        elements = []
        elementCount = self._selectionService.Count(self._compSeltypeCode)

        for x in xrange(elementCount):
            packet_pointer = self._selectionService.ByIndex(self._compSeltypeCode, x)
            if not packet_pointer:
                continue

            element = self.initModoObject(packet_pointer)
            elements.append(element)

        return elements

    # -------- Private methods

    def __init__(self):
        self._selectionService = lx.service.Selection()
        self._compSeltypeCode = self._selectionService.LookupType(self.componentType)
        self._transpacket = self.packetTranslationClass(self._selectionService.Allocate(self.componentType))


class VertexSelection(MeshComponentSelection):
    
    @property
    def componentType(self):
        return lx.symbol.sSELTYP_VERTEX

    @property
    def packetTranslationClass(self):
        return lx.object.VertexPacketTranslation

    def initModoObject(self, packetPointer):
        item = self._transpacket.Item(packetPointer)
        elementId = self._transpacket.Vertex(packetPointer)
    
        mesh = modo.Mesh(item)
        geo = modo.MeshGeometry(item, mode='read')
        
        # Mesh Vertex interprets long index parameter as id,
        # and int as index.
        # So if we want initialise MeshVertex with id it needs
        # to be long.
        elementId = long(elementId)
        return (mesh, modo.MeshVertex(elementId, geo))
        

class EdgeSelection(MeshComponentSelection):
    
    @property
    def componentType(self):
        return lx.symbol.sSELTYP_EDGE

    @property
    def packetTranslationClass(self):
        return lx.object.EdgePacketTranslation
    
    def initModoObject(self, packetPointer):
        item = self._transpacket.Item(packetPointer)
        id1, id2 = self._transpacket.Vertices(packetPointer)
    
        mesh = modo.Mesh(item)
        geo = modo.MeshGeometry(item, mode='read')
        
        return (mesh, modo.MeshEdge((long(id1), long(id2)), geo))


class PolygonSelection(MeshComponentSelection):
    
    @property
    def componentType(self):
        return lx.symbol.sSELTYP_POLYGON

    @property
    def packetTranslationClass(self):
        return lx.object.PolygonPacketTranslation
    
    def initModoObject(self, packetPointer):
        item = self._transpacket.Item(packetPointer)
        pid = self._transpacket.Polygon(packetPointer)

        mesh = modo.Mesh(item)
        geo = modo.MeshGeometry(item, mode='read')
        
        polyAccess = geo.polygons.accessor
        polyAccess.Select(pid)
        index = polyAccess.Index()
        return (mesh, modo.MeshPolygon(index, geo))
        
        
class SelectionUtils(object):
    
    @classmethod
    def currentComponentSelectionAsVertexSelection(cls):
        """ Gets current component selection and returns it as vertex selection.

        Returns
        -------
        list of tuples (modo.Mesh, modo.MeshVertex)
        """
        vsel = bool(lx.eval('item.componentMode vertex ?'))
        if vsel:
            vertexSelection = VertexSelection()
            return vertexSelection.get()
        esel = bool(lx.eval('item.componentMode edge ?'))
        if esel:
            edgeSelection = EdgeSelection()
            edges = edgeSelection.get()
            return cls._edgesToVertices(edges)
        psel = bool(lx.eval('item.componentMode polygon ?'))
        if psel:
            polySelection = PolygonSelection()
            polys = polySelection.get()
            return cls._polygonsToVertices(polys)
            
    # -------- Private methods
    
    @classmethod
    def _polygonsToVertices(cls, components):
        vertices = {}
        for comp in components:
            for v in comp[1].vertices:
                if not vertices.has_key(v.index):
                    vertices[v.index] = (comp[0], v)
        return vertices.values()

    @classmethod
    def _edgesToVertices(cls, edges):
        vertices = {}
        for edge in edges:
            vid1, vid2 = edge[1].accessor.Endpoints()
            for vid in (vid1, vid2):
                if not vertices.has_key(vid):
                    vertices[vid] = (edge[0], modo.MeshVertex(long(vid), edge[0].geometry))
        return vertices.values()