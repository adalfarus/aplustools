# environment.py
from typing import (Callable as _Callable, cast as _cast, Any as _Any, Union as _Union, Optional as _Optional,
                    Literal as _Literal)
from types import FrameType as _FrameType
from pathlib import Path as _Path
import subprocess as _subprocess
import warnings as _warnings
import platform as _platform
import inspect as _inspect
import shutil as _shutil
import sys as _sys
import os as _os
import psutil as _psutil
import time as _time
import tempfile as _tempfile
from enum import Enum as _Enum
import ctypes as _ctypes
import locale as _locale
from contextlib import contextmanager as _contextmanager

from PIL import Image as _Image

from ..data import bytes_to_human_readable_binary_iec as _bytes_to_human_readable_binary_iec
from ..data import bits_to_human_readable as _bits_to_human_readable


try:
    import winreg as _winreg
except ImportError:
    _winreg = None
try:
    import win32clipboard as _win32clipboard
except ImportError:
    _win32clipboard = None
try:
    from windows_toasts import (Toast, WindowsToaster, InteractableWindowsToaster, ToastInputTextBox,
                                ToastActivatedEventArgs, ToastButton, ToastInputSelectionBox, ToastSelection)
except ImportError:
    Toast = WindowsToaster = InteractableWindowsToaster = ToastInputTextBox = None
    ToastActivatedEventArgs = ToastButton = ToastInputSelectionBox = ToastSelection = None


def inject_current_file_path(func: _Callable):
    def _wrapper(relative_path: str):
        frame = _inspect.currentframe().f_back
        module = _inspect.getmodule(frame)
        if module is not None:
            file_path = module.__file__
        else:
            file_path = __file__  # Fallback to the current script
        return func(relative_path, file_path)
    return _wrapper


def remove(paths: _Union[str, _Path, tuple[_Union[str, _Path]], list[_Union[str, _Path]]]):
    if isinstance(paths, (str, _Path)):
        paths = [str(paths)]
    else:
        paths = [str(p) for p in paths]

    for path in paths:
        if not _os.path.exists(path):
            raise ValueError(f"Path {path} doesn't exist.")
        if not is_accessible(path):
            raise ValueError(f"Path {path} not accessible")

        if _os.path.isfile(path):
            _os.remove(path)
        elif _os.path.isdir(path):
            if not _os.listdir(path):
                _os.rmdir(path)
            else:
                _shutil.rmtree(path)
        else:
            raise OSError(f"Bug, please report, path {path} is neither a file or a directory.")


def safe_remove(paths: _Union[str, _Path, tuple[_Union[str, _Path]], list[_Union[str, _Path]]]):
    try:
        remove(paths)
    except Exception as e:
        print(e)


def safe_write(filename, content):
    # Create a temporary file in the same directory as the target file
    dir_name, base_name = _os.path.split(filename)
    with _tempfile.NamedTemporaryFile('w', dir=dir_name, delete=False) as tmp_file:
        tmp_file_name = tmp_file.name
        tmp_file.write(content)

    # Move the temporary file to the target file location
    try:
        _os.replace(tmp_file_name, filename)
    except Exception as e:
        # If any error occurs, remove the temporary file
        _os.remove(tmp_file_name)
        raise e


class SafeFileWriter:
    def __init__(self, filename, mode='w'):
        self.filename = filename
        self.mode = mode
        self.temp_file = _tempfile.NamedTemporaryFile(mode=mode, dir=_os.path.dirname(filename), delete=False)
        self.temp_filename = self.temp_file.name

    def write(self, content):
        return self.temp_file.write(content)

    def writelines(self, lines):
        return self.temp_file.writelines(lines)

    def read(self, size=-1):
        return self.temp_file.read(size)

    def readline(self, size=-1):
        return self.temp_file.readline(size)

    def readlines(self, hint=-1):
        return self.temp_file.readlines(hint)

    def flush(self):
        return self.temp_file.flush()

    def close(self):
        if not self.temp_file.closed:
            self.temp_file.close()
            try:
                _os.replace(self.temp_filename, self.filename)
            except Exception as e:
                _os.remove(self.temp_filename)
                raise e

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            _os.remove(self.temp_filename)
        else:
            self.close()


def is_accessible(path: str):
    return _os.access(path, _os.R_OK)


def is_empty_directory(path: str) -> bool:
    if not _os.path.isdir(path):
        return False
    elif _os.path.isdir(path):
        try:
            for entry in _os.listdir(path):
                entry = _os.path.join(path, entry)
                if _os.path.isdir(entry):
                    if not is_empty_directory(entry):
                        return False
                else:
                    return False
        except PermissionError:
            print(f"Permission denied: {path}")
            return False
        return True
    else:
        raise FileNotFoundError(f"No such file or directory '{path}'")


