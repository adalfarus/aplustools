# environment.py
from typing import Union, Optional, Callable, Any, Type, cast, Literal, Tuple
from types import FrameType
import subprocess
import warnings
import platform
import inspect
import shutil
import sys
import os
import psutil
import time
import speedtest
import tempfile
from aplustools.data import bytes_to_human_readable_binary_iec


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
    os.chdir(System.system().get_tempdir())


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


def save_remove(paths: Union[str, list]):
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


def safe_rename(org_nam: str, new_nam: str) -> bool:
    try:
        os.rename(org_nam, new_nam)
        print(f"{org_nam} renamed to {new_nam}.")
        return True
    except Exception as e:
        print(f"An error occurred while renaming: {e}")
        return False


def strict(cls: Type[Any]):
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
                if inspect.isfunction(attr_value):
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


def privatize(cls: Type[Any]):
    """A class decorator that protects private attributes."""

    original_getattr = cls.__getattribute__
    original_setattr = cls.__setattr__

    def _get_caller_name() -> str:
        """Return the calling function's name."""
        return cast(FrameType, cast(FrameType, inspect.currentframe()).f_back).f_code.co_name

    def protected_getattr(self, name: str) -> Any:
        if name.startswith('_') and _get_caller_name() not in dir(cls):
            raise AttributeError(f"Access to private attribute {name} is forbidden")
        return original_getattr(self, name)

    def protected_setattr(self, name: str, value: Any) -> None:
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
            attributes = ', '.join(f"{key}={getattr(self, key)}" for key in self.__dict__)
            return f"{cls.__name__}({attributes})"

        cls.__repr__ = __repr__
    return cls


class _BaseSystem:
    def __init__(self):
        self.os = platform.system()
        self.os_version = platform.version()
        self.major_os_version = platform.release()
        self.cpu_arch = platform.machine()
        self.cpu_brand = None
        self.gpu_info = None
        self.theme = None

    def get_cpu_brand(self):
        """Get the brand and model of the CPU."""
        if self.os == 'Windows':
            return platform.processor()
        elif self.os == 'Linux' or self.os == 'Darwin':
            command = "cat /proc/cpuinfo | grep 'model name' | uniq"
            return subprocess.check_output(command, shell=True).decode().split(': ')[1].strip()
        return "Unknown"

    def schedule_event(self, name: str, script_path: str, event_time: Literal["startup", "login"]):
        raise NotImplementedError("schedule_event is not implemented")

    def send_notification(self, title: str, message: str,
                          input_fields: Tuple[Tuple[str, str, str], ...] = (("input_arg", "Input", "Hint"),),
                          selections: Tuple[Tuple[str, str, tuple, ..., int], ...] = (("selection_arg", "Sel Display Name", ("selection_name", "Selection Display Name"), 0),),
                          buttons: Tuple[Tuple[str, Callable], ...] = (("Accept", lambda: None), ("Cancel", lambda: None),),
                          click_callback: Callable = lambda: None):
        raise NotImplementedError("send_notification is not implemented")

    def get_gpu_info(self):
        raise NotImplementedError("get_gpu_info is not implemented")

    def get_tempdir(self):
        return tempfile.gettempdir()

    def get_home_directory(self):
        """Get the user's home directory."""
        return os.path.expanduser("~")

    def get_running_processes(self):
        """Get a list of running processes."""
        processes = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                processes.append(proc.as_dict(attrs=['pid', 'name']))
            except psutil.NoSuchProcess:
                pass
        return processes

    def get_disk_usage(self, path: Optional[str] = None):
        """Get disk usage statistics."""
        if path is None:
            path = self.get_home_directory()
        usage = shutil.disk_usage(path)
        return {
            'total': bytes_to_human_readable_binary_iec(usage.total),
            'used': bytes_to_human_readable_binary_iec(usage.used),
            'free': bytes_to_human_readable_binary_iec(usage.free)
        }

    def get_memory_info(self):
        """Get memory usage statistics."""
        memory = psutil.virtual_memory()
        return {
            'total': bytes_to_human_readable_binary_iec(memory.total),
            'available': bytes_to_human_readable_binary_iec(memory.available),
            'percent': f"{memory.percent}%",
            'used': bytes_to_human_readable_binary_iec(memory.used),
            'free': bytes_to_human_readable_binary_iec(memory.free)
        }

    def get_network_info(self):
        """Get network interface information."""
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
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
        os.environ[key] = value

    def get_environment_variable(self, key: str):
        """Get an environment variable."""
        return os.environ.get(key)

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
        """Get system uptime."""
        return time.time() - psutil.boot_time()

    def measure_network_speed(self):
        """Measure network speed using speedtest-cli."""
        st = speedtest.Speedtest()
        st.download()
        st.upload()
        return st.results.dict()


