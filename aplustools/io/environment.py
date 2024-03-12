# environment.py
from typing import Union, Optional, Callable
import subprocess
import warnings
import platform
import tempfile
import inspect
import shutil
import sys
import os


try:
    import winreg
except ImportError:
    winreg = None  # winreg is not available on non-Windows platforms


def set_working_dir_to_main_script_location():
    """
    Set the current working directory to the location of the main script
    or executable. It considers whether the script is frozen using PyInstaller
    or is running as a normal Python script.
    """
    import __main__
    try:
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
        print(f"Working directory set to {main_dir}")

    except Exception as e:
        print(f"An error occurred while changing the working directory: {e}")
        raise  # Re-raise the error


def change_working_dir_to_script_location():
    if getattr(sys, 'frozen', False):
        # If the script is running as a bundled executable created by PyInstaller
        script_dir = os.path.dirname(sys.executable)
    else:
        # Get the path of the caller of this function
        frame = inspect.currentframe()
        caller_frame = frame.f_back
        caller_file = caller_frame.f_globals["__file__"]
        script_dir = os.path.dirname(os.path.abspath(caller_file))

    # Change the current working directory to the script directory
    os.chdir(script_dir)


def change_working_dir_to_temp_folder():
    os.chdir(tempfile.gettempdir())


def change_working_dir_to_userprofile_folder(folder: str):
    system = os.name
    if system == 'posix':
        home_dir = os.path.join(os.path.join(os.path.expanduser('~')), folder)  # os.path.expanduser("~/Desktop")
    elif system == 'nt':
        home_dir = os.path.join(os.path.join(os.environ['USERPROFILE']), folder)
    else:
        raise OSError(f"System {system} isn't supported by this function.")
    os.chdir(home_dir)


