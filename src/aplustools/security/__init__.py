# security __init__

from src.aplustools.package._direct_functions import LazyModuleLoader as _LazyModuleLoader

# Lazy loading modules
protocols = _LazyModuleLoader('aplustools.security.protocols')
crypto = _LazyModuleLoader('aplustools.security.crypto')
database = _LazyModuleLoader('aplustools.security.crypto')
passwords = _LazyModuleLoader('aplustools.security.crypto')
rand = _LazyModuleLoader('aplustools.security.crypto')

# Define __all__ to limit what gets imported with 'from <package> import *'
__all__ = ['protocols', 'crypto', 'database', 'passwords', 'rand']

# Dynamically add exports from _direct_functions

# Update __all__ with the public members from _direct_functions and clean up globals
for name in list(globals()):
    if name.startswith('_') and not (name.startswith('__') and name.endswith('__')):
        # Remove private attributes from globals
        del globals()[name]
    else:
        # Add public attributes to __all__
        __all__.append(name)
del name
