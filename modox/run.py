
import lx

from log import Log

def run(cmdString, logErrors=True, log=None):
    """ Runs a command via lx.eval.
    
    Parameters
    ----------
    cmdString : str
        Command string to run.
        
    log : modox.Log, None
        Log to output potential error messages through.
        When None is passed a standard 'python' log is used.
    
    Returns
    -------
    Return value from lx.eval (if any).
    """
    try:
        return lx.eval(cmdString)
    except RuntimeError, e:
        if logErrors:
            if log is None:
                log = Log('python')
            log.out('Command Failed: %s' % cmdString, log.MSG_ERROR)
            log.startChildEntries()
            log.out(e.message, log.MSG_ERROR)
            log.stopChildEntries()
    return None