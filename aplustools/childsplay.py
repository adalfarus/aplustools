# childsplay.py, aims to make python standard classes easier and more consistent
import datetime
import warnings
import builtins
from . import adultswork as aw
import sys
import inspect


class ExperimentalError(Warning):
    pass

warnings.warn("This module is still experimental. Please use with caution", 
              ExperimentalError, 
              stacklevel=2)

warnings.warn("This will alter the internal variable classes of python, be sure to only use it when learning python! If you want to use this in a real world application, use adultswork instead.", 
              UserWarning, 
              stacklevel=2)

class ImportClass:
    def __init__(self, hard: bool=False):
        self.hard = hard
    def str_import(self):
        if not self.hard: str = aw.EnhancedString
        else: sys.modules['builtins'].str = aw.EnhancedString
    def dict_import(self):
        if not self.hard: dict = aw.EnhancedDict
        else: sys.modules['builtins'].dict = aw.EnhancedDict
    def list_import(self):
        if not self.hard: list = aw.EnhancedList
        else: sys.modules['builtins'].list = aw.EnhancedList
    def int_import(self):
        if not self.hard: int = aw.EnhancedInteger
        else: sys.modules['builtins'].int = aw.EnhancedInteger
    def float_import(self):
        if not self.hard: float = aw.EnhancedFloat
        else: sys.modules['builtins'].float = aw.EnhancedFloat
    def set_import(self):
        if not self.hard: set = aw.EnhancedSet
        else: sys.modules['builtins'].set = aw.EnhancedSet
    def file_import(self):
        from .adultswork import EnhancedFile
    def datetime_import(self):
        from .adultswork import EnhancedDateTime
    def tuple_import(self):
        if not self.hard: tuple = aw.EnhancedTuple
        else: sys.modules['builtins'].tuple = aw.EnhancedTuple
    def import_all(self):
        public_method_names = [method for method in dir(self) if callable(getattr(self, method)) if not method.startswith('_')]  # 'private' methods start from _
        for method in public_method_names:
            if not method == "import_all": getattr(self, method)()