def safe_rename(org_nam: str, new_nam: str) -> bool:
    try:
        _os.rename(org_nam, new_nam)
        print(f"{org_nam} renamed to {new_nam}.")
        return True
    except Exception as e:
        print(f"An error occurred while renaming: {e}")
        return False


def strict(mark_class_as_cover_or_cls: bool | type = True) -> _Callable:
    """The strict decorator is used to prevent hackers from easily getting passwords/private keys stored in instances"""
    mark_class_as_cover = True
    if isinstance(mark_class_as_cover_or_cls, bool):
        mark_class_as_cover = mark_class_as_cover_or_cls

    def _decorator(cls: type) -> type:
        class_name = cls.__name__ + ("Cover" if mark_class_as_cover else "")
        original_setattr = cls.__setattr__

        # Overridden __setattr__ for the original class
        def _new_setattr(self, name, value):
            original_setattr(self, name, value)
            # Update the cover class if attribute is public
            if not name.startswith('_') and hasattr(self, '_cover') and getattr(self._cover, name) != value:
                setattr(self._cover, name, value)

        # Replace __setattr__ in the original class
        cls.__setattr__ = _new_setattr

        # Define new __init__ for the cover class
        def _new_init(self, *args, **kwargs):
            # Create an instance of the original class
            original_instance = cls(*args, **kwargs)
            original_instance._cover = self  # Reference to the cover class

            # Bind public methods and attributes to the cover class instance
            for attr_name in dir(original_instance):
                if not attr_name.startswith('_'):  # or attr_name in ('__dict__', '__module__'):
                    attr_value = getattr(original_instance, attr_name)
                    if _inspect.isfunction(attr_value):
                        setattr(self, attr_name, attr_value.__get__(self, cls))
                    else:
                        setattr(self, attr_name, attr_value)

            def _custom_setattr(instance, name, value):
                object.__setattr__(instance, name, value)
                if not name.startswith('_') and getattr(original_instance, name) != value:
                    setattr(original_instance, name, value)

            self._dynamic_setattr = _custom_setattr

            # Remove reference to original instance
            # del original_instance

        def _setattr_overwrite(self, name, value):
            if hasattr(self, '_dynamic_setattr'):
                self._dynamic_setattr(self, name, value)
            else:
                object.__setattr__(self, name, value)

        # Create a new cover class with the new __init__ and other methods/attributes
        cover_class_attrs = {
            '__init__': _new_init,
            '__class__': cls,
            '__setattr__': _setattr_overwrite,
            '__repr__': cls.__repr__,
            '__str__': cls.__str__
        }
        for attr_name in dir(cls):
            if callable(getattr(cls, attr_name)) and not attr_name.startswith('_'):
                cover_class_attrs[attr_name] = getattr(cls, attr_name)

        CoverClass = type(class_name, (object,), cover_class_attrs)
        return CoverClass
    return _decorator if not isinstance(mark_class_as_cover_or_cls, type) else _decorator(mark_class_as_cover_or_cls)


def privatize(cls: type) -> type:
    """A class decorator that "protects" private attributes."""

    original_getattr = cls.__getattribute__
    original_setattr = cls.__setattr__

    def _get_caller_name() -> str:
        """Return the calling function's name."""
        return _cast(_FrameType, _cast(_FrameType, _inspect.currentframe()).f_back).f_code.co_name

    def _protected_getattr(self, name: str) -> _Any:
        if name.startswith('_') and _get_caller_name() not in dir(cls):
            raise AttributeError(f"Access to private attribute {name} is forbidden")
        return original_getattr(self, name)

    def _protected_setattr(self, name: str, value: _Any) -> None:
        if name.startswith('_') and _get_caller_name() not in dir(cls):
            raise AttributeError(f"Modification of private attribute {name} is forbidden")
        original_setattr(self, name, value)

    cls.__getattribute__ = _protected_getattr
    cls.__setattr__ = _protected_setattr

    return cls


def auto_repr(cls: type):
    """
    Decorator that automatically generates a __repr__ method for a class.
    """
    if cls.__repr__ is object.__repr__:
        def __repr__(self):
            attributes = ', '.join(f"{key}={getattr(self, key)}" for key in self.__dict__ if not key.startswith("_")
                                   or (key.startswith("__") and key.endswith("__")))
            return f"{cls.__name__}({attributes})"

        cls.__repr__ = __repr__
    return cls


def auto_repr_with_privates(cls: type):
    """
    Decorator that automatically generates a __repr__ method for a class, including all private attributes.
    """
    if cls.__repr__ is object.__repr__:
        def __repr__(self):
            attributes = ', '.join(f"{key}={getattr(self, key)}" for key in self.__dict__)
            return f"{cls.__name__}({attributes})"

        cls.__repr__ = __repr__
    return cls


