# utils __init__

from aplustools.package import LazyModuleLoader as _LazyModuleLoader

# Lazy loading modules
dummy = _LazyModuleLoader('aplustools.utils.dummy')

# Define __all__ to limit what gets imported with 'from <package> import *'
__all__ = ['dummy']

# Dynamically add exports from _direct_functions
from aplustools.utils._direct_functions import *

# Update __all__ with the public members from _direct_functions and clean up globals
for name in list(globals()):
    if name.startswith('_') and not (name.startswith('__') and name.endswith('__')):
        # Remove private attributes from globals
        del globals()[name]
    else:
        # Add public attributes to __all__
        __all__.append(name)
del name
