

import lx


class Monitor(object):
    """ Wrapper for using progress monitors.
    
    Parameters
    ----------
    ticksCount : int
        How many tick in total monitor will have. The last tick is 100% progress.
    
    title : str
        Title string for the monitor.
    """
    
    def setup(self, ticksCount, title):
        """ Sets up new monitor.
        
        When previous monitor was not released it'll spawn new submonitor I think.
        
        Parameters
        ----------
        ticksCount : int
            How many tick in total monitor will have. The last tick is 100% progress.
        
        title : str
            Title string for the monitor.
        """
        if ticksCount < 1:
            ticksCount = 1

        self._dialogService = lx.service.StdDialog()
        self._monitor = lx.object.Monitor(self._dialogService.MonitorAllocate(title))
        self._monitor.Initialize(int(ticksCount))

        self._totalTicks = ticksCount
        self._intTicksProgress = 0
        self._floatTicksProgress = 0.0

    @property
    def monitor(self):
        """ Gets the internal monitor object.
        
        Returns
        -------
        lx.object.Monitor
        """
        return self._monitor

    def tick(self, tickAmount):
        """ Increments monitor by tickAmount.
        
        Float is used for tick amount despite the fact the monitor works with ints.
        This allows for more precise progress counting.

        Parameters
        ----------
        tickAmount : float
        """
        self._floatTicksProgress += tickAmount
        self._intTicksProgress += int(tickAmount)
        
        missingTicks = int(self._floatTicksProgress) - self._intTicksProgress
        if missingTicks > 0:
            tickAmount += missingTicks
            self._intTicksProgress += missingTicks

        self._monitor.Increment(int(tickAmount))

    @property
    def progress(self):
        return self._intTicksProgress

    @progress.setter
    def progress(self, tickAmount):
        """ Sets monitor to given tick amount.
        
        The amount has to be larger then current tick.
        This is useful to make sure monitor reaches desired progress at a given point.
        
        Paramters
        ---------
        tickAmount : int
        """
        tickAmount = int(tickAmount)
        if tickAmount <= int(self._floatTicksProgress):
            return
        missingTicks = tickAmount - self._intTicksProgress
        if missingTicks > 0:
            self._monitor.Increment(missingTicks)

    def release(self):
        """ Releases monitor.
        
        This HAS to be called when the job is done!
        """
        self._dialogService.MonitorRelease()

    # -------- Private methods

    def __init__ (self, ticksCount=None, title=None):
        self._monitor = lx.object.Monitor()
        if ticksCount is not None and title is not None:
            self.setup(ticksCount, title)