class _WindowsSystem(_BaseSystem):
    def __init__(self):
        super().__init__()
        self.cpu_brand = self.get_cpu_brand()
        self.gpu_info = self.get_gpu_info()
        self.theme = self.get_system_theme()

    def get_cpu_brand(self):
        return platform.processor()

    def get_gpu_info(self):
        command = "wmic path win32_VideoController get name"
        output = subprocess.check_output(command.split(" ")).decode()
        return [line.strip() for line in output.split('\n') if line.strip()][1:]

    def get_system_theme(self):
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

    def schedule_event(self, name: str, script_path: str, event_time: Literal["startup", "login"]):
        """Schedule an event to run at startup or login on Windows."""
        task_name, command = f"{name} (APT-{event_time.capitalize()} Task)", ""
        if event_time == "startup":
            command = f'schtasks /create /tn "{task_name}" /tr "{script_path}" /sc onstart /rl highest /f'
        elif event_time == "login":
            command = f'schtasks /create /tn "{task_name}" /tr "{script_path}" /sc onlogon /rl highest /f'
        subprocess.run(command.split(" "), check=True)

    def send_notification(self, title: str, message: str,
                          input_fields: Tuple[Tuple[str, str, str], ...] = (("input_arg", "Input", "Hint"),),
                          selections: Tuple[Tuple[str, str, tuple, ..., int], ...] = (("selection_arg", "Sel Display Name", ("selection_name", "Selection Display Name"), 0),),
                          buttons: Tuple[Tuple[str, Callable], ...] = (("Accept", lambda: None), ("Cancel", lambda: None),),
                          click_callback: Callable = lambda: None):
        if not input_fields:
            toaster = WindowsToaster(title)
            new_toast = Toast()
            new_toast.text_fields = [message]
            new_toast.on_activated = click_callback
            toaster.show_toast(new_toast)
        else:
            interactable_toaster = InteractableWindowsToaster(title)
            new_toast = Toast([message])

            for input_field in input_fields:
                arg_name, display_name, input_hint = input_field
                new_toast.AddInput(ToastInputTextBox(arg_name, display_name, input_hint))

            for selection in selections:
                selection_arg_name, selection_display_name, *selection_options, default_selection_id = selection

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

            new_toast.on_activated = lambda activated_event_args: (response_lst[activated_event_args.arguments]()
                                                                   or click_callback(**activated_event_args.inputs))

            interactable_toaster.show_toast(new_toast)

    def get_battery_status(self):
        battery = psutil.sensors_battery()
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
        return subprocess.check_output(command.split(" ")).decode().strip()

    def get_gpu_info(self):
        command = "system_profiler SPDisplaysDataType | grep 'Chipset Model'"
        output = subprocess.check_output(command.split(" ")).decode()
        return [line.split(': ')[1].strip() for line in output.split('\n') if 'Chipset Model' in line]

    def get_system_theme(self):
        command = "defaults read -g AppleInterfaceStyle"
        try:
            theme = subprocess.check_output(command.split(" ")).decode().strip()
            return 'dark' if theme.lower() == 'dark' else 'light'
        except subprocess.CalledProcessError:
            return 'light'  # Default to Light since Dark mode is not set

    def schedule_event(self, name: str, script_path: str, event_time: Literal["startup", "login"]):
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
        with open(os.path.expanduser(plist_path), 'w') as f:
            f.write(plist_content)
        subprocess.run(f'launchctl load {os.path.expanduser(plist_path)}'.split(" "), check=True)

    def send_notification(self, title: str, message: str,
                          _: Tuple[Tuple[str, str, str], ...] = (("input_arg", "Input", "Hint"),),
                          __: Tuple[Tuple[str, str, tuple, ..., int], ...] = (("selection_arg", "Sel Display Name", ("selection_name", "Selection Display Name"), 0),),
                          ___: Tuple[Tuple[str, Callable], ...] = (("Accept", lambda: None), ("Cancel", lambda: None),),
                          click_callback: Callable = lambda: None):
        script = f'display notification "{message}" with title "{title}"'
        subprocess.run(["osascript", "-e", script])

    def get_battery_status(self):
        command = "pmset -g batt" if self.os == 'Darwin' else "upower -i /org/freedesktop/UPower/devices/battery_BAT0"
        try:
            output = subprocess.check_output(command.split(" ")).decode().strip()
            return output
        except subprocess.CalledProcessError:
            return "Battery status not available."

    def get_clipboard(self):
        command = "pbpaste"
        return subprocess.check_output(command.split(" ")).decode().strip()

    def set_clipboard(self, data: str):
        command = f'echo "{data}" | pbcopy'
        subprocess.run(command.split(" "), check=True)


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
        command = "lspci | grep VGA"
        output = subprocess.check_output(command.split(" ")).decode()
        return output.strip()

    def get_system_theme(self):
        # This might vary depending on the desktop environment (GNOME example)
        command = "gsettings get org.gnome.desktop.interface gtk-theme"
        try:
            theme = subprocess.check_output(command.split(" ")).decode().strip().strip("'")
            return "dark" if "dark" in theme.lower() else "light"
        except subprocess.CalledProcessError:
            return "light"

    def schedule_event(self, name: str, script_path: str, event_time: Literal["startup", "login"]):
        """Schedule an event to run at startup or login on Linux."""
        if event_time == "startup":
            service_content = f"""
            [Unit]
            Description={name}
            After=network.target

            [Service]
            ExecStart={script_path}
            Restart=always
            User={os.getlogin()}

            [Install]
            WantedBy=default.target
            """
            service_path = f"/etc/systemd/system/{name.replace(' ', '_').lower()}_startup.service"
            with open(service_path, 'w') as f:
                f.write(service_content)
            os.system(f"systemctl enable {service_path}")
            os.system(f"systemctl start {service_path}")
        elif event_time == "login":
            cron_command = f'@reboot {script_path}'
            subprocess.run(f'(crontab -l; echo "{cron_command}") | crontab -'.split(" "), check=True)

    def send_notification(self, title: str, message: str,
                          _: Tuple[Tuple[str, str, str], ...] = (("input_arg", "Input", "Hint"),),
                          __: Tuple[Tuple[str, str, tuple, ..., int], ...] = (("selection_arg", "Sel Display Name", ("selection_name", "Selection Display Name"), 0),),
                          ___: Tuple[Tuple[str, Callable], ...] = (("Accept", lambda: None), ("Cancel", lambda: None),),
                          click_callback: Callable = lambda: None):
        subprocess.run(["notify-send", title, message])

    def get_battery_status(self):
        command = "pmset -g batt" if self.os == 'Darwin' else "upower -i /org/freedesktop/UPower/devices/battery_BAT0"
        try:
            output = subprocess.check_output(command.split(" ")).decode().strip()
            return output
        except subprocess.CalledProcessError:
            return "Battery status not available."

    def get_clipboard(self):
        command = "xclip -selection clipboard -o"
        return subprocess.check_output(command.split(" ")).decode().strip()

    def set_clipboard(self, data: str):
        command = f'echo "{data}" | xclip -selection clipboard'
        subprocess.run(command.split(" "))


