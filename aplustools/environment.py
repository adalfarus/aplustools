# environment.py
import os
import sys
import shutil
import tempfile
import __main__
from typing import Union, Optional
import inspect

def set_working_dir_to_main_script_location():
    """
    Set the current working directory to the location of the main script
    or executable. It considers whether the script is frozen using PyInstaller
    or is running as a normal Python script.
    """
    try:
        # Get the directory where the main script (or frozen exe) is located
        if getattr(sys, 'frozen', False):
            # If the script is running as a bundled executable created by PyInstaller
            main_dir = os.path.dirname(sys.executable)
        else:
            # If the script is running as a normal Python script
            main_dir = os.path.dirname(os.path.abspath(__main__.__file__))

        # Change the current working directory to the main script directory
        os.chdir(main_dir)
        print(f"Working directory set to {main_dir}")

    except Exception as e:
        print(f"An error occurred while changing the working directory: {e}")
        raise # Re-raise the error

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
    
def change_working_dir_to_userprof_folder(folder: str):
    system = os.name
    if system == 'posix':
        wDir = os.path.join(os.path.join(os.path.expanduser('~')), folder) # os.path.expanduser("~/Desktop")
    elif system == 'nt':
        wDir = os.path.join(os.path.join(os.environ['USERPROFILE']), folder)
    os.chdir(wDir)
    
def inject_file_path(func):
    def wrapper(relative_path: str):
        frame = inspect.currentframe().f_back
        module = inspect.getmodule(frame)
        if module is not None:
            file_path = module.__file__
        else:
            file_path = __file__  # Fallback to the current script
        return func(relative_path, file_path)
    return wrapper

@inject_file_path
def absolute_path(relative_path: str, file_path: str) -> str:
    base_dir = os.path.dirname(os.path.abspath(file_path))
    return os.path.join(base_dir, relative_path)
    
def remv(paths: Union[str, list]):
    if not isinstance(paths, list): paths = [paths]
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
                    
def contains_only_directories(path: str) -> bool:
    for item in os.listdir(path):
        if not os.path.isdir(os.path.join(path, item)):
            return False
    return True

def is_accessible(path):
    return os.access(path, os.R_OK)

def is_empty_directory(path: str) -> bool:
    if os.path.isfile(path):
        return False
    elif os.path.isdir(path):
        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    if entry.is_file():
                        return False
                    elif entry.is_dir():
                        if not is_empty_directory(entry.path):
                            return False
        except PermissionError:
            print(f"Permission denied: {path}")
            return False
        return True
    else:
        raise FileNotFoundError(f"No such file or directory '{path}'")

class Path:
    def __init__(self, path: str):
        self.path = os.path.abspath(path)

    def exists(self) -> bool:
        """Check if the path exists."""
        return os.path.exists(self.path)

    def is_file(self) -> bool:
        """Check if the path is a file."""
        return os.path.isfile(self.path)

    def is_directory(self) -> bool:
        """Check if the path is a directory."""
        return os.path.isdir(self.path)

    def create_directory(self):
        """Create a directory at the path."""
        try:
            if not self.exists():
                os.makedirs(self.path)
                print(f"Directory {self.path} created.")
            else:
                print(f"Directory {self.path} already exists.")
        except Exception as e:
            print(f"An error occurred: {e}")
            raise  # Reraise the exception after logging or printing the error message

    def list_files(self) -> list:
        """List all files in the directory."""
        if self.is_directory():
            with os.scandir(self.path) as entries:
                return [entry.name for entry in entries if entry.is_file()]
        else:
            print(f"{self.path} is not a directory.")
            return []

    def list_subdirectories(self) -> list:
        """List all subdirectories in the directory."""
        if self.is_directory():
            with os.scandir(self.path) as entries:
                return [entry.name for entry in entries if entry.is_dir()]
        else:
            print(f"{self.path} is not a directory.")
            return []

    def get_size(self) -> Optional[int]:
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

def copy(orloc: str, newloc: str):
    shutil.copy(orloc, newloc)

def move(orloc: str, newloc: str):
    shutil.move(orloc, newloc)
    
def rename(ornam: str, newnam: str) -> bool:
    try:
        os.rename(ornam, newnam)
        print(f"{ornam} renamed to {newnam}.")
        return True
    except Exception as e:
        print(f"An error occurred while renaming: {e}")
        return False
