# environment.py
import os
import sys
import shutil
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
    
def remv(paths: list):
    if not isinstance(paths, list): paths = list(paths)
    for path in paths:
        if os.path.exists(path):
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                if len(os.listdir(path)) == 0:
                    os.rmdir(path)
                elif is_empty_directory(path):
                    shutil.rmtree(path)
                else:
                    shutil.rmtree(path)
                    
def contains_only_directories(path):
    for item in os.listdir(path):
        if not os.path.isdir(os.path.join(path, item)):
            return False
    return True

def is_empty_directory(path):
    with os.scandir(path) as entries:
        for entry in entries:
            if entry.is_file():
                return False
            elif entry.is_dir():
                if not is_empty_directory(entry.path):
                    return False
    return True

class Path:
    def __init__(self, path):
        self.path = os.path.abspath(path)

    def exists(self):
        """Check if the path exists."""
        return os.path.exists(self.path)

    def is_file(self):
        """Check if the path is a file."""
        return os.path.isfile(self.path)

    def is_directory(self):
        """Check if the path is a directory."""
        return os.path.isdir(self.path)

    def create_directory(self):
        """Create a directory at the path."""
        if not self.exists():
            os.makedirs(self.path)
            print(f"Directory {self.path} created.")
        else:
            print(f"Directory {self.path} already exists.")

    def list_files(self):
        """List all files in the directory."""
        if self.is_directory():
            with os.scandir(self.path) as entries:
                return [entry.name for entry in entries if entry.is_file()]
        else:
            print(f"{self.path} is not a directory.")
            return []

    def list_subdirectories(self):
        """List all subdirectories in the directory."""
        if self.is_directory():
            with os.scandir(self.path) as entries:
                return [entry.name for entry in entries if entry.is_dir()]
        else:
            print(f"{self.path} is not a directory.")
            return []

    def get_size(self):
        """Get the size of a file in bytes."""
        if self.is_file():
            return os.path.getsize(self.path)
        else:
            print(f"{self.path} is not a file.")
            return None

    def rename(self, new_path):
        """Rename the path to a new path."""
        os.rename(self.path, new_path)
        print(f"{self.path} renamed to {new_path}.")
        self.path = new_path

    def __str__(self):
        return self.path
    
    def __iter__(self):
        if self.is_directory():
            with os.scandir(self.path) as entries:
                for entry in entries:
                    yield entry.path
        else:
            print(f"{self.path} is not a directory.")
            yield self.path
            
    def __len__(self):
        return len(self.path.split("\\"))