def static_class(message: str | type = "This is a static class that can't be instantiated"):
    """
    Decorator that makes a class static, like a module, just for storing functions.
    """
    cls = None
    if not isinstance(message, str):
        cls = message
        message = "This is a static class that can't be instantiated"

    def _decorator(cls: type):
        if cls.__init__ is object.__init__:
            def __init__(self):
                raise NotImplementedError(message)

            cls.__init__ = __init__
        return cls
    if cls is None:
        return _decorator
    return _decorator(cls)


@_contextmanager
def suppress_warnings():
    """Context manager to suppress warnings."""
    _warnings.filterwarnings("ignore")
    try:
        yield
    finally:
        _warnings.filterwarnings("default")


class Window:
    @staticmethod
    def extract_icon_from_executable(exe_path: str, save_path: str) -> str:
        icon_size = _ctypes.windll.user32.GetSystemMetrics(11)  # SM_CXICON (icon width and height)

        # Load the icon from the executable
        large, small = _ctypes.c_void_p(), _ctypes.c_void_p()
        _ctypes.windll.shell32.ExtractIconExW(exe_path, 0, _ctypes.byref(large), _ctypes.byref(small), 1)

        hicon = large if large else small
        if not hicon:
            raise Exception("Could not load icon from executable")

        # Create a device context and bitmap
        hdc = _ctypes.windll.user32.GetDC(0)
        hbm = _ctypes.windll.gdi32.CreateCompatibleBitmap(hdc, icon_size, icon_size)
        hmemdc = _ctypes.windll.gdi32.CreateCompatibleDC(hdc)
        _ctypes.windll.gdi32.SelectObject(hmemdc, hbm)
        _ctypes.windll.user32.DrawIconEx(hmemdc, 0, 0, hicon, icon_size, icon_size, 0, 0, 3)

        # Prepare a bitmap info header
        class BITMAPINFOHEADER(_ctypes.Structure):
            _fields_ = [
                ('biSize', _ctypes.c_uint32),
                ('biWidth', _ctypes.c_int32),
                ('biHeight', _ctypes.c_int32),
                ('biPlanes', _ctypes.c_uint16),
                ('biBitCount', _ctypes.c_uint16),
                ('biCompression', _ctypes.c_uint32),
                ('biSizeImage', _ctypes.c_uint32),
                ('biXPelsPerMeter', _ctypes.c_int32),
                ('biYPelsPerMeter', _ctypes.c_int32),
                ('biClrUsed', _ctypes.c_uint32),
                ('biClrImportant', _ctypes.c_uint32)
            ]

        bmi = BITMAPINFOHEADER()
        bmi.biSize = _ctypes.sizeof(BITMAPINFOHEADER)
        bmi.biWidth = icon_size
        bmi.biHeight = icon_size
        bmi.biPlanes = 1
        bmi.biBitCount = 32  # 32 bits (RGBA)
        bmi.biCompression = 0  # BI_RGB
        bmi.biSizeImage = 0
        bmi.biXPelsPerMeter = 0
        bmi.biYPelsPerMeter = 0
        bmi.biClrUsed = 0
        bmi.biClrImportant = 0

        # Extract bitmap bits
        bitmap_bits = _ctypes.create_string_buffer(bmi.biWidth * bmi.biHeight * 4)
        result = _ctypes.windll.gdi32.GetDIBits(hmemdc, hbm, 0, icon_size, bitmap_bits, _ctypes.byref(bmi), 0)
        if result == 0:
            raise Exception("GetDIBits failed")

        # Create an image from the bitmap bits
        img = _Image.frombuffer('RGBA', (icon_size, icon_size), bitmap_bits, 'raw', 'BGRA', 0, 1)
        img = img.transpose(_Image.Transpose.FLIP_TOP_BOTTOM)  # Flip the image vertically
        img.save(save_path, 'PNG')

        # Cleanup
        _ctypes.windll.user32.ReleaseDC(0, hdc)
        _ctypes.windll.gdi32.DeleteObject(hbm)
        _ctypes.windll.gdi32.DeleteDC(hmemdc)
        _ctypes.windll.user32.DestroyIcon(hicon)

        return save_path

    @classmethod
    def get_windows_app_icon_path(cls):
        buffer = _ctypes.create_unicode_buffer(260)
        _ctypes.windll.kernel32.GetModuleFileNameW(None, buffer, 260)
        exe_path = buffer.value
        icon_path = _os.path.join(_os.path.dirname(exe_path), 'extracted_icon.png')
        return cls.extract_icon_from_executable(exe_path, icon_path)

    @classmethod
    def get_app_icon_path(cls):
        if _os.name == 'nt':  # Windows
            return cls.get_windows_app_icon_path()
        elif _sys.platform == 'darwin':  # macOS
            app_path = _os.path.abspath(_sys.argv[0])
            while not app_path.endswith('.app'):
                app_path = _os.path.dirname(app_path)
            icon_path = _os.path.join(app_path, 'Contents', 'Resources', 'AppIcon.icns')
            if _os.path.exists(icon_path):
                return icon_path
            else:
                raise FileNotFoundError(f"Icon file not found at {icon_path}")
        elif _sys.platform.startswith('linux'):  # Linux
            icon_path = '/path/to/your/icon.png'
            if _os.path.exists(icon_path):
                return icon_path
            else:
                raise FileNotFoundError(f"Icon file not found at {icon_path}")
        else:
            raise OSError(f"Unsupported operating system: {_os.name}")