class System:
    @staticmethod
    def system() -> Union[_WindowsSystem, _DarwinSystem, _LinuxSystem, _BaseSystem]:
        os_name = platform.system()
        if os_name == 'Windows':
            return _WindowsSystem()
        elif os_name == 'Darwin':
            return _DarwinSystem()
        elif os_name == 'Linux':
            return _LinuxSystem()
        else:
            warnings.warn("Unsupported Operating System, returning _BaseSystem instance.", RuntimeWarning, 2)
            return _BaseSystem()


def print_system_info():
    sys_info = System.system()
    print(f"Operating System: {sys_info.os}")
    print(f"OS Version: {sys_info.major_os_version}")
    print(f"CPU Architecture: {sys_info.cpu_arch}")
    print(f"CPU Brand: {sys_info.cpu_brand}")
    print(f"System Theme: {sys_info.theme}")


def basic_notification():
    system = System.system()
    system.send_notification("Zenra", "Hello, how are you?", (), (), ())


def test_disk_space_conversion():
    system = System.system()
    print(system.get_memory_info())


def safe_os_command_execution(command: str) -> str:
    return subprocess.check_output(command.split(" ")).decode().strip()


def local_test():
    try:
        print_system_info()
        basic_notification()
        test_disk_space_conversion()

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
