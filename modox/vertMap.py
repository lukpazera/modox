
import lx
import modo

import const as c


class VertexMapUtils(object):

    @classmethod
    def transferWeights(cls,
                        meshFrom,
                        meshTo,
                        wmapsList,
                        method=c.VertexMapTransferMethod.DISTANCE,
                        skipEmptyMaps=True,
                        monitor=None,
                        ticks=0):
        """ Transfers weights from the list between two meshes.

        Note that this function affects weight maps selection so you may want to
        back selection up before calling this function and then restore it.

        Parameters
        ----------
        meshFrom : modo.Item

        meshTo : modo.Item

        wmapsList : [str]

        method : str
            One of modox.VertexMapTransferMethod constants.

        skipEmptyMaps : bool
            When True transferred weight maps that remain empty are automatically deleted.

        monitor : modox.Monitor

        tick : float
            Number of monitor ticks to spend on the transfer operation.
        """

        if monitor is not None:
            steps = len(wmapsList) + 4
            tick = float(ticks) / float(steps)

        # Add weight maps to the target mesh.
        with modo.Mesh(meshTo).geometry as geo:
            for wmapName in wmapsList:
                if not geo.vmaps[wmapName]: # This returns empty list if vertex map is not on the item.
                    geo.vmaps.addWeightMap(wmapName)
            geo.setMeshEdits()

        if monitor:
            monitor.tick(tick * 2.0)

        # Select mesh from first, then override it with mesh to.
        # I think this puts the meshTo as active (foreground) mesh and puts
        # meshFrom as background mesh.
        # Seems to work correctly with the transfer weights command.
        meshFrom.select(replace=True)
        meshTo.select(replace=True)

        for wmapName in wmapsList:
            # Select weight map to which data will be transfered.
            lx.eval('select.vertexMap %s wght replace' % wmapName)
            lx.eval('vertMap.transfer {%s} weight local %s off true' % (wmapName, method))
            if monitor:
                monitor.tick(tick)

        # Optimize unused deformers.
        if skipEmptyMaps:
            for wmapName in wmapsList:
                # Need to select weight map for now because the rs.vertexMap.empty command
                # works off currently selecte map - its arguments are not implmeented yet.
                lx.eval('select.vertexMap {%s} wght replace' % wmapName)
                isEmpty = lx.eval('rs.vertexMap.empty ? type:wght name:{%s}' % wmapName)
                if isEmpty:
                    lx.eval('vertMap.deleteByName wght {%s}' % wmapName)

        monitor.tick(tick * 2.0)