class SystemTheme(_Enum):
    """Used to make system theme information standardized"""
    LIGHT = "Light"
    DARK = "Dark"
    UNKNOWN = "Unknown"


@static_class
class BasicSystemFunctions:
    """Encapsulates system information that isn't tied to a specific os."""
    @staticmethod
    def get_home_directory():
        """Get the user's home directory."""
        return _os.path.expanduser("~")

    @staticmethod
    def get_running_processes():
        """Get a list of running processes."""
        processes = []
        for proc in _psutil.process_iter(['pid', 'name']):
            try:
                processes.append(proc.as_dict(attrs=['pid', 'name']))
            except _psutil.NoSuchProcess:
                pass
        return processes

    @classmethod
    def get_disk_usage(cls, path: _Optional[str] = None):
        """Get disk usage statistics."""
        if path is None:
            path = cls.get_home_directory()
        usage = _shutil.disk_usage(path)
        return {
            'total': _bytes_to_human_readable_binary_iec(usage.total),
            'used': _bytes_to_human_readable_binary_iec(usage.used),
            'free': _bytes_to_human_readable_binary_iec(usage.free)
        }

    @staticmethod
    def get_memory_info():
        """Get memory usage statistics."""
        memory = _psutil.virtual_memory()
        return {
            'total': _bytes_to_human_readable_binary_iec(memory.total),
            'available': _bytes_to_human_readable_binary_iec(memory.available),
            'percent': f"{memory.percent}%",
            'used': _bytes_to_human_readable_binary_iec(memory.used),
            'free': _bytes_to_human_readable_binary_iec(memory.free)
        }

    @staticmethod
    def get_network_info():
        """Get network interface information."""
        addrs = _psutil.net_if_addrs()
        stats = _psutil.net_if_stats()
        network_info = {}
        for interface, addr_info in addrs.items():
            network_info[interface] = {
                'addresses': [{'address': addr.address, 'family': str(addr.family), 'netmask': addr.netmask,
                               'broadcast': addr.broadcast} for addr in addr_info],
                'isup': stats[interface].isup
            }
        return network_info

    @staticmethod
    def set_environment_variable(key: str, value: str):
        """Set an environment variable using os.environ."""
        _os.environ[key] = value

    @staticmethod
    def get_environment_variable(key: str):
        """Get an environment variable using os.environ."""
        return _os.environ.get(key)

    @staticmethod
    def get_uptime():
        """Get system uptime in minutes."""
        return (_time.time() - _psutil.boot_time()) / 60

    @staticmethod
    def measure_network_speed():
        """Measure network speed using speedtest-cli."""
        import speedtest as _speedtest
        st = _speedtest.Speedtest()
        download_speed = st.download()
        upload_speed = st.upload()
        results = st.results.dict()
        results['download'] = _bits_to_human_readable(download_speed)
        results['upload'] = _bits_to_human_readable(upload_speed)
        return results

    @staticmethod
    def set_working_dir_to_main_script_location():
        """
        Set the current working directory to the location of the main script
        or executable. It considers whether the script is frozen using PyInstaller
        or is running as a normal Python script.
        """
        import __main__
        try:
            # Get the directory where the main script (or frozen exe) is located
            if getattr(_sys, 'frozen', False):
                # If the script is running as a bundled executable created by PyInstaller
                main_dir = _os.path.dirname(_sys.executable)
            else:
                # If the script is running as a normal Python script
                if hasattr(__main__, '__file__'):
                    main_dir = _os.path.dirname(_os.path.abspath(__main__.__file__))
                else:
                    main_dir = _os.path.dirname(_os.getcwd())
                    _warnings.warn(
                        "Could not set the current working directory to the location of the main script or executable.",
                        RuntimeWarning,
                        stacklevel=2
                        )

            # Change the current working directory to the main script directory
            _os.chdir(main_dir)
            print(f"Working directory set to {main_dir}")

        except Exception as e:
            print(f"An error occurred while changing the working directory: {e}")
            raise  # Re-raise the error

    @staticmethod
    def change_working_dir_to_script_location():
        try:
            if getattr(_sys, 'frozen', False):
                # If the script is running as a bundled executable created by PyInstaller
                script_dir = _os.path.dirname(_sys.executable)
            else:
                # Get the path of the caller of this function
                frame = _inspect.currentframe()
                caller_frame = frame.f_back
                caller_file = caller_frame.f_globals["__file__"]
                script_dir = _os.path.dirname(_os.path.abspath(caller_file))

            # Change the current working directory to the script directory
            _os.chdir(script_dir)
            print(f"Working directory changed to {script_dir}")
        except Exception as e:
            print(f"An error occurred while changing the working directory: {e}")
            raise

    @staticmethod
    def change_working_dir_to_temp_folder():
        try:
            temp_dir = _tempfile.gettempdir()
            _os.chdir(temp_dir)
            print(f"Working directory changed to {temp_dir}")

        except Exception as e:
            print(f"An error occurred while changing the working directory: {e}")
            raise

    @staticmethod
    def change_working_dir_to_new_temp_folder():
        try:
            folder = _tempfile.mkdtemp()
            _os.chdir(folder)
            return folder
        except Exception as e:
            print(f"An error occurred while changing the working directory: {e}")
            raise

    @staticmethod
    def change_working_dir_to_userprofile_folder(folder: str):
        try:
            if _os.name == 'posix':
                home_dir = _os.path.join(_os.path.join(_os.path.expanduser('~')), folder)  # os.path.expanduser("~/Desktop")
            elif _os.name == 'nt':
                home_dir = _os.path.join(_os.path.join(_os.environ['USERPROFILE']), folder)
            else:
                raise OSError(f"System {_os.name} isn't supported by this function.")
            _os.chdir(home_dir)
            print(f"Working directory changed to {home_dir}")
        except Exception as e:
            print(f"An error occurred while changing the working directory: {e}")
            raise


