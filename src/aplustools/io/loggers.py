import logging
import sys
import threading
from typing import Any, Optional, Callable


raise DeprecationWarning("This module is currently deprecated and will be refactored in the future")


class PrintCaptureLogger:
    def __init__(self,
                 logger_name: str = __name__,
                 log_filename: str = "Default.log",
                 file_log_level=logging.INFO,
                 logging_format: Optional[str] = None,
                 capture_stdout: bool = True,
                 overwrite_stdout: bool = True,
                 stdout_passthrough: bool = True,
                 keyword_filter: Optional[Callable[[str], bool]] = None):
        self.capture_stdout = capture_stdout
        self.stdout_passthrough = stdout_passthrough
        self.keyword_filter = keyword_filter or (lambda msg: False)

        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)

        self.log_file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        self.log_file_handler.setLevel(file_log_level)

        # Set custom logging format if provided
        if logging_format:
            formatter = logging.Formatter(logging_format)
        else:
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        self.log_file_handler.setFormatter(formatter)
        self.logger.addHandler(self.log_file_handler)

        self.lock = threading.Lock()

        if overwrite_stdout:
            sys.stdout = self
            self.terminal = sys.__stdout__
            self.buffer = ''
        else:
            self.terminal = None

    def write(self, message: str):
        """Captures stdout messages."""
        self.buffer += message
        if message.endswith('\n'):
            content = self.buffer.strip()
            self.buffer = ''
            self._log_content(content)

    def _log_content(self, content: str):
        """Logs the content from stdout."""
        with self.lock:
            if self.stdout_passthrough:
                self.terminal.write(content + '\n')
            if self.capture_stdout and not self.keyword_filter(content):
                self.logger.info(content)

    def flush(self):
        """Flush method needed for Python 3 compatibility."""
        pass

    def close(self):
        """Closes the log file and restores the original stdout, if overwritten."""
        with self.lock:
            for handler in self.logger.handlers:
                handler.close()
                self.logger.removeHandler(handler)
            if self.terminal:
                sys.stdout = self.terminal

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Example usage of the PrintCaptureLogger class
def keyword_filter(message: str) -> bool:
    # Define your keywords
    keywords = ['ERROR', 'CRITICAL']
    return any(keyword in message for keyword in keywords)


def classify_type_stan(message: str) -> Tuple[LogType, str]:
    mess = message.lower()
    if any(x in mess for x in ["err", "error"]):
        log_type = LogType.ERR
    elif any(x in mess for x in ["warn", "warning"]):
        log_type = LogType.WARN
    elif any(x in mess for x in ["deb", "debug"]):
        log_type = LogType.DEBUG
    else:
        log_type = LogType.NONE
    return log_type, ""



# Creating an instance of PrintCaptureLogger
logger_name = "my_logger"
log_filename = "app.log"
logging_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

print_logger = PrintCaptureLogger(
    logger_name=logger_name,
    log_filename=log_filename,
    file_log_level=logging.INFO,
    logging_format=logging_format,
    capture_stdout=True,
    overwrite_stdout=True,
    stdout_passthrough=False,
    keyword_filter=keyword_filter
)

# Setting up an existing logger with the same name
logger = logging.getLogger(logger_name)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.ERROR)
console_formatter = logging.Formatter(logging_format)
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# Using the logger
with print_logger:
    logger.debug("This is a debug message from logger")
    logger.info("This is an info message from logger")
    logger.error("This is an error message from logger")
    print("This is a print statement containing ERROR")
    print("This is a regular print statement")
