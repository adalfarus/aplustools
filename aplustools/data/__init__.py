# data __init__

from aplustools.package import LazyModuleLoader as _LazyModuleLoader

# Lazy loading modules
database = _LazyModuleLoader('aplustools.data.database')
updaters = _LazyModuleLoader('aplustools.data.updaters')
faker = _LazyModuleLoader('aplustools.data.faker')
imagetools = _LazyModuleLoader('aplustools.data.imagetools')
advanced_imagetools = _LazyModuleLoader('aplustools.data.advanced_imagetools')
compressor = _LazyModuleLoader('aplustools.data.compressor')

# Define __all__ to limit what gets imported with 'from <package> import *'
__all__ = ['database', 'updaters', 'faker', 'imagetools', 'advanced_imagetools', 'compressor']

# Dynamically add exports from _direct_functions
from aplustools.data._direct_functions import *

# Update __all__ with the public members from _direct_functions and clean up globals
for name in list(globals()):
    if name.startswith('_') and not (name.startswith('__') and name.endswith('__')):
        # Remove private attributes from globals
        del globals()[name]
    else:
        # Add public attributes to __all__
        __all__.append(name)
del name