class _BaseSystem:
    def __init__(self):
        self.os = _platform.system()
        self.os_version = _platform.version()
        self.major_os_version = _platform.release()

    def get_cpu_arch(self):
        return _platform.machine()

    def get_cpu_brand(self):
        """Get the brand and model of the CPU."""
        if self.os == 'Windows':
            return _platform.processor()
        elif self.os == 'Linux' or self.os == 'Darwin':
            command = "cat /proc/cpuinfo | grep 'model name' | uniq"
            return _subprocess.check_output(command, shell=True).decode().split(': ')[1].strip()
        return "Unknown"

    def get_gpu_info(self):
        """Gets the gpu info in a standardized format"""
        raise NotImplementedError("get_gpu_info is not implemented for this os")

    def get_system_theme(self) -> SystemTheme:
        """Gets tne current OS theme"""
        raise NotImplementedError("get_system_theme is not implemented for this os")

    def schedule_event(self, name: str, script_path: str, event_time: _Literal["startup", "login"]):
        """Schedules an event"""
        raise NotImplementedError("schedule_event is not implemented for this os")

    def send_notification(self, title: str, message: str,
                          input_fields: tuple[tuple[str, str, str], ...] = (("input_arg", "Input", "Hint"),),
                          selections: tuple[tuple[str, str, list[tuple], int], ...] = (("selection_arg", "Sel Display Name", ["selection_name", "Selection Display Name"], 0),),
                          buttons: tuple[tuple[str, _Callable], ...] = (("Accept", lambda: None), ("Cancel", lambda: None),),
                          click_callback: _Callable = lambda: None):
        """Sends a complex notification using a cross platform notification or a system specific one if it supports all
        the features"""
        from ..io.gui.balloon_tip import (NotificationManager)  # To prevent a circular import

        icon_path = Window.get_app_icon_path()
        NotificationManager.show_notification(
            icon_path,
            "Sample Notification",
            "This is a sample notification message.",
            inputs=input_fields,
            selections=selections,
            buttons=buttons,
            click_callback=lambda inputs, selections: print(f"Clicked with inputs: {inputs}, selections: {selections}"),
            auto_close_duration=7000  # Auto close after 7 seconds
        )

    def send_native_notification(self, title: str, message: str):
        """Sends a simple notification using the os's native notification system."""
        raise NotImplementedError("send_native_notification is not implemented for this os")

    def get_appdata_directory(self, app_dir: str, scope: _Literal["user", "global"] = "global"):
        """
        Gets you the right appdata directory for your scope.

        :param app_dir: The name of the folder you want your app to have.
        :param scope: If the data should be accessible to all users or just the current one.
        """
        raise NotImplementedError("get_appdata_directory is not implemented for this os")

    def get_battery_status(self):
        """Get battery status information."""
        raise NotImplementedError("get_battery_status is not implemented for this os")

    def get_clipboard(self):
        """Get the content of the clipboard."""
        raise NotImplementedError("get_clipboard is not implemented for this os")

    def set_clipboard(self, data: str):
        """Set the content of the clipboard."""
        raise NotImplementedError("set_clipboard is not implemented for this os")

    def get_system_language(self) -> tuple[str | str | None, str | str | None]:
        """Gets the current system language and encoding"""
        language_code, encoding = _locale.getdefaultlocale()
        return language_code, encoding


