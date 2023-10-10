import sys
import time

class Logger(object):
    def __init__(self, filename="Default.log"):
        self.terminal = sys.stdout
        self.log = open(filename, "a")

    def write(self, message):
        timestamp = f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())}] "
        message_with_timestamp = timestamp + message if message != '\n' else message
        if self.terminal is not None:
            try:
                self.terminal.write(message_with_timestamp)
            except Exception as e:
                pass
        self.log.write(message_with_timestamp)
        self.log.flush()

    def flush(self):
        # this flush method is needed for python 3 compatibility.
        # this handles the flush command by doing nothing.
        # you might want to specify some extra behavior here.
        pass
        
def monitor_stdout(log_file):
    sys.stdout = Logger(log_file)
    