import sys
import time
from typing import TextIO, Union, Optional, Type, Callable
import builtins # Remove, when removeing deprecated functions in 0.1.4
from enum import Enum
import warnings


class Logger(object):
    def __init__(self, filename: str="Default.log", show_time: bool=True, print_log_to_stdout: bool=True, *_, **__):
        self.show_time = show_time
        self.print_log_to_stdout = print_log_to_stdout
        self.log_file = open(filename, "a", encoding='utf-8')
        
    def _add_timestamp(self, message: str) -> str:
        """Adds a timestamp to the message if show_time is True."""
        if self.show_time and message.strip():
            timestamp = f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())}] " if self.show_time else ''
            return timestamp + message if message != '\n' else message
        return message
    
    def log(self, message: str):
        """Logs a message to the file and optionally to stdout."""
        message_with_timestamp = self._add_timestamp(message) + "\n"
        self.log_file.write(message_with_timestamp)
        self.log_file.flush()
        if self.print_log_to_stdout:
            self._write_to_stdout(message_with_timestamp)
            
    def _write_to_stdout(self, message: str):
        """Writes message to stdout."""
        print(message)
        
    def close(self):
        """Closes the log file."""
        self.log_file.close()
        
    def __del__(self):
        """Destructor to ensure the log file is closed properly."""
        self.close()

class LogType(Enum):
    NONE = ""
    DEBUG = "[DEBUG] "
    WARN = "[WARN] "
    ERR = "[ERR] "
    ANY = None
    
def overwrite_logtype(new_logtype: Type[LogType]):
    LogType = new_logtype

class PrintLogger(Logger):
    def __init__(self, filename: str="Default.log", show_time: bool=True, 
                 capture_print: bool=True, overwrite_print: bool=True, 
                 print_passthrough: bool=True, print_log_to_stdout: bool=True, *_, **__):
        super().__init__(filename, show_time, print_log_to_stdout)
        self.capture_print = capture_print
        self.terminal = sys.stdout if overwrite_print else None
        self.print_passthrough = print_passthrough
        self.buffer = ''
            
    def _check_content(self, content: str):
        """Check the content from stdout traffic."""
        if self.capture_print:
            message_with_timestamp = self._add_timestamp(content)
            self.log_file.write(message_with_timestamp)
            self.log_file.flush()
        if self.print_passthrough:
            message_with_timestamp = self._add_timestamp(content)
            self._write_to_stdout(message_with_timestamp)

    def _write_to_stdout(self, message: str): # Overwrite this with the new one
        """Writes message to stdout."""
        if self.terminal is not None:
            self.terminal.write(message)
            self.terminal.flush()

    def write(self, message: str):
        """Original write, here to catch any stdout traffic."""
        self.buffer += message
        if message.endswith('\n'):
            content = self.buffer
            self.buffer = ''
            self._check_content(content)

    def flush(self):
        # this flush method is needed for python 3 compatibility.
        # this handles the flush command by doing nothing.
        # Flush behaviour is already handled elsewhere.
        pass
        
    def close(self): # Overwrite this too
        """Closes the log file and restores the original stdout, if overwritten."""
        self.log_file.close()
        if self.terminal:
            sys.stdout = self.terminal

def classify_type_stan(message: str) -> LogType:
    mess = message.lower()
    if any(x in mess for x in ["err", "error"]):
        return LogType.ERR
    elif any(x in mess for x in ["warn", "warning"]):
        return LogType.WARN
    elif any(x in mess for x in ["deb", "debug"]):
        return LogType.DEBUG
    else: return LogType.NONE

