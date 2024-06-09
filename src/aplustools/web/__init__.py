# web __init__

from aplustools.package import LazyModuleLoader as _LazyModuleLoader

# Lazy loading modules
utils = _LazyModuleLoader('aplustools.web.utils')
request = _LazyModuleLoader('aplustools.web.request')
search = _LazyModuleLoader('aplustools.web.search')

# Define __all__ to limit what gets imported with 'from <package> import *'
__all__ = ['utils', 'request', 'search']

# Dynamically add exports from _direct_functions
from aplustools.web._direct_functions import *

# Update __all__ with the public members from _direct_functions and clean up globals
for name in list(globals()):
    if name.startswith('_') and not (name.startswith('__') and name.endswith('__')):
        # Remove private attributes from globals
        del globals()[name]
    else:
        # Add public attributes to __all__
        __all__.append(name)
del name
