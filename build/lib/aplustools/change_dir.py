# change_dir.py
import os
import sys
import tempfile

def change_working_dir_to_script_location():
    # Get the directory where the script (or frozen exe) is located
    if getattr(sys, 'frozen', False):
        # If the script is running as a bundled executable created by PyInstaller
        script_dir = os.path.dirname(sys.executable)
    else:
        # If the script is running as a normal Python script
        script_dir = os.path.dirname(os.path.realpath(__file__))

    # Change the current working directory to the script directory
    os.chdir(script_dir)
    
def change_working_dir_to_temp_folder():
    os.chdir(tempfile.gettempdir())
    
def change_working_dir_to_userprof_folder(folder):
    system = os.name
    if system == 'posix':
        wDir = os.path.join(os.path.join(os.path.expanduser('~')), folder) # os.path.expanduser("~/Desktop")
    elif system == 'nt':
        wDir = os.path.join(os.path.join(os.environ['USERPROFILE']), folder)
    os.chdir(wDir)
    
def absolute_path(relative_path):
    ab = os.path.dirname(__file__)
    return os.path.join(ab, relative_path)
    