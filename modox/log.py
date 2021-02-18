

import os.path

import lx


class Log(object):
    """ Allows for printing messages to custom MODO log.
    
    Parameters
    ----------
    logSystemName : str
        Name of the log system that output will go to.
    
    defaultSystemName : str, optional
        When requested log system cannot be found log output
        will fall back on the default one. It's set to 'python' by default,
        you can change it to another default log only. Don't use custom here
        as if it fails this class will fail initialisation too.
    """

    MSG_INFO = lx.symbol.e_INFO
    MSG_WARNING = lx.symbol.e_WARNING
    MSG_ERROR = lx.symbol.e_FAILED

    MSG_TYPE_PREFIX = {MSG_INFO: '',
                       MSG_WARNING: 'WARNING: ',
                       MSG_ERROR: 'ERROR: '}

    LOG_INSET = '    '
    
    def out(self, messageString, messageType=MSG_INFO):
        """ Prints the message out.
        
        Parameters
        ----------
        messageString : str
            Message to print out via the log.
        
        messageType : constant
            One of predefined message type constants (such as MSG_INFO).
        """
        if not isinstance(messageString, str):
            messageString = str(messageString)

        entry = self._logService.CreateEntryMessage(messageType, messageString)
        self._lastEntry = entry
        if self._parentEntry is not None:
            self._parentEntry.AddEntry(entry)
        else:
            self._logSystem.AddEntry(entry)

        if self._outputToFile and self._outputFilename:
            m = self._inset + self.MSG_TYPE_PREFIX[messageType] + messageString + "\n"
            f = open(self._outputFilename, mode='a')
            f.write(m)
            f.close()
        
    def startChildEntries(self):
        self._parentEntry = self._lastEntry
        self._inset += self.LOG_INSET

    def stopChildEntries(self):
        self._parentEntry = None
        self._inset = ''

    def outputToFile(self, filename):
        """ Triggers outputting log messages to a file.
        
        Parameters
        ----------
        filename : str, None
            Pass filename to start outputting to a given file (it will be overwritten!)
            or None to stop outputting to a file.
        """
        if filename is not None:
            self._outputFilename = filename
            self._outputToFile = True
        else:
            self._outputFilename = ''
            self._outputToFile = False
        
        if self._outputToFile:
            f = open(filename, mode='w')
            f.write('Debug Logging Started\n')
            f.write('---------------------\n')
            f.close()

    # -------- Private Methods
    
    def __init__(self, logSystemName, defaultSystemName='python'):
        self._logName = logSystemName
        self._logService = lx.service.Log()
        try:
            self._logSystem = self._logService.SubSystemLookup(self._logName)
        except LookupError:
            self._logSystem = self._logService.SubSystemLookup(defaultSystemName)
        self._lastEntry = None
        self._parentEntry = None
        self._outputToFile = False
        self._outputFilename = ''
        self._inset = ''