class _WindowsSystem(_BaseSystem):
    def get_cpu_brand(self):
        return _platform.processor()

    def get_gpu_info(self):
        command = "wmic path win32_VideoController get name"
        output = _subprocess.check_output(command.split(" ")).decode()
        return [line.strip() for line in output.split('\n') if line.strip()][1:]

    def get_system_theme(self) -> SystemTheme:
        key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize'
        light_theme_value = 'AppsUseLightTheme'
        system_theme_value = 'SystemUsesLightTheme'

        try:
            # Try to open the registry key
            reg_key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, key)
        except FileNotFoundError:
            # Key does not exist
            return SystemTheme.UNKNOWN
        except Exception as e:
            # Some other error occurred
            print(f"Exception occurred while opening registry key: {e}")
            return SystemTheme.UNKNOWN

        try:
            # Try to read the AppsUseLightTheme value
            theme_value, _ = _winreg.QueryValueEx(reg_key, light_theme_value)
            _winreg.CloseKey(reg_key)
            return SystemTheme.DARK if theme_value == 0 else SystemTheme.LIGHT
        except FileNotFoundError:
            # If the AppsUseLightTheme value does not exist, try the SystemUsesLightTheme value
            try:
                reg_key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, key)
                theme_value, _ = _winreg.QueryValueEx(reg_key, system_theme_value)
                _winreg.CloseKey(reg_key)
                return SystemTheme.DARK if theme_value == 0 else SystemTheme.LIGHT
            except FileNotFoundError:
                # Neither value exists, return UNKNOWN
                _winreg.CloseKey(reg_key)
                return SystemTheme.UNKNOWN
            except Exception as e:
                print(f"Exception occurred while reading SystemUsesLightTheme: {e}")
                _winreg.CloseKey(reg_key)
                return SystemTheme.UNKNOWN
        except Exception as e:
            print(f"Exception occurred while reading AppsUseLightTheme: {e}")
            _winreg.CloseKey(reg_key)
            return SystemTheme.UNKNOWN

    def schedule_event(self, name: str, script_path: str, event_time: _Literal["startup", "login"]):
        """Schedule an event to run at startup or login on Windows."""
        task_name, command = f"{name} (APT-{event_time.capitalize()} Task)", ""
        if event_time == "startup":
            command = f'schtasks /create /tn "{task_name}" /tr "{script_path}" /sc onstart /rl highest /f'
        elif event_time == "login":
            command = f'schtasks /create /tn "{task_name}" /tr "{script_path}" /sc onlogon /rl highest /f'
        _subprocess.run(command.split(" "), check=True)

    def send_notification(self, title: str, message: str,
                          input_fields: tuple[tuple[str, str, str], ...] = (("input_arg", "Input", "Hint"),),
                          selections: tuple[tuple[str, str, list[tuple], int], ...] = (("selection_arg", "Sel Display Name", ["selection_name", "Selection Display Name"], 0),),
                          buttons: tuple[tuple[str, _Callable], ...] = (("Accept", lambda: None), ("Cancel", lambda: None),),
                          click_callback: _Callable = lambda: None):
        if not (input_fields or selections or buttons):
            if WindowsToaster is not None and Toast is not None:
                toaster = WindowsToaster(title)
                new_toast = Toast()
                new_toast.text_fields = [message]
                new_toast.on_activated = click_callback
                toaster.show_toast(new_toast)
        else:
            if (InteractableWindowsToaster is not None
                    and Toast is not None
                    and ToastInputTextBox is not None
                    and ToastSelection is not None
                    and ToastButton is not None):
                interactable_toaster = InteractableWindowsToaster(title)
                new_toast = Toast([message])

                for input_field in input_fields:
                    arg_name, display_name, input_hint = input_field
                    new_toast.AddInput(ToastInputTextBox(arg_name, display_name, input_hint))

                for selection in selections:
                    selection_arg_name, selection_display_name, selection_options, default_selection_id = selection

                    selection_option_objects = []
                    for selection_option in selection_options:
                        selection_option_id, selection_option_display_name = selection_option
                        selection_option_objects.append(ToastSelection(selection_option_id, selection_option_display_name))

                    new_toast.AddInput(ToastInputSelectionBox(selection_arg_name, selection_display_name,
                                                              selection_option_objects,
                                                              selection_option_objects[default_selection_id]))

                response_lst = []
                for i, button in enumerate(buttons):
                    button_text, callback = button
                    response_lst.append(callback)
                    new_toast.AddAction(ToastButton(button_text, str(i)))

                new_toast.on_activated = lambda activated_event_args: (response_lst[int(activated_event_args.arguments)]()
                                                                       or click_callback(**activated_event_args.inputs))

                interactable_toaster.show_toast(new_toast)

    def send_native_notification(self, title: str, message: str):
        if WindowsToaster is not None and Toast is not None:
            toaster = WindowsToaster(title)
            new_toast = Toast()
            new_toast.text_fields = [message]
            toaster.show_toast(new_toast)
        else:
            print("You are not on a default windows machine")

    def get_battery_status(self):
        battery = _psutil.sensors_battery()
        if battery:
            return {'percent': battery.percent, 'secsleft': battery.secsleft, 'power_plugged': battery.power_plugged}

    def get_appdata_directory(self, app_dir: str, scope: _Literal["user", "global"] = "global"):
        if scope == "user":
            return _os.path.join(_os.environ.get("APPDATA"), app_dir)  # App data for the current user
        return _os.path.join(_os.environ.get("PROGRAMDATA"), app_dir)  # App data for all users

    def get_clipboard(self):
        _win32clipboard.OpenClipboard()
        try:
            data = _win32clipboard.GetClipboardData()
        except TypeError:
            data = None
        _win32clipboard.CloseClipboard()
        return data

    def set_clipboard(self, data: str):
        _win32clipboard.OpenClipboard()
        _win32clipboard.EmptyClipboard()
        _win32clipboard.SetClipboardText(data)
        _win32clipboard.CloseClipboard()

    def get_system_language(self) -> tuple[str | str | None, str | str | None]:
        language_code, encoding = super().get_system_language()
        if language_code:
            return language_code, encoding
        else:
            GetUserDefaultUILanguage = _ctypes.windll.kernel32.GetUserDefaultUILanguage
            lang_id = GetUserDefaultUILanguage()
            return _locale.windows_locale[lang_id], None


