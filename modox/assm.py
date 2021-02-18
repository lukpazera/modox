
import lx
import modo

from item import Item


class Assembly(object):
    """ A set of functions to work on modo assembly items.
    """
    
    @classmethod
    def load(cls, filename):
        """ Loads assembly from file.
        
        This is just a wrapper for the command that loads an assembly.
        This function does not know what assembly was loaded so doesn't return
        any assembly object.
        """
        pass
    
    @classmethod
    def save(cls, assmItem, filename, description=None):
        """ Saves an assembly as .lxp preset.
        
        Note that this function changes MODO's item selection!
        
        Parameters
        ----------
        assmItem : modo.Item
        
        filename : str
            Full filename including extension.
        
        description : str
            When provided this string will be added as description to the preset
            and will show up under preset thumbnail in preset browser.
        """
        assmItem.select(replace=True)
        cmd = '!item.selPresetSave type:locator filename:{%s}' % (filename)
        if description:
            cmd += (' desc:{%s}' % description)
        try:
            lx.eval(cmd)
        except RuntimeError:
            return False
        return True

    @classmethod
    def delete(cls, assmItem, includeChildren=True):
        """ Deletes assembly and all its contents.
        
        Paramters
        ---------
        assmItem : modo.Item
        
        includeChildren : bool
            When True all child assemblies will be deleted as well.
        """
        lx.eval('!item.delete group child:%d item:{%s}' % (int(includeChildren), assmItem.id))
    
    @classmethod
    def addSubassembly(cls, subassmModoItem, assmModoItem, parentIndex=-1):
        """ Adds an assembly to another assembly.
        
        subassmModoItem : modo.Item
        
        assmModoItem : modo.Item, modo.Group
        """
        if not isinstance(assmModoItem, modo.Group):
            assmModoItem = modo.Group(assmModoItem)
            
        subassmModoItem.setParent(assmModoItem, index=parentIndex)
        assmModoItem.addItems(subassmModoItem)
    
    @classmethod
    def getSubassemblies(cls, assmModoItem, recursive=True):
        """ Gets subassemblies of a given assembly.
        
        Subassemblies are assemblies parented to this assembly (or one of its subassemblies).
        
        Parameters
        ----------
        assmModoItem : modo.Item
        
        recursive : bool
            When True entire hierarchy of subassemblies will be returned, not just children.
        
        Returns
        -------
        list of modo.Item
        """
        return assmModoItem.children(recursive=recursive)
    
    @classmethod
    def getInputChanels(cls, assmModoItem):
        """ Gets all the input channels of a given assembly.
        
        Paramters
        ---------
        assmModoItem : modo.Item
            The assembly which inputs need to returned.
        
        Returns
        -------
        list of modo.Channel
            Empty list is returned when there are no inputs.
        """        
        inputs, outputs = cls.getInputOutputChannels(assmModoItem)
        return inputs
    
    @classmethod
    def getOutputChannels(cls, assmModoItem):
        """ Gets all the output channels of a given assembly.
        
        Paramters
        ---------
        assmModoItem : modo.Item
            The assembly which outputs need to returned.
        
        Returns
        -------
        list of modo.Channel
            Empty list is returned when there are no outputs.
        """         
        inputs, outputs = cls.getInputOutputChannels(assmModoItem)
        return outputs
    
    @classmethod
    def getInputOutputChannels(cls, assmModoItem):
        """ Gets all the input and output channels of a given assembly.
        
        Paramters
        ---------
        assmModoItem : modo.Item
            The assembly which inputs/outputs need to returned.
        
        Returns
        -------
        list1, list2 of modo.Channel
            list1 are inputs, list2 are outputs.
            Empty lists are returned if there are no inputs or outputs.
        """
        userChannels = Item(assmModoItem.internalItem).getUserChannels()
        graph = lx.object.ChannelGraph(assmModoItem.scene.GraphLookup('assemblyChans'))
        
        inputs = []
        outputs = []
        
        # The channel is an input if it has a rev link on the assemblyChans graph.
        # The link goes from to the assembly item itself to its -1 index channel.
        # The output is the same but is fwd link.
        for chan in userChannels:
            if graph.RevCount(assmModoItem, chan.index) > 0:
                inputs.append(chan)
            elif graph.FwdCount(assmModoItem, chan.index) > 0:
                outputs.append(chan)
        return inputs, outputs

    @classmethod
    def autoConnectOutputsToInputs(cls, assemblyFrom, assemblyTo):
        """
        Automatically connects outputs of the assemblyFrom to inputs of assemblyTo.
        Channels are matched by name.

        Parameters
        ----------
        assemblyFrom : modo.Item

        assemblyTo : modo.Item
        """
        outputs = cls.getOutputChannels(assemblyFrom)
        inputs = cls.getInputChanels(assemblyTo)

        inputsByName = {}
        for input in inputs:
            inputsByName[input.name] = input

        for outChan in outputs:
            try:
                inChan = inputsByName[outChan.name]
            except KeyError:
                continue
            outChan >> inChan

    @classmethod
    def isItemInAssemblyHierarchy(self, modoItem, rootAssemblyModoItem):
        """ Tests whether given item is in assembly hierarchy of given root assembly.
        
        In practice, we want to know if an item is either in a given assembly
        or inside one of its subassemblies.
        
        Parameters
        ----------
        modoItem : modo.Item
            Item that needs to be tested.
            
        rootAssemblyModoItem : modo.Item
            Root of assemblies hierarchy. It has to be assembly/group item.
        
        Returns
        -------
        bool
        """
        itemGroups = modoItem.connectedGroups
        if itemGroups is None:
            return False

        # If required group is right there on first level, return True.
        if rootAssemblyModoItem in itemGroups:
            return True
        
        # If not go up groups hierarchy for each group the item is in.
        for groupModoItem in itemGroups:
            parentGroup = groupModoItem.parent
            while parentGroup is not None:
                if parentGroup == rootAssemblyModoItem:
                    return True
                parentGroup = parentGroup.parent
        
        return False
        
    @classmethod
    def iterateOverSubassemblies(cls, assmModoItem, callback, recursive=True):
        """ Iterates over all subassemblies.
        
        Paramters
        ---------
        assmModoItem : modo.Item
        
        callback : function
            This function will be called for every subassembly. The subassembly item is given
            as first and only argument to function.
        """
        subassms = cls.getSubassemblies(assmModoItem, recursive=recursive)
        for sub in subassms:
            result = callback(sub)
            if result:
                break
    
    @classmethod
    def iterateOverItems(cls, assmModoItem, callback, includeSubassemblies=True, assmTestCallback=None):
        """ Iterates over all items contained within given assembly.
        
        Iterating includes subassemblies by default.
        The assembly item itself is also iterated.
        
        Parameters
        ----------
        assmModoItem : modo.Item
            The assembly which contents should be iterated.
            
        callback : function
            Function that will be called on each item.
            This function should take modo.Item as its first and only argument.
            
            Returns:
            Callback can return True to terminate iteration at any step.
            Don't return any value to keep going through entire loop.
        
        includeSubassemblies : bool, optional
            When True subassemblies will be included in iteration.
        
        assmTestCallback : function, optional
            Only relevant when includeSubassemblies is True.
            Pass callback if you want to test subassemblies before including their items in iteration.
            Callback needs to take single argument which is assembly modo item and return True or False.
            
            Parameters:
            assmModoItem : modo.Item
            
            Returns:
            bool : True to include subassembly, False otherwise.
        """
        itemList = []
        assemblies = [assmModoItem]
        if includeSubassemblies:
            if assmTestCallback is None:
                assemblies.extend(assmModoItem.children(recursive=True))
            else:
                # Test assemblies before including.
                subassms = assmModoItem.children(recursive=True)
                for modoItem in subassms:
                    if assmTestCallback(modoItem):
                        assemblies.append(modoItem)
                        
        for assm in assemblies:
            itemList.append(assm)
            try:
                itemList.extend(assm.items)
            except AttributeError:
                continue

        for item in itemList:
            result = callback(item)
            if result:
                break