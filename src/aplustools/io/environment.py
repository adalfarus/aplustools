# environment.py
from types import FrameType as _FrameType
from pathlib import Path as _Path
import subprocess as _subprocess
import warnings as _warnings
import platform as _platform
import inspect as _inspect
import shutil as _shutil
import typing as _typing
import sys as _sys
import os as _os
import psutil as _psutil
import time as _time
import tempfile as _tempfile
from enum import Enum as _Enum
import ctypes as _ctypes

from PIL import Image as _Image
import speedtest as _speedtest

from src.aplustools import bytes_to_human_readable_binary_iec as _bytes_to_human_readable_binary_iec
from src.aplustools import bits_to_human_readable as _bits_to_human_readable


try:
    import winreg
    from windows_toasts import (Toast, WindowsToaster, InteractableWindowsToaster, ToastInputTextBox,
                                ToastActivatedEventArgs, ToastButton, ToastInputSelectionBox, ToastSelection)
    import win32clipboard
except ImportError:
    winreg = win32clipboard = Toast = WindowsToaster = InteractableWindowsToaster = ToastInputTextBox = None
    ToastActivatedEventArgs = ToastButton = ToastInputSelectionBox = ToastSelection = None


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


def change_working_dir_to_temp_folder():
    try:
        temp_dir = _tempfile.gettempdir()
        _os.chdir(temp_dir)
        print(f"Working directory changed to {temp_dir}")

    except Exception as e:
        print(f"An error occurred while changing the working directory: {e}")
        raise


def change_working_dir_to_new_temp_folder():
    try:
        folder = _tempfile.mkdtemp()
        _os.chdir(folder)
        return folder
    except Exception as e:
        print(f"An error occurred while changing the working directory: {e}")
        raise


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


def inject_current_file_path(func: _typing.Callable):
    def wrapper(relative_path: str):
        frame = _inspect.currentframe().f_back
        module = _inspect.getmodule(frame)
        if module is not None:
            file_path = module.__file__
        else:
            file_path = __file__  # Fallback to the current script
        return func(relative_path, file_path)
    return wrapper


@inject_current_file_path
def absolute_path(relative_path: str, file_path: str) -> str:
    base_dir = _os.path.dirname(_os.path.abspath(file_path))
    return _os.path.join(base_dir, relative_path)


def remove(paths: _typing.Union[str, _Path, _typing.Tuple[_typing.Union[str, _Path]], _typing.List[_typing.Union[str, _Path]]]):
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


def safe_remove(paths: _typing.Union[str, _Path, _typing.Tuple[_typing.Union[str, _Path]],
                                     _typing.List[_typing.Union[str, _Path]]]):
    try:
        remove(paths)
    except Exception as e:
        print(e)


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


def strict(cls: _typing.Type[_typing.Any]):
    class_name = cls.__name__ + "Cover"
    original_setattr = cls.__setattr__

    # Overridden __setattr__ for the original class
    def new_setattr(self, name, value):
        original_setattr(self, name, value)
        # Update the cover class if attribute is public
        if not name.startswith('_') and hasattr(self, '_cover') and getattr(self._cover, name) != value:
            setattr(self._cover, name, value)

    # Replace __setattr__ in the original class
    cls.__setattr__ = new_setattr

    # Define new __init__ for the cover class
    def new_init(self, *args, **kwargs):
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

        def custom_setattr(instance, name, value):
            object.__setattr__(instance, name, value)
            if not name.startswith('_') and getattr(original_instance, name) != value:
                setattr(original_instance, name, value)

        self._dynamic_setattr = custom_setattr

        # Remove reference to original instance
        # del original_instance

    def setattr_overwrite(self, name, value):
        if hasattr(self, '_dynamic_setattr'):
            self._dynamic_setattr(self, name, value)
        else:
            object.__setattr__(self, name, value)

    # Create a new cover class with the new __init__ and other methods/attributes
    cover_class_attrs = {
        '__init__': new_init,
        '__class__': cls,
        '__setattr__': setattr_overwrite,
    }
    for attr_name in dir(cls):
        if callable(getattr(cls, attr_name)) and not attr_name.startswith('_'):
            cover_class_attrs[attr_name] = getattr(cls, attr_name)

    CoverClass = type(class_name, (object,), cover_class_attrs)
    return CoverClass


