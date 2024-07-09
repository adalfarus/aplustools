# data __init__

from ..package import LazyModuleLoader as _LazyModuleLoader

# Lazy loading modules
database = _LazyModuleLoader('.data.database')
updaters = _LazyModuleLoader('.data.updaters')
imagetools = _LazyModuleLoader('.data.imagetools')
advanced_imagetools = _LazyModuleLoader('.data.advanced_imagetools')
compressor = _LazyModuleLoader('.data.compressor')
unien = _LazyModuleLoader('.data.unien')
faker_pro = _LazyModuleLoader('.data.faker_pro')
noise = _LazyModuleLoader('.data.noise')

# Define __all__ to limit what gets imported with 'from <package> import *'
__all__ = ['database', 'updaters', 'imagetools', 'advanced_imagetools', 'compressor', 'unien', 'faker_pro', 'noise']

# Dynamically add exports from _direct_functions
from ._direct_functions import *

# Update __all__ with the public members from _direct_functions and clean up globals
for name in list(globals()):
    if name.startswith('_') and not (name.startswith('__') and name.endswith('__')):
        # Remove private attributes from globals
        del globals()[name]
    else:
        # Add public attributes to __all__
        __all__.append(name)
del name
