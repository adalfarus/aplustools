import os
import sys
import __main__
import warnings

warnings.warn(
    "This module is deprecated and will be removed in version 0.1.4, please use environment.set_working_dir_to_main_script_location instead.",
    RuntimeWarning,
    stacklevel=2
    )

# Get the directory where the main script (or frozen exe) is located
if getattr(sys, 'frozen', False):
    # If the script is running as a bundled executable created by PyInstaller
    main_dir = os.path.dirname(sys.executable)
else:
    # If the script is running as a normal Python script
    if hasattr(__main__, '__file__'):
        main_dir = os.path.dirname(os.path.abspath(__main__.__file__))
    else:
        main_dir = os.path.dirname(os.getcwd())
        warnings.warn(
            "Could not set the current working directory to the location of the main script or executable.",
            RuntimeWarning,
            stacklevel=2
            )

# Change the current working directory to the main script directory
os.chdir(main_dir)
