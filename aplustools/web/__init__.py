# web __init__

class _LazyModuleLoader:
    def __init__(self, module_name):
        self.module_name = module_name
        self.module = None

    def _load_module(self):
        if self.module is None:
            try:
                self.module = __import__(self.module_name, globals(), locals(), ['*'])
            except ImportError:
                raise ImportError("Optional module not installed. Please install it to use this feature.")
        return self.module

    def __repr__(self):
        if self.module is None:
            return f"<LazyModuleLoader for '{self.module_name}'>"
        else:
            return repr(self.module)

    def __getattr__(self, item):
        module = self._load_module()
        return getattr(module, item)

    def __dir__(self):
        self._load_module()
        return dir(self.module)


# Lazy loading modules
webtools = _LazyModuleLoader('aplustools.web.webtools')

# Install all possible dependencies, execute python command, ...
from ._direct_functions import *

# Define __all__ to limit what gets imported with 'from <package> import *'
__all__ = ['webtools']
