# aplustools __init__
__version__ = "1.5.0"


class _LazyModuleLoader:  # Shared code with aplustools.package
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
io = _LazyModuleLoader('aplustools.io')
data = _LazyModuleLoader('aplustools.data')
utils = _LazyModuleLoader('aplustools.utils')
web = _LazyModuleLoader('aplustools.web')
package = _LazyModuleLoader('aplustools.package')
security = _LazyModuleLoader('aplustools.security')

# Define __all__ to limit what gets imported with 'from <package> import *'
__all__ = ['io', 'data', 'utils', 'web', 'package', 'security']

# Dynamically add exports from _direct_functions
from aplustools._direct_functions import *

# Update __all__ with the public members from _direct_functions and clean up globals
for name in list(globals()):
    if name.startswith('_') and not (name.startswith('__') and name.endswith('__')):
        # Remove private attributes from globals
        del globals()[name]
    else:
        # Add public attributes to __all__
        __all__.append(name)
del name
