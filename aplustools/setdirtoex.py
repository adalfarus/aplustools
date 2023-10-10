import os
import sys
import __main__

# Get the directory where the main script (or frozen exe) is located
if getattr(sys, 'frozen', False):
    # If the script is running as a bundled executable created by PyInstaller
    main_dir = os.path.dirname(sys.executable)
else:
    # If the script is running as a normal Python script
    main_dir = os.path.dirname(os.path.abspath(__main__.__file__))

# Change the current working directory to the main script directory
os.chdir(main_dir)
