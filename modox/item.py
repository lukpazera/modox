

import lx
import modo


class Item(modo.Item):
    
    @property
    def typeRaw(self):
        """ Gets item type using raw SDK.

        This is the same for most items as type property except for groups.
        For groups td sdk will return group type (assembly, etc.) while raw sdk
        will simply return 'group' for any group.

        Returns
        -------
        str
        """
        typeCode = self.internalItem.Type()
        itemTypeName = lx.service.Scene().ItemTypeName(typeCode)
        return itemTypeName
    
    def autoFocusInItemList(self):
        """ Focuses on the item in item list.
        """
        self.select(replace=True)
        # try/except is needed here as this command will fail
        # when item list is not in UI.
        try:
            lx.eval("!itemList.find")
        except RuntimeError:
            pass

    def isInHierarchy(self, hierarchyRootItem):
        """ Tests whether an item is under given hierarchy root item.
        
        Parameters
        ----------
        hierarchyRootItem : modo.Item
        """
        item = self.parent
        result = False
        while item is not None:
            if item == hierarchyRootItem:
                result = True
                break
            item = item.parent
        return result
    
    @property
    def rootSuperType(self):
        """ Returns the topmost supertype of an item.
                
        Returns
        -------
        str
            Super type as string or None if item has no supertype (is super type itself).
        """
        sceneService = lx.service.Scene()
        superType = self.internalItem.Type()
        rootSuperType = None
    
        while superType != 0:
            superType = sceneService.ItemTypeSuper(superType)
            if superType == 0:
                break
            rootSuperType = superType
    
        if rootSuperType:
            return sceneService.ItemTypeName(rootSuperType)

        return None

    @property
    def isOfXfrmCoreSuperType(self):
        """ Tests whether item is inherits from locator type item meaning it has transforms.

        Returns
        -------
        bool
        """
        return self.rootSuperType == 'xfrmcore'

    @property
    def isOfChannelModifierSuperType(self):
        """ Tests whether this item is chanel modifier.
        """
        return self.rootSuperType == 'chanModify'

    def getOrderedHierarchy(self, includeRoot=False):
        """ Gets item's hierarchy in order according to item depth in hierarchy.
        
        Items with hierarchy level 1 will be listed first, then level 2, etc.
        This will not be the same order as in item list!
        
        Parameters
        ----------
        includeRoot : bool
            When True the return hierarchy list will start from the root
            item itself.
            
        Returns
        -------
        list : modo.Item
        """
        hierarchy = []
        if includeRoot:
            hierarchy.append(self)
            
        queue = self.children(recursive=False)
    
        while queue and len(queue) > 0:
            # The 0 index for pop() is crucial to get hierarchy that is in right order!
            # Or at least in the order in which it appears in item list.
            i = queue.pop(0)
            hierarchy.append(i)
            subItems = i.children(recursive=False)
            if subItems and len(subItems) > 0:
                queue += subItems
        
        return hierarchy

    def addUserChannel(self, name, storageType, username=None):
        """ Adds new user channel to the item.
    
        Parameters
        ----------
        name : str
        
        storageType : str
            Symbol such as the one returned by ChannelStorageType() method.
            sTYPE_STRING, sTYPE_BOOLEAN, etc.
            
        username : str
            Optional user friendly name for a channel.
        
        Returns
        -------
        modo.Channel, None
        """
        if not name or not storageType:
            return False

        # If storage type is matrix then it has to be changed to string type equivalent
        # TODO: This maybe should be changed to looking up a dictionary that converts
        # storage types to string types - just in case in future other channel types
        # do not match between storage type and string requried by channel.create
        if storageType == 'matrix4':
            storageType = 'matrix'

        # Right now creating user channels has to be done via lx.eval
        if username:
            try:
                lx.eval('!channel.create "%s" %s item:{%s} username:{%s}' % (name, storageType, self.id, username))
            except RuntimeError:
                return None
        else:
            try:
                lx.eval('!channel.create "%s" %s item:{%s}' % (name, storageType, self.id))
            except RuntimeError:
                return None
        return self.channel(name)

    def getUserChannelsNames(self, sort=True):
        """ Gets a list of item's user channels.
        
        Parameters
        ----------
        sort : bool
            When set the list will be returned in order in which channels
            are listed on the item. It will be reverse order otherwise.
        """
        chanCount = self.internalItem.ChannelCount()
        chanList = []
        # Channels are scanned in reverse order.
        # The list will have to be reversed at the end.
        # Searching stops at the first channel that belongs
        # to some package. User channels have no package.
        for i in xrange(chanCount - 1, -1, -1):
            try:
                package = self.internalItem.ChannelPackage(i)
            except LookupError:
                chanList.append(self.internalItem.ChannelName(i))
                continue
            else:
                break
    
        if sort:
            chanList.reverse()
        return chanList

    def getUserChannels(self, sort=True):
        """ Gets a list of item's user channels.
        
        Parameters
        ----------
        sort : bool, optional
            When True channels will be sorted in order in which they appear in channel properties.
            The order will be reverse otherwise. Not sorting is faster.
        
        Returns
        -------
        list of modo.Channel
        """
        channels = []
        channelNames = self.getUserChannelsNames(sort)
        for chanName in channelNames:
            chanObj = self.channel(chanName)
            if chanObj is not None and chanObj:
                channels.append(chanObj)
        return channels
    
    def hasUserChannels(self):
        chanCount = self.internalItem.ChannelCount()
        try:
            package = self.internalItem.ChannelPackage(chanCount - 1)
        except LookupError:
            return True
        return False

    @property
    def itemCommand(self):
        return self.channel('ecCmdString').get()
    
    @itemCommand.setter
    def itemCommand(self, cmdString):
        """ Gets/sets item command on an item.
        
        Parameters
        ----------
        cmdString : str
            Item command string the way it should be put into Assembly properties.
        """
        try:
            lx.eval('!item.command add {%s} item:{%s}' % (cmdString, self.id))
        except RuntimeError:
            pass


