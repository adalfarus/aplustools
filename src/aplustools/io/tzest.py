import traceback
import sys

class CustomException(Exception):
    def __init__(self, message, essential_tb):
        super().__init__(f"{message}\n\nSimplified Traceback:\n{essential_tb}")

def simplified_traceback(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            # Extract the traceback
            tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            essential_tb = ''.join(tb_lines[-3:])  # Adjust this based on how much info you need
            raise CustomException("", essential_tb) from e
    return wrapper

@simplified_traceback
def example_function():
    # function body
    raise KeyError("HELL")

example_function()