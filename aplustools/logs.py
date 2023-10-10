import sys
import time

class Logger(object):
    def __init__(self, filename="Default.log", show_time=True, capture_print=True, overwrite_print=True):
        self.show_time = show_time
        self.capture_print = capture_print
        self.terminal = sys.stdout if overwrite_print else None
        self.log = open(filename, "a")
        self.buffer = ''

    def log(self, message):
        timestamp = f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())}] " if self.show_time else ''
        message_with_timestamp = timestamp + message if message != '\n' else message
        self.log.write(message_with_timestamp)
        self.log.flush()

    def write(self, message):
        self.buffer += message
        if message.endswith('\n'):
            content = self.buffer
            self.buffer = ''
            if self.capture_print:
                timestamp = f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())}] " if self.show_time else ''
                message_with_timestamp = timestamp + content
                if self.terminal is not None:
                    self.terminal.write(message_with_timestamp)
                    self.terminal.flush()
                self.log.write(message_with_timestamp)
                self.log.flush()
            elif self.terminal is not None:
                self.terminal.write(content)
                self.terminal.flush()

    def flush(self):
        # this flush method is needed for python 3 compatibility.
        # this handles the flush command by doing nothing.
        # you might want to specify some extra behavior here.
        pass
        
    def close(self):
        self.log.close()
        if self.terminal:
            sys.stdout = self.terminal
        
def monitor_stdout(log_file):
    sys.stdout = Logger(log_file)
    