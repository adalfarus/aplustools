# aplustools __init__
__version__ = "1.4.9"


from aplustools.package import LazyModuleLoader as _LazyModuleLoader

# Lazy loading modules
io = _LazyModuleLoader('aplustools.io')
data = _LazyModuleLoader('aplustools.data')
utils = _LazyModuleLoader('aplustools.utils')
web = _LazyModuleLoader('aplustools.web')
package = _LazyModuleLoader('aplustools.package')

# Define __all__ to limit what gets imported with 'from <package> import *'
__all__ = ['io', 'data', 'utils', 'web', 'package']

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
