

import lx


class MessageCode(object):
    OK = lx.symbol.e_OK
    FALSE = lx.symbol.e_FALSE
    ABORT = lx.symbol.e_ABORT
    FAILED = lx.symbol.e_FAILED


class Message(object):
    """ Wrapper for lx.object.Message. More user friendly hopefully.
    
    Parameters
    ----------
    msg : lx.object.Message
        Initialise class with raw message object.
    """

    Code = MessageCode

    @classmethod
    def getMessageTextFromTable(cls, table, key, arguments=[]):
        """ Resolves message from given table id and message key.
        
        This is class method that doesn't require separate message object.
        
        Returns
        -------
        str
        """
        msgService = lx.service.Message()
        msg = lx.object.Message(msgService.Allocate())
        xmsg = Message(msg)
        xmsg.set(table, key, arguments=arguments)
        return xmsg.text
        
    def set(self, msgTable, msgKey, arguments=[]):
        """ Sets a message for message table and message keys.
        
        Parameters
        ----------
        msgTable : str
            Key for message table defined in config.
        
        msgKey : str
            Key for the message as defined in config.
            
        arguments : list
            optional list of arguments if message requires them.
            Subsequent arguments relate to %1, %2, %3, etc. arguments
            in the message string.
            Ints, floats, strings and objects are supported.
            
        Raises
        ------
        LookupError
            When message was not found.
        """
        try:
            self._msg.SetMessage(msgTable, msgKey, 0)
        except RuntimeError:
            raise LookupError
        
        if arguments:
            if type(arguments) not in (tuple, list):
                arguments = [arguments]
                
            argIndex = 1
            for value in arguments:
                if type(value) in (int, long):
                    self._msg.SetArgumentInt(argIndex, value)
                elif isinstance(value, float):
                    self._msg.SetArgumentFloat(argIndex, value)
                elif isinstance(value, str):
                    self._msg.SetArgumentString(argIndex, value)
                else:
                    self._msg.SetArgumentObject(argIndex, value)
                argIndex += 1

    @property
    def text(self):
        """ Gets message text. Works after message is set via set().
        """
        msgService = lx.service.Message()
        return msgService.MessageText(self._msg)

    def setCode(self, code):
        """
        Sets message code. This is used to abort method using this message object
        such as cmd_Interact() or basic_execute().

        Parameters
        ----------
        code : MessageCode
            One of MessageCode constants.
        """
        self._msg.SetCode(code)

    # -------- Private methods
    
    def __init__(self, msg):
        self._msg = lx.object.Message(msg)