def privatize(cls: _typing.Type[_typing.Any]):
    """A class decorator that protects private attributes."""

    original_getattr = cls.__getattribute__
    original_setattr = cls.__setattr__

    def _get_caller_name() -> str:
        """Return the calling function's name."""
        return _typing.cast(_FrameType, _typing.cast(_FrameType, _inspect.currentframe()).f_back).f_code.co_name

    def protected_getattr(self, name: str) -> _typing.Any:
        if name.startswith('_') and _get_caller_name() not in dir(cls):
            raise AttributeError(f"Access to private attribute {name} is forbidden")
        return original_getattr(self, name)

    def protected_setattr(self, name: str, value: _typing.Any) -> None:
        if name.startswith('_') and _get_caller_name() not in dir(cls):
            raise AttributeError(f"Modification of private attribute {name} is forbidden")
        original_setattr(self, name, value)

    cls.__getattribute__ = protected_getattr
    cls.__setattr__ = protected_setattr

    return cls


def auto_repr(cls):
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


def auto_repr_with_privates(cls):
    """
    Decorator that automatically generates a __repr__ method for a class.
    """
    if cls.__repr__ is object.__repr__:
        def __repr__(self):
            attributes = ', '.join(f"{key}={getattr(self, key)}" for key in self.__dict__)
            return f"{cls.__name__}({attributes})"

        cls.__repr__ = __repr__
    return cls


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


class Theme(_Enum):
    LIGHT = "Light"
    DARK = "Dark"
    UNKNOWN = "Unknown"


class _BaseSystem:
    def __init__(self):
        self.os = _platform.system()
        self.os_version = _platform.version()
        self.major_os_version = _platform.release()
        self.cpu_arch = _platform.machine()
        self.cpu_brand = None
        self.gpu_info = None
        self.theme = None

    def get_cpu_brand(self):
        """Get the brand and model of the CPU."""
        if self.os == 'Windows':
            return _platform.processor()
        elif self.os == 'Linux' or self.os == 'Darwin':
            command = "cat /proc/cpuinfo | grep 'model name' | uniq"
            return _subprocess.check_output(command, shell=True).decode().split(': ')[1].strip()
        return "Unknown"

    def schedule_event(self, name: str, script_path: str, event_time: _typing.Literal["startup", "login"]):
        raise NotImplementedError("schedule_event is not implemented")

    def send_notification(self, title: str, message: str,
                          input_fields: _typing.Tuple[_typing.Tuple[str, str, str], ...] = (("input_arg", "Input", "Hint"),),
                          selections: _typing.Tuple[_typing.Tuple[str, str, _typing.List[tuple], int], ...] = (("selection_arg", "Sel Display Name", ["selection_name", "Selection Display Name"], 0)),
                          buttons: _typing.Tuple[_typing.Tuple[str, _typing.Callable], ...] = (("Accept", lambda: None), ("Cancel", lambda: None),),
                          click_callback: _typing.Callable = lambda: None):
        from src.aplustools.io.gui.balloon_tip import NotificationManager  # To prevent a circular import

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
        raise NotImplementedError("send_native_notification is not implemented")

    def get_gpu_info(self):
        raise NotImplementedError("get_gpu_info is not implemented")

    def get_home_directory(self):
        """Get the user's home directory."""
        return _os.path.expanduser("~")

    def get_running_processes(self):
        """Get a list of running processes."""
        processes = []
        for proc in _psutil.process_iter(['pid', 'name']):
            try:
                processes.append(proc.as_dict(attrs=['pid', 'name']))
            except _psutil.NoSuchProcess:
                pass
        return processes

    def get_disk_usage(self, path: _typing.Optional[str] = None):
        """Get disk usage statistics."""
        if path is None:
            path = self.get_home_directory()
        usage = _shutil.disk_usage(path)
        return {
            'total': _bytes_to_human_readable_binary_iec(usage.total),
            'used': _bytes_to_human_readable_binary_iec(usage.used),
            'free': _bytes_to_human_readable_binary_iec(usage.free)
        }

    def get_memory_info(self):
        """Get memory usage statistics."""
        memory = _psutil.virtual_memory()
        return {
            'total': _bytes_to_human_readable_binary_iec(memory.total),
            'available': _bytes_to_human_readable_binary_iec(memory.available),
            'percent': f"{memory.percent}%",
            'used': _bytes_to_human_readable_binary_iec(memory.used),
            'free': _bytes_to_human_readable_binary_iec(memory.free)
        }

    def get_network_info(self):
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

    def set_environment_variable(self, key: str, value: str):
        """Set an environment variable."""
        _os.environ[key] = value

    def get_environment_variable(self, key: str):
        """Get an environment variable."""
        return _os.environ.get(key)

    def get_battery_status(self):
        """Get battery status information."""
        raise NotImplementedError("get_battery_status is not implemented")

    def get_clipboard(self):
        """Get the content of the clipboard."""
        raise NotImplementedError("get_clipboard is not implemented")

    def set_clipboard(self, data: str):
        """Set the content of the clipboard."""
        raise NotImplementedError("set_clipboard is not implemented")

    def get_uptime(self):
        """Get system uptime in minutes."""
        return (_time.time() - _psutil.boot_time()) / 60

    def measure_network_speed(self):
        """Measure network speed using speedtest-cli."""
        st = _speedtest.Speedtest()
        download_speed = st.download()
        upload_speed = st.upload()
        results = st.results.dict()
        results['download'] = _bits_to_human_readable(download_speed)
        results['upload'] = _bits_to_human_readable(upload_speed)
        return results


class _WindowsSystem(_BaseSystem):
    def __init__(self):
        super().__init__()
        self.cpu_brand = self.get_cpu_brand()
        self.gpu_info = self.get_gpu_info()
        self.theme = self.get_system_theme()

    def get_cpu_brand(self):
        return _platform.processor()

    def get_gpu_info(self):
        command = "wmic path win32_VideoController get name"
        output = _subprocess.check_output(command.split(" ")).decode()
        return [line.strip() for line in output.split('\n') if line.strip()][1:]

    def get_system_theme(self) -> Theme:
        if not winreg:
            return Theme.UNKNOWN

        key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize'
        value = 'AppsUseLightTheme'
        try:
            reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key)
            theme_value, _ = winreg.QueryValueEx(reg_key, value)
            winreg.CloseKey(reg_key)
            return Theme.DARK if theme_value == 0 else Theme.LIGHT
        except Exception as e:
            print(f"Exception occurred: {e}")
            return Theme.UNKNOWN

    def schedule_event(self, name: str, script_path: str, event_time: _typing.Literal["startup", "login"]):
        """Schedule an event to run at startup or login on Windows."""
        task_name, command = f"{name} (APT-{event_time.capitalize()} Task)", ""
        if event_time == "startup":
            command = f'schtasks /create /tn "{task_name}" /tr "{script_path}" /sc onstart /rl highest /f'
        elif event_time == "login":
            command = f'schtasks /create /tn "{task_name}" /tr "{script_path}" /sc onlogon /rl highest /f'
        _subprocess.run(command.split(" "), check=True)

    def send_notification(self, title: str, message: str,
                          input_fields: _typing.Tuple[_typing.Tuple[str, str, str], ...] = (("input_arg", "Input", "Hint"),),
                          selections: _typing.Tuple[_typing.Tuple[str, str, _typing.List[tuple], int], ...] = (("selection_arg", "Sel Display Name", [("selection_name", "Selection Display Name")], 0)),
                          buttons: _typing.Tuple[_typing.Tuple[str, _typing.Callable], ...] = (("Accept", lambda: None), ("Cancel", lambda: None),),
                          click_callback: _typing.Callable = lambda: None):
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

    def get_clipboard(self):
        win32clipboard.OpenClipboard()
        try:
            data = win32clipboard.GetClipboardData()
        except TypeError:
            data = None
        win32clipboard.CloseClipboard()
        return data

    def set_clipboard(self, data: str):
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(data)
        win32clipboard.CloseClipboard()


class _DarwinSystem(_BaseSystem):
    def __init__(self):
        super().__init__()
        self.cpu_brand = self.get_cpu_brand()
        self.gpu_info = self.get_gpu_info()
        self.theme = self.get_system_theme()

    def get_cpu_brand(self):
        command = "sysctl -n machdep.cpu.brand_string"
        return _subprocess.check_output(command.split(" ")).decode().strip()

    def get_gpu_info(self):
        command = "system_profiler SPDisplaysDataType | grep 'Chipset Model'"
        output = _subprocess.check_output(command.split(" ")).decode()
        return [line.split(': ')[1].strip() for line in output.split('\n') if 'Chipset Model' in line]

    def get_system_theme(self) -> Theme:
        command = "defaults read -g AppleInterfaceStyle"
        try:
            theme = _subprocess.check_output(command.split(" ")).decode().strip()
            return Theme.DARK if theme.lower() == 'dark' else Theme.LIGHT
        except _subprocess.CalledProcessError:
            return Theme.LIGHT  # Default to Light since Dark mode is not set

    def schedule_event(self, name: str, script_path: str, event_time: _typing.Literal["startup", "login"]):
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

    def get_clipboard(self):
        command = "pbpaste"
        return _subprocess.check_output(command.split(" ")).decode().strip()

    def set_clipboard(self, data: str):
        command = f'echo "{data}" | pbcopy'
        _subprocess.run(command.split(" "), check=True)


class _LinuxSystem(_BaseSystem):
    def __init__(self):
        super().__init__()
        self.cpu_brand = self.get_cpu_brand()
        self.gpu_info = self.get_gpu_info()
        self.theme = self.get_system_theme()

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

    def get_system_theme(self) -> Theme:
        # This might vary depending on the desktop environment (GNOME example)
        command = "gsettings get org.gnome.desktop.interface gtk-theme"
        try:
            theme = _subprocess.check_output(command.split(" ")).decode().strip().strip("'")
            return Theme.DARK if "dark" in theme.lower() else Theme.LIGHT
        except _subprocess.CalledProcessError:
            return Theme.UNKNOWN

    def schedule_event(self, name: str, script_path: str, event_time: _typing.Literal["startup", "login"]):
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

    def get_clipboard(self):
        command = "xclip -selection clipboard -o"
        try:
            return _subprocess.check_output(command.split(" ")).decode().strip()
        except _subprocess.CalledProcessError:
            return ""

    def set_clipboard(self, data: str):
        command = f'echo "{data}" | xclip -selection clipboard'
        _subprocess.run(command.split(" "))


class System:
    @staticmethod
    def system() -> _typing.Union[_WindowsSystem, _DarwinSystem, _LinuxSystem, _BaseSystem]:
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


def print_system_info():
    sys_info = System.system()
    print(f"Operating System: {sys_info.os}")
    print(f"OS Version: {sys_info.major_os_version}")
    print(f"CPU Architecture: {sys_info.cpu_arch}")
    print(f"CPU Brand: {sys_info.cpu_brand}")
    print(f"System Theme: {sys_info.theme}")


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


def local_test():
    try:
        print_system_info()
        system = System.system()
        # _BaseSystem.send_notification(None, "Zenra", "Hello, how are you?", (), (), ())
        system.send_native_notification("Zenra,", "NOWAYY")
        print("System RAM", system.get_memory_info())
        print(f"Pc has been turned on since {int(System.system().get_uptime(),)} minutes")
        # print("Network test", System.system().measure_network_speed())

        @strict
        class MyCls:
            _attr = ""
        var = MyCls()._attr
    except AttributeError:
        print("Test completed successfully.")
        return True
    except Exception as e:
        print(f"Exception occurred {e}.")
        return False
    print("Strict decorator not working.")
    return False


if __name__ == "__main__":
    local_test()
    _time.sleep(100)
