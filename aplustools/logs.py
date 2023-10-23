import sys
import time
from typing import TextIO, Union, Optional
import builtins

class Logger(object):
    def __init__(self, filename: str="Default.log", show_time: bool=True, 
                 capture_print: bool=True, overwrite_print: bool=True, 
                 print_passthrough: bool=True, print_log_to_stdout: bool=True):
        self.show_time = show_time
        self.capture_print = capture_print
        self.terminal = sys.stdout if overwrite_print else None
        self.print_passthrough = print_passthrough
        self.print_log_to_stdout = print_log_to_stdout
        self.log_file = open(filename, "a")
        self.buffer = ''

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
            
    def _check_content(self, content: str):
        """Check the content from stdout traffic."""
        if self.capture_print:
            message_with_timestamp = self._add_timestamp(content)
            self.log_file.write(message_with_timestamp)
            self.log_file.flush()
        if self.print_passthrough:
            message_with_timestamp = self._add_timestamp(content)
            self._write_to_stdout(message_with_timestamp)

    def _write_to_stdout(self, message: str):
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
        
    def close(self):
        """Closes the log file and restores the original stdout, if overwritten."""
        self.log_file.close()
        if self.terminal:
            sys.stdout = self.terminal

def monitor_stdout(log_file: Optional[str]=None, logger: Optional[Logger]=None) -> Union[TextIO, Logger]:
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
        logger = Logger(log_file)
    
    sys.stdout = logger
    return sys.stdout

def cprint(*args, sep=' ', end='\n', file=None, flush=False):
    # Concatenate all the items passed to the function
    concatenated_args = sep.join(map(str, args))
    # Call the original print function to output the result
    builtins.print(concatenated_args, end=end, file=file, flush=flush)

def overwrite_print():
    print = cprint