class ItemUtils(object):
    
    @classmethod
    def autoFocusItemListOnSelection(cls):
        """ Focuses item list on currently selected items.
        """
        try:
            lx.eval("!itemList.find")
        except RuntimeError:
            pass
        
    @classmethod
    def autoPlaceInChain(self, modoItem, offset):
        """ Places given item under currently selected one in hierarchy.
        
        It's useful for quick positioning of items to form a simple chain.
        Note that it only works on locator type items.
        
        Parameters
        ----------
        modoItem : modo.Item
            Item that will be placed into hierarchical chain.
        offset : modo.Vector3
            Offset to apply to item in its local space.
        """
        xitem = Item(modoItem.internalItem)
        if not xitem.isOfXfrmCoreSuperType:
            return
        
        for parentItem in modo.Scene().selected:
            if parentItem.type != modoItem.type:
                continue
            modoItem.setParent(parentItem, -1)
            pos = modo.LocatorSuperType(modoItem).position
            pos.x.set(offset.x, 0.0, False, lx.symbol.s_ACTIONLAYER_SETUP)
            pos.y.set(offset.y, 0.0, False, lx.symbol.s_ACTIONLAYER_SETUP)
            pos.z.set(offset.z, 0.0, False, lx.symbol.s_ACTIONLAYER_SETUP)
            break

    @classmethod
    def addForwardGraphConnections(self, modoItem, targetItems, graphName):
        """ Adds a forward graph connection between items.
        
        Parameters
        ----------
        modoItem : modo.Item
            Item that will have a forward connection going.
            
        targetItems : modo.Item, list of modo.Item
            Items to which the modoItem will be connected to with a forward graph link.
        """
        if type(targetItems) not in (list, tuple):
            targetItems = [targetItems]
        
        plugGraph = modoItem.itemGraph(graphName)
        for targetModoItem in targetItems:
            targetGraph = targetModoItem.itemGraph(graphName)
            plugGraph >> targetGraph
    
    @classmethod
    def getForwardGraphConnections(self, modoItem, graphName):
        """ Gets forward connections from an item on a given graph.
        
        Returns
        -------
        list of modo.Item
            Empty list is returned when there are no connections.
        """
        graph = modoItem.itemGraph(graphName)
        return graph.forward()

    @classmethod
    def getFirstForwardGraphConnection(self, modoItem, graphName):
        """ Gets first forward connection from an item on a given graph.

        Returns
        -------
        modo.Item, None
            None is returned when there are no forward connections.
        """
        graph = modoItem.itemGraph(graphName)
        try:
            return graph.forward(0)
        except LookupError:
            pass
        return None

    @classmethod
    def clearForwardGraphConnections(self, modoItem, graphName, specificItems=[]):
        """ Clears all forward connections from an item on a given graph.
        
        Paramters
        ---------
        specificItems : modo.Item, list of modo.Item, optional
            Optional list of specific items to which given item should not be connected on a graph.
            When set - only connections to specific items will be removed.
        """
        graph = modoItem.itemGraph(graphName)
        existingConnections = graph.forward()

        if not existingConnections:
            return

        if specificItems:
            if type(specificItems) not in (list, tuple):
                specificItems = [specificItems]

        for connection in existingConnections:
            if specificItems and connection not in specificItems:
                continue

            fwdGraph = connection.itemGraph(graphName)
            # Try to understand this order one day
            fwdGraph << graph

    @classmethod
    def hasReverseGraphConnections(cls, modoItem, graphName):
        """
        Tests whether given item as any reverse connections on a given graph.

        Parameters
        ----------
        modoItem : modo.Item
            Item that will be tested.

        graphName : str
            Name of the graph to test.
        """
        graph = modoItem.itemGraph(graphName)
        return graph._graph.RevCount(graph._item) > 0

    @classmethod
    def addReverseGraphConnections(self, modoItem, targetItems, graphName):
        """ Adds reverse graph connections between items.
        
        Parameters
        ----------
        modoItem : modo.Item
            Item that will have a reverse connection going.
            
        targetItems : modo.Item, list of modo.Item
            Items to which the modoItem will be connected to with a reverse graph link.
        """
        if type(targetItems) not in (list, tuple):
            targetItems = [targetItems]
        
        plugGraph = modoItem.itemGraph(graphName)
        for targetModoItem in targetItems:
            targetGraph = targetModoItem.itemGraph(graphName)
            targetGraph >> plugGraph

    @classmethod
    def getReverseGraphConnections(self, modoItem, graphName):
        """ Gets reverse connections from an item on a given graph.
        
        Returns
        -------
        list of modo.Item
            Empty list is returned when there are no reverse connections.
        """
        graph = modoItem.itemGraph(graphName)
        return graph.reverse()

    @classmethod
    def getFirstReverseGraphConnection(self, modoItem, graphName):
        """ Gets first reverse connection from an item on a given graph.
        
        Returns
        -------
        modo.Item, None
            None is returned when there are no reverse connections.
        """
        graph = modoItem.itemGraph(graphName)
        try:
            return graph.reverse(0)
        except LookupError:
            pass
        return None
        
    @classmethod
    def clearReverseGraphConnections(self, modoItem, graphName, specificItems=[]):
        """ Clears all reverse connections from an item on a given graph.
        
        Paramters
        ---------
        specificItems : modo.Item, list of modo.Item, optional
            Optional list of specific items to which given item should not be connected on a graph.
            When set - only connections to specific items will be removed.
        """
        graph = modoItem.itemGraph(graphName)
        existingConnections = graph.reverse()

        if not existingConnections:
            return

        if specificItems:
            if type(specificItems) not in (list, tuple):
                specificItems = [specificItems]

        for connection in existingConnections:
            if specificItems and connection not in specificItems:
                continue

            revGraph = connection.itemGraph(graphName)
            graph << revGraph

    @classmethod
    def getHierarchyRecursive(cls, modoItem, includeRoot=False):
        """ Gets hierarchy in recursive way.
        
        Traversing items tree in recursive way gets the hierarchy in the same
        order as it appears in item list in UI.
        
        Parameters
        ----------
        
        """
        tree = []
        if includeRoot:
            tree = [modoItem]
        cls._traverseTree(modoItem, tree)
        return tree
    
    @classmethod
    def getHierarchyLevel(cls, modoItem):
        """ Gets how deep given item is in hierarchy.
        
        Parameters
        ----------
        modoItem : modo.item
        
        Returns
        -------
        int
        """
        level = 0
        item = modoItem.parent
        while item is not None:
            level += 1
            item = item.parent
        return level

    @classmethod
    def getParentConstraintItem(self, modoItem):
        """ Gets parent constraint item for a given item (if any).
        
        Returns
        -------
        modo.Item or None
        """
        parentChannel = modoItem.channel('parentMatrix')
        
        try:
            inputChannel = parentChannel.reverse(0)
        except LookupError:
            return None

        if inputChannel.item.type != 'cmDynamicParent':
            return None
        
        return inputChannel.item

    @classmethod
    def getWorldMatrixComposeModifier(self, modoItem):
        """ Gets world matrix compose modifier if it's connected to the item.
        
        This is the modifier that combines all 3 world transforms of an item.
        Usually used in dynamic parenting setup.
        """
        wpos = modoItem.channel('wposMatrix')
        wrot = modoItem.channel('wrotMatrix')
        wscl = modoItem.channel('wsclMatrix')
        
        try:
            chan = wpos.forward(0)
            item1 = chan.item
        except LookupError:
            return None
        try:
            chan = wrot.forward(0)
            item2 = chan.item
        except LookupError:
            return None
        try:
            chan = wscl.forward(0)
            item3 = chan.item
        except LookupError:
            return None
        
        if (item1.type == 'cmMatrixCompose' and 
            item1 == item2 and
            item1 == item3):
            return item1
        return None
        
    @classmethod
    def getItemSelectionSets(self, modoItems):
        """ Gets a list of item selection sets given item belongs to.
        
        Returns
        -------
        list of str
            Empty list will be returned if the item is not assigned to any item selection sets.
        """
        if type(modoItems) not in (list, tuple):
            modoItems = [modoItems]
        
        allSets = []
        for modoItem in modoItems:
            try:
                v = modoItem.readTag('SSET')
            except LookupError:
                continue
            itemSets = v.split(';')
            for iset in itemSets:
                if iset not in allSets:
                    allSets.append(iset)
        return allSets

    @classmethod
    def isTransformItem(self, modoItem):
        """ Tests whether given item is of transform type.
        
        Parameters
        ----------
        modoItem : modo.Item
        """
        return modoItem.superType == 'transform'

    @classmethod
    def getTransformItemHost(self, xfrmItem):
        """ Gets
        
        Parameters
        ----------
        xfrmItem : modo.Item of type translation, rotation or scale.
        
        Returns
        -------
        modo.Item, None
            None is returned when transform item does not have 'host'.
        """
        graph = xfrmItem.itemGraph('xfrmCore')
        try:
            return graph.forward(0)
        except LookupError:
            return None
        return None

    @classmethod
    def duplicateItemsAsHierarchy(self, itemList, itemType):
        """ Takes a list of items and creates new hierarchy out of their duplicates.
        
        Returns
        -------
        list of modo.Item
        """
        newItems = []
        scene = modo.Scene()
        
        for item in itemList:
            newItem = scene.addItem(itemType, item.name + '_duplicate')
            newItems.append(newItem)
    
        # Parenting
        if len(newItems) > 1:
            for x in xrange(1, len(newItems)):
                newItems[x].setParent(newItems[x - 1])
    
        # Transform matching
        for x in xrange(len(newItems)):
            lx.eval('!item.match item pos average:false item:{%s} itemTo:{%s}' % (newItems[x].id, itemList[x].id))
            lx.eval('!item.match item rot average:false item:{%s} itemTo:{%s}' % (newItems[x].id, itemList[x].id))
            lx.eval('!item.match item scl average:false item:{%s} itemTo:{%s}' % (newItems[x].id, itemList[x].id))
        
        return newItems
    
    @classmethod
    def setCreateDropScript(self, modoItem, scriptAlias):
        """ Sets create drop script on an item.
        
        Parameters
        ----------
        scriptAlias : str, None
            Needs to be script alias defined in a config for a particular script file.
            Pass None to clear the drop script.
        """
        modoItem.setTag('ACRT', scriptAlias)
    
    @classmethod
    def clearCreateDropScript(self, modoItem):
        """ Clears create drop script from an item.
        """
        modoItem.setTag('ACRT', None)

    @classmethod
    def setSourceDropScript(cls, modoItem, scriptAlias=None):
        """
        Sets or clears source drop script.

        Parameters
        ----------
        scriptAlias : str, None
            Needs to be script alias defined in a config for a particular script file.
            Pass None to clear the drop script.
        """
        modoItem.setTag('IDSS', scriptAlias)

    @classmethod
    def setDestinationDropScript(cls, modoItem, scriptAlias=None):
        """
        Sets or clears destination drop script.

        Parameters
        ----------
        scriptAlias : str, None
            Needs to be script alias defined in a config for a particular script file.
            Pass None to clear the drop script.
        """
        modoItem.setTag('IDSD', scriptAlias)

    @classmethod
    def setItemCommandManually(cls, modoItem, commandString, denyDropAction=False):
        """
        Sets item command manually meaning not using item.command but replicating all this command does.

        This is useful because using item.command fails sometimes - the command is disabled.

        Parameters
        ----------
        modoItem : modo.Item

        commandString : str
        """
        internalItem = modoItem.internalItem
        if not internalItem.PackageTest('execCommand'):
            internalItem.PackageAdd('execCommand')

        modoItem.channel('ecCmdString').set(commandString, time=0.0, key=False, action=lx.symbol.s_ACTIONLAYER_SETUP)
        modoItem.channel('ecEnable').set(True, time=0.0, key=False, action=lx.symbol.s_ACTIONLAYER_SETUP)
        if denyDropAction:
            modoItem.setTag('NDRG', 'denied')

    @classmethod
    def removeItemCommand(cls, modoItem):
        """
        Removes item command from given item.

        Parameters
        ----------
        modoItem : modo.Item
        """
        internalItem = modoItem.internalItem
        if internalItem.PackageTest('execCommand'):
            internalItem.PackageRemove('execCommand')

    @classmethod
    def getItemCommand(cls, modoItem):
        """
        Gets the item command from an item (if any).

        Parameters
        ----------
        modoItem : modo.Item

        Returns
        -------
        str, None
            Command string or None if item command is not set up on an item.
        """
        internalItem = modoItem.internalItem
        if not internalItem.PackageTest('execCommand'):
            return None
        return modoItem.channel('ecCmdString').get(time=0.0, action=lx.symbol.s_ACTIONLAYER_SETUP)

    # -------- Private functions
    
    @classmethod
    def _traverseTree(cls, modoItem, tree):
        children = modoItem.children()
        if children:
            for child in children:
                tree.append(child)
                cls._traverseTree(child, tree)