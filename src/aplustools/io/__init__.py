# io __init__

from src.aplustools import LazyModuleLoader as _LazyModuleLoader

# Lazy loading modules
environment = _LazyModuleLoader('aplustools.io.environment')
loggers = _LazyModuleLoader('aplustools.io.loggers')
gui = _LazyModuleLoader('aplustools.io.gui')

# Define __all__ to limit what gets imported with 'from <package> import *'
__all__ = ['environment', 'loggers', 'gui']

# Dynamically add exports from _direct_functions
from src.aplustools import *

# Update __all__ with the public members from _direct_functions and clean up globals
for name in list(globals()):
    if name.startswith('_') and not (name.startswith('__') and name.endswith('__')):
        # Remove private attributes from globals
        del globals()[name]
    else:
        # Add public attributes to __all__
        __all__.append(name)
del name