class _DarwinSystem(_BaseSystem):
    def get_cpu_brand(self):
        command = "sysctl -n machdep.cpu.brand_string"
        return _subprocess.check_output(command.split(" ")).decode().strip()

    def get_gpu_info(self):
        command = "system_profiler SPDisplaysDataType | grep 'Chipset Model'"
        output = _subprocess.check_output(command.split(" ")).decode()
        return [line.split(': ')[1].strip() for line in output.split('\n') if 'Chipset Model' in line]

    def get_system_theme(self) -> SystemTheme:
        command = "defaults read -g AppleInterfaceStyle"
        try:
            theme = _subprocess.check_output(command.split(" ")).decode().strip()
            return SystemTheme.DARK if theme.lower() == 'dark' else SystemTheme.LIGHT
        except _subprocess.CalledProcessError:
            return SystemTheme.LIGHT  # Default to Light since Dark mode is not set

    def schedule_event(self, name: str, script_path: str, event_time: _Literal["startup", "login"]):
        """Schedule an event to run at startup or login on macOS."""
        plist_content = f"""
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
            <key>Label</key>
            <string>com.example.{name.replace(' ', '_').lower()}</string>
            <key>ProgramArguments</key>
            <array>
                <string>{script_path}</string>
            </array>
            <key>RunAtLoad</key>
            <true/>
        </dict>
        </plist>
        """
        plist_path = f'~/Library/LaunchAgents/com.example.{name.replace(" ", "_").lower()}.plist'
        with open(_os.path.expanduser(plist_path), 'w') as f:
            f.write(plist_content)
        _subprocess.run(f'launchctl load {_os.path.expanduser(plist_path)}'.split(" "), check=True)

    def send_native_notification(self, title: str, message: str):
        script = f'display notification "{message}" with title "{title}"'
        _subprocess.run(["osascript", "-e", script])

    def get_battery_status(self):
        command = "pmset -g batt" if self.os == 'Darwin' else "upower -i /org/freedesktop/UPower/devices/battery_BAT0"
        try:
            output = _subprocess.check_output(command.split(" ")).decode().strip()
            return output
        except _subprocess.CalledProcessError:
            return "Battery status not available."

    def get_appdata_directory(self, app_dir: str, scope: _Literal["user", "global"] = "global"):
        if scope == "user":
            return _os.path.join(_os.path.expanduser("~"), "Library", "Application Support", app_dir)  # App data for the current user
        return _os.path.join("/Library/Application Support", app_dir)  # App data for all users

    def get_clipboard(self):
        command = "pbpaste"
        return _subprocess.check_output(command.split(" ")).decode().strip()

    def set_clipboard(self, data: str):
        command = f'echo "{data}" | pbcopy'
        _subprocess.run(command.split(" "), check=True)

    def get_system_language(self) -> tuple[str | str | None, str | str | None]:
        language_code, encoding = super().get_system_language()
        if language_code:
            return language_code, encoding
        else:
            result = _subprocess.run(['defaults', 'read', '-g', 'AppleLocale'], stdout=_subprocess.PIPE)
            return result.stdout.decode().strip(), None