def inject_file_path(func: Callable):
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
    if not isinstance(paths, list):
        paths = [paths]
    for path in paths:
        if os.path.exists(path):
            if is_accessible(path):
                if os.path.isfile(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    if len(os.listdir(path)) == 0:
                        os.rmdir(path)
                    elif is_empty_directory(path):
                        shutil.rmtree(path)
                    else:
                        shutil.rmtree(path)
                else:
                    print("Bug, please report")
            else:
                print("Path not accessible")
        else:
            print("Path doesn't exist")


def contains_only_directories(path: str) -> bool:
    for item in os.listdir(path):
        if not os.path.isdir(os.path.join(path, item)):
            return False
    return True


def is_accessible(path: str):
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
        
    def mkdir(self, new_inner_dir: str):
        own_dir = self.path
        new_dir = os.path.join(self.path, new_inner_dir)
        self.path = new_dir
        self.create_directory()
        self.path = own_dir
        return new_dir
        
    def join(self, rel_inner_path: str):
        self.path = os.path.join(self.path, rel_inner_path)

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

    def rename(self, new_path: str):
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


def copy(org_loc: str, new_loc: str):
    shutil.copy(org_loc, new_loc)


def move(org_loc: str, new_loc: str):
    shutil.move(org_loc, new_loc)


def rename(org_nam: str, new_nam: str) -> bool:
    try:
        os.rename(org_nam, new_nam)
        print(f"{org_nam} renamed to {new_nam}.")
        return True
    except Exception as e:
        print(f"An error occurred while renaming: {e}")
        return False


def functionize(cls):
    warnings.warn("This is still experimental and may not be working as expected. A finished version should be available in release 0.1.5.", 
                  UserWarning, 
                  stacklevel=2)
    def wrapper(*args, **kwargs):
        # Creating an instance of the class
        instance = cls(*args, **kwargs)
        # Collecting the instance attributes (variables) and their values
        attrs = {attr: getattr(instance, attr) for attr in instance.__dict__}
        # Collecting methods and converting them to standalone functions
        methods = {
            name: (lambda method: lambda *args, **kwargs: method(instance, *args, **kwargs))(method)
            for name, method in cls.__dict__.items()
            if inspect.isfunction(method)
        }
        # Combining attributes and methods
        return {**attrs, **methods}
    return wrapper

def old_strict(cls):
    warnings.warn("This is still experimental and may not be working as expected. A finished version should be available in release 0.1.5.", 
                  UserWarning, 
                  stacklevel=2)
    # Create the new class with the same name
    class_name = cls.__name__
    def create_method(name):
        def method(self, *args, **kwargs):
            return getattr(self._inner_instance, name)(*args, **kwargs)
        return method
    def create_property(name):
        def getter(self):
            return getattr(self._inner_instance, name)
        return property(getter)
    outer_class_attrs = {
        '__init__': lambda self, *args, **kwargs: setattr(self, '_inner_instance', cls(*args, **kwargs))
    }
    # Add public methods and properties from the original class
    for attr_name in dir(cls):
        if not attr_name.startswith('_'):
            attr = getattr(cls, attr_name)
            if callable(attr):
                outer_class_attrs[attr_name] = create_method(attr_name)
            else:
                outer_class_attrs[attr_name] = create_property(attr_name)
    # Create the new class
    OuterClass = type(class_name, (object,), outer_class_attrs)
    def newgetattr(self, name):
        if callable(name):
            outer_class_attrs[attr_name] = create_method(attr_name)
        else:
            outer_class_attrs[attr_name] = create_property(attr_name)
    return OuterClass

def strict(cls):
    warnings.warn("This is still experimental and may not be working as expected. A finished version should be available in release 0.1.5.", 
                  UserWarning, 
                  stacklevel=2)
    # Create the new class with the same name
    class_name = cls.__name__
    def create_method(name):
        def method(self, *args, **kwargs):
            return getattr(self._inner_instance, name)(*args, **kwargs)
        return method
    def create_property(name):
        def getter(self):
            return getattr(self._inner_instance, name)
        return property(getter)
    def init_wrapper(self, *args, **kwargs):
        self.__dict__['_inner_instance'] = cls(*args, **kwargs)
    def setattr_wrapper(self, name, value):
        if name in self.__dict__ or name == '_inner_instance':
            object.__setattr__(self, name, value)
        else:
            setattr(self._inner_instance, name, value)
    def getattr_wrapper(self, name):
        if name in self.__dict__:
            return object.__getattribute__(self, name)
        return getattr(self._inner_instance, name)
    outer_class_attrs = {
        '__init__': init_wrapper, 
        '__setattr__': setattr_wrapper, 
        '__getattr__': getattr_wrapper
    }
    # Add public methods and properties from the original class
    for attr_name in dir(cls):
        if not attr_name.startswith('_'):
            attr = getattr(cls, attr_name)
            if callable(attr):
                outer_class_attrs[attr_name] = create_method(attr_name)
            else:
                outer_class_attrs[attr_name] = create_property(attr_name)
    # Create the new class
    OuterClass = type(class_name, (object,), outer_class_attrs)
    return OuterClass
"""
@strict
class Hello:
    def __init__(self):
        self.counter = 0
    def _hell(self):
        print(1)
    def hell(self):
        self._hell()
        self.counter += 1
    
@functionize
class Hello2:
    def __init__(self):
        pass
    def _hell(self):
        print("self")
    def hell(self):
        self._hell()
        
class Hello3:
    def __init__(self):
        pass
    def _hell(self):
        print(1)
    def hell(self):
        self._hell()

ins = Hello()
ins.hell()
print(ins.counter)
ins._hell()
"""



class System:
    def __init__(self):
        self.os = self.get_os()
        self.os_version = self.get_os_version()
        self.cpu_arch = self.get_cpu_arch()
        self.cpu_brand = self.get_cpu_brand()
        # GPU information retrieval can be complex and platform-dependent
        # self.gpu_info = self.get_gpu_info()
        self.theme = self.get_system_theme()

    def get_os(self):
        """Get the name of the operating system."""
        return platform.system()

    def get_os_version(self):
        """Get the version of the operating system."""
        return platform.version()
    
    def get_major_os_version(self):
        return platform.release()

    def get_cpu_arch(self):
        """Get the architecture of the CPU (e.g., x86_64, ARM)."""
        return platform.machine()

    def get_cpu_brand(self):
        """Get the brand and model of the CPU."""
        if self.os == 'Windows':
            return platform.processor()
        elif self.os == 'Linux' or self.os == 'Darwin':
            command = "cat /proc/cpuinfo | grep 'model name' | uniq"
            return subprocess.check_output(command, shell=True).decode().split(': ')[1].strip()
        return "Unknown"

    # GPU information retrieval is more complex and may require third-party libraries or specific system commands

    def get_system_theme(self):
        if self.os == 'Windows':
            return self.get_windows_theme()
        elif self.os == 'Darwin':
            return self.get_macos_theme()
        elif self.os == 'Linux':
            return self.get_linux_theme()
        return "Unknown"

    def get_windows_theme(self):
        if not winreg:
            return None

        key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize'
        value = 'AppsUseLightTheme'
        try:
            reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key)
            theme_value, _ = winreg.QueryValueEx(reg_key, value)
            winreg.CloseKey(reg_key)
            return 'Dark' if theme_value == 0 else 'Light'
        except Exception:
            return None

    def get_macos_theme(self):
        try:
            theme = subprocess.check_output("defaults read -g AppleInterfaceStyle", shell=True).decode().strip()
            return 'Dark' if theme == 'Dark' else 'Light'
        except subprocess.CalledProcessError:
            return 'Light'  # Default to Light since Dark mode is not set

    def get_linux_theme(self):
        # This method is very basic and might not work on all Linux distributions.
        # Linux theme detection can be very varied depending on the desktop environment.
        try:
            theme = subprocess.check_output("gsettings get org.gnome.desktop.interface gtk-theme", shell=True).decode().strip()
            return 'Dark' if 'dark' in theme.lower() else 'Light'
        except Exception:
            return None


def print_system_info():
    sys_info = System()
    print(f"Operating System: {sys_info.os}")
    print(f"OS Version: {sys_info.os_version}")
    print(f"CPU Architecture: {sys_info.cpu_arch}")
    print(f"CPU Brand: {sys_info.cpu_brand}")
    print(f"System Theme: {sys_info.theme}")


def local_test():
    try:
        print_system_info()
    except Exception as e:
        print(f"Exception occurred {e}.")
        return False
    else:
        print("Test completed successfully.")
        return True


if __name__ == "__main__":
    local_test()