class TypeLogger(PrintLogger):
    def __init__(self, filename: str="Default.log", show_time: bool=True, capture_print: bool=True, # The , *_, **__ need to be added as direct init calls lead to errors
                 overwrite_print: bool=True, show_type: bool = True, classify_type_func: Callable = classify_type_stan, #capture_type: bool=True, 
                 print_passthrough: bool=True, print_log_to_stdout: bool=True, use_type: bool=True, cu_type: Type[LogType]=LogType.ANY, *_, **__):
        super().__init__(filename, show_time, capture_print, overwrite_print, print_passthrough, print_log_to_stdout)
        self.show_type = show_type
        self._classify_type_func = classify_type_func
        self.use_type = use_type
        self._cu_type = cu_type
        #self.capture_type = capture_type # Removed this, as you can just make your own subclass if you really need it

    @property
    def classify_type_func(self):
        return self._classify_type_func
    
    @classify_type_func.setter
    def classify_type_func(self, value):
        self._classify_type_func = value

    @classify_type_func.deleter
    def classify_type_func(self):
        tb = sys.exception().__traceback__
        raise NotImplementedError("...").with_traceback(tb)
        #del self._classify_type_func

    @property
    def cu_type(self):
        return self._cu_type
    
    @cu_type.setter
    def cu_type(self, value):
        self._cu_type = value

    @cu_type.deleter
    def cu_type(self):
        tb = sys.exception().__traceback__
        raise NotImplementedError("...").with_traceback(tb)
        #del self._cu_type

    def _add_type(self, message: str) -> str:
        """Adds the type to the message if show_type is True."""
        if self.show_type and message.strip() and self.use_type:
            message_type = classify_type_stan(message) if self.show_type else ''
            if self._cu_type == message_type or self._cu_type == LogType.ANY:
                return message_type.value + message if message != '\n' else message
        return message
    
    def _add_timestamp(self, message: str) -> str:#, add_type: bool=True) -> str:
        """Adds a timestamp to the message if show_time is True. The type is also added, if show_type is true"""
        if self.show_time and message.strip():
            timestamp = f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())}] " if self.show_time else ''
            message = timestamp + message if message != '\n' else message
        if self.show_type:# and add_type:
            message = self._add_type(message)
        return message
    
#    def log(self, message: str):
#        """Logs a message to the file and optionally to stdout."""
#        message_with_timestamp = self._add_timestamp(message, self.capture_type) + "\n"
#        self.log_file.write(message_with_timestamp)
#        self.log_file.flush()
#        if self.print_log_to_stdout:
#            message_with_timestamp = self._add_timestamp(message, self.show_type) + "\n"
#            self._write_to_stdout(message_with_timestamp)
#            
#    def _check_content(self, content: str):
#        """Check the content from stdout traffic."""
#        if self.capture_print:
#            message_with_timestamp = self._add_timestamp(content, self.capture_type)
#            self.log_file.write(message_with_timestamp)
#            self.log_file.flush()
#        if self.print_passthrough:
#            message_with_timestamp = self._add_timestamp(content, self.show_type)
#            self._write_to_stdout(message_with_timestamp)

def monitor_stdout(log_file: Optional[str]=None, logger: Optional[Type[Logger]]=None) -> Union[TextIO, Type[Logger]]:
    """Monitors and logs stdout messages based on given parameters.

    Args:
        log_file: The name of the log file.
        logger: An instance of the Logger class.

    Returns:
        An instance of the Logger class with stdout being monitored and logged.
    """
    if logger is None:
        if log_file is None:
            raise ValueError("Either log_file or logger must be provided")
        logger = PrintLogger(log_file)
    elif type(logger) is Logger:
        raise ValueError("The default Logger class wasn't built to be used like this, please use PrintLogger or TypeLogger instead.")
    
    sys.stdout = logger
    return sys.stdout

def cprint(*args, sep=' ', end='\n', file=None, flush=False):
    warnings.warn("This function is for an older version of this library, please stop using it as it will be removed in version 0.1.4.", 
                  DeprecationWarning, 
                  stacklevel=2)
    # Concatenate all the items passed to the function
    concatenated_args = sep.join(map(str, args))
    # Call the original print function to output the result
    builtins.print(concatenated_args, end=end, file=file, flush=flush)

def overwrite_print():
    warnings.warn("This function is for an older version of this library, please stop using it as it will be removed in version 0.1.4.", 
                  DeprecationWarning, 
                  stacklevel=2)
    print = cprint

def local_test():
    #cprint("Test") # Deprecated, no need to test
    #overwrite_print()
    #print("Test22")
    logger = Logger("./cu.txt")
    logger.log("Hello Worlds")
    logger2 = PrintLogger("./cu.txt")
    print("Hellow worldddsssss")
    monitor_stdout(logger=logger2)
    print("Logging this")
    logger2.log("Logging that")
    logger2.close()
    print("Just print lol")
    ref = monitor_stdout(logger=TypeLogger("./cu.txt"))
    print("[Debug] No ref, so just print xd")
    print("[Warn] No ref, so just print xd")
    print("Do not do this, you need a ref to close it")
    ref.close()
    print("DONE")
    return True # Works
    
if __name__ == "__main__":
    local_test()
