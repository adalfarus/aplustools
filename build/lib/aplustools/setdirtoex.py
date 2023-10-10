import os
import sys

# Get the directory where the script (or frozen exe) is located
if getattr(sys, 'frozen', False):
    # If the script is running as a bundled executable created by PyInstaller
    script_dir = os.path.dirname(sys.executable)
else:
    # If the script is running as a normal Python script
    script_dir = os.path.dirname(os.path.realpath(__file__))

# Change the current working directory to the script directory
os.chdir(script_dir)