class _LinuxSystem(_BaseSystem):
    def get_cpu_brand(self):
        try:
            with open('/proc/cpuinfo') as f:
                for line in f:
                    if 'model name' in line:
                        return line.split(':')[1].strip()
        except FileNotFoundError:
            return "Unknown"

    def get_gpu_info(self):
        try:
            # Run `lspci` and pipe its output to the next process
            p1 = _subprocess.Popen(["lspci"], stdout=_subprocess.PIPE, stderr=_subprocess.PIPE)
            # Run `grep VGA` to filter the output of `lspci`
            p2 = _subprocess.Popen(["grep", "VGA"], stdin=p1.stdout, stdout=_subprocess.PIPE, stderr=_subprocess.PIPE)
            p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits
            output, error = p2.communicate()

            if p2.returncode != 0:
                print(f"grep VGA returned non-zero exit status {p2.returncode}. Error: {error.decode().strip()}")
                return []

            output = output.decode()
            return [line.strip() for line in output.split('\n') if line.strip()]
        except FileNotFoundError as e:
            print("lspci or grep command not found. Please ensure both are installed.")
            return []
        except Exception as e:
            print(f"Unexpected exception occurred: {e}")
            if 'libEGL.so.1' in str(e):
                print("libEGL.so.1 is missing. Please install it with:")
                print("sudo apt-get install libegl1-mesa")  # For Debian-based systems
                print("sudo yum install mesa-libEGL")  # For Red Hat-based systems
            return []

    def get_system_theme(self) -> SystemTheme:
        # This might vary depending on the desktop environment (GNOME example)
        command = "gsettings get org.gnome.desktop.interface gtk-theme"
        try:
            theme = _subprocess.check_output(command.split(" ")).decode().strip().strip("'")
            return SystemTheme.DARK if "dark" in theme.lower() else SystemTheme.LIGHT
        except _subprocess.CalledProcessError:
            return SystemTheme.UNKNOWN

    def schedule_event(self, name: str, script_path: str, event_time: _Literal["startup", "login"]):
        """Schedule an event to run at startup or login on Linux."""
        if event_time == "startup":
            service_content = f"""
            [Unit]
            Description={name}
            After=network.target

            [Service]
            ExecStart={script_path}
            Restart=always
            User={_os.getlogin()}

            [Install]
            WantedBy=default.target
            """
            service_path = f"/etc/systemd/system/{name.replace(' ', '_').lower()}_startup.service"
            with open(service_path, 'w') as f:
                f.write(service_content)
            _os.system(f"systemctl enable {service_path}")
            _os.system(f"systemctl start {service_path}")
        elif event_time == "login":
            cron_command = f'@reboot {script_path}'
            _subprocess.run(f'(crontab -l; echo "{cron_command}") | crontab -'.split(" "), check=True)

    def send_native_notification(self, title: str, message: str):
        try:
            _subprocess.run(["notify-send", title, message])
        except FileNotFoundError:
            print("notify-send command not found.")
        except _subprocess.CalledProcessError as e:
            print(f"Exception occurred: {e}")

    def get_battery_status(self):
        command = "pmset -g batt" if self.os == 'Darwin' else "upower -i /org/freedesktop/UPower/devices/battery_BAT0"
        try:
            output = _subprocess.check_output(command.split(" ")).decode().strip()
            return output
        except _subprocess.CalledProcessError:
            return "Battery status not available."

    def get_appdata_directory(self, app_dir: str, scope: _Literal["user", "global"] = "global"):
        if scope == "user":
            return _os.path.join(_os.path.expanduser("~"), ".local", "share", app_dir)  # App data for the current user
        return _os.path.join("/usr/local/share", app_dir)  # App data for all users

    def get_clipboard(self):
        command = "xclip -selection clipboard -o"
        try:
            return _subprocess.check_output(command.split(" ")).decode().strip()
        except _subprocess.CalledProcessError:
            return ""

    def set_clipboard(self, data: str):
        command = f'echo "{data}" | xclip -selection clipboard'
        _subprocess.run(command.split(" "))

    def get_system_language(self) -> tuple[str | str | None, str | str | None]:
        language_code, encoding = super().get_system_language()
        if language_code:
            return language_code, encoding
        else:
            return _os.environ.get('LANG', 'en_US'), None


def get_system() -> _Union[_WindowsSystem, _DarwinSystem, _LinuxSystem, _BaseSystem]:
    """Gets the right system for your os."""
    os_name = _platform.system()
    if os_name == 'Windows':
        return _WindowsSystem()
    elif os_name == 'Darwin':
        return _DarwinSystem()
    elif os_name == 'Linux':
        return _LinuxSystem()
    else:
        _warnings.warn("Unsupported Operating System, returning _BaseSystem instance.", RuntimeWarning, 2)
        return _BaseSystem()


def safe_os_command_execution(command: str) -> str:
    return _subprocess.check_output(command.split(" ")).decode().strip()


def safe_exec(command: str) -> str:
    """
    Execute a command safely by using subprocess and splitting the input string.

    :param command: The command string to be executed.
    """
    try:
        # Split the command by spaces and run it using subprocess
        result = _subprocess.run(command.split(), check=True, capture_output=True, text=True)
        return result.stdout
    except _subprocess.CalledProcessError as e:
        return f"An error occurred: {e}"
