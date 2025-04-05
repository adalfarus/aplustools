"""TBA"""
from mmap import ALLOCATIONGRANULARITY as _ALLOCATIONGRANULARITY
from threading import enumerate as _threading_enumerate
from multiprocessing import current_process as _multiprocessing_process
from contextlib import contextmanager as _contextmanager
from pathlib import Path as _Path
import subprocess as _subprocess
from enum import Enum as _Enum
import tempfile as _tempfile
import warnings as _warnings
import platform as _platform
import inspect as _inspect
import locale as _locale
import ctypes as _ctypes
import shutil as _shutil
import time as _time
import sys as _sys
import os as _os

try:
    from ctypes.wintypes import MAX_PATH
except ValueError:  # Raises on linux
    MAX_PATH = _os.pathconf('/', 'PC_PATH_MAX')

from ..package import optional_import as _optional_import, enforce_hard_deps as _enforce_hard_deps
from ..data import (SingletonMeta as _SingletonMeta)
from ..data.bintools import (bits_to_human_readable as _bits_to_human_readable,
                             bytes_to_human_readable_binary_iec as _bytes_to_human_readable_binary_iec)

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

_winreg = _optional_import("winreg")
_win32clipboard = _optional_import("win32clipboard")
_Toast = _optional_import("windows_toasts.Toast")
_WindowsToaster = _optional_import("windows_toasts.WindowsToaster")
_InteractableWindowsToaster = _optional_import("windows_toasts.InteractableWindowsToaster")
_ToastInputTextBox = _optional_import("windows_toasts.ToastInputTextBox")
_ToastActivatedEventArgs = _optional_import("windows_toasts.ToastActivatedEventArgs")
_ToastButton = _optional_import("windows_toasts.ToastButton")
_ToastInputSelectionBox = _optional_import("windows_toasts.ToastInputSelectionBox")
_ToastSelection = _optional_import("windows_toasts.ToastSelection")
_msvcrt = _optional_import("msvcrt")
_fcntl = _optional_import("fcntl")
_pywintypes = _optional_import("pywintypes")
_win32file = _optional_import("win32file")
_win32con = _optional_import("win32con")
_winerror = _optional_import("winerror")
_psutil = _optional_import("psutil")

__deps__: list[str] = ["speedtest-cli>=2.1.3", "windows-toasts>=1.1.1; os_name == 'nt'", "PySide6>=6.7.0",
            "psutil>=6.0.0", "pywin32>=306"]
__hard_deps__: list[str] = []
_enforce_hard_deps(__hard_deps__, __name__)

_overlapped = None
if _win32file is not None:
    _overlapped = _win32file.OVERLAPPED()


class SystemTheme(_Enum):
    """Used to make system theme information standardized"""
    LIGHT = 2
    DARK = 1
    UNKNOWN = 0


class _BaseSystem(metaclass=_SingletonMeta):
    """
    A base class to represent a system's general functionalities, such as CPU and GPU information,
    OS version, system theme, and event scheduling. This class serves as a framework for handling
    platform-specific details.
    """

    def __init__(self) -> None:
        """
        Initialize the _BaseSystem with basic OS information, including the OS name, version,
        and major version number.
        """
        self.os: str = _platform.system()
        self.os_version: str = _platform.version()
        self.major_os_version: str = _platform.release()

    def get_cpu_arch(self) -> str:
        """
        Get the architecture of the CPU.

        :return: A string representing the CPU architecture (e.g., 'x86_64', 'arm64').
        """
        return _platform.machine()

    def get_cpu_brand(self) -> str:
        """
        Get the brand and model of the CPU.

        :return: A string representing the CPU brand and model. If not supported by the OS, returns 'Unknown'.
        """
        if self.os == "Windows":
            return _platform.processor()
        elif self.os == "Linux" or self.os == "Darwin":
            command = "cat /proc/cpuinfo | grep 'model name' | uniq"
            return _subprocess.check_output(command, shell=True).decode().split(": ")[1].strip()
        return "Unknown"

    def get_gpu_info(self) -> str:
        """
        Get the GPU information in a standardized format.

        :raises NotImplementedError: This method is not implemented for this operating system.
        """
        raise NotImplementedError("get_gpu_info is not implemented for this os")

    def get_system_theme(self) -> SystemTheme:
        """
        Get the current OS theme (e.g., light or dark mode).

        :raises NotImplementedError: This method is not implemented for this operating system.
        """
        raise NotImplementedError("get_system_theme is not implemented for this os")

    def schedule_event(self, name: str, script_path: str, event_time: _ty.Literal["startup", "login"]) -> None:
        """
        Schedule an event to run at a specified time, such as at startup or login.

        :param name: The name of the event to schedule.
        :param script_path: The path to the script to be executed at the scheduled time.
        :param event_time: Specifies when the event should be triggered. Can be 'startup' or 'login'.

        :raises NotImplementedError: This method is not implemented for this operating system.
        """
        raise NotImplementedError("schedule_event is not implemented for this os")

    def send_notification(self, title: str, message: str,
                          input_fields: tuple[tuple[str, str, str], ...] = (("input_arg", "Input", "Hint"),),
                          selections: tuple[tuple[str, str, list[tuple], int], ...] = (("selection_arg", "Sel Display Name", ["selection_name", "Selection Display Name"], 0),),
                          buttons: tuple[tuple[str, _a.Callable], ...] = (("Accept", lambda: None), ("Cancel", lambda: None),),
                          click_callback: _a.Callable = lambda: None) -> None:
        """
        Sends a cross-platform complex notification, or a system-specific notification with support for input fields,
        selections, buttons, and callbacks.

        :param title: The title of the notification.
        :param message: The main message to display in the notification.
        :param input_fields: A tuple of input field configurations. Each field is a tuple containing
                             the argument name, display name, and a hint.
        :param selections: A tuple of selection field configurations. Each field is a tuple containing
                           the argument name, display name, list of selections, and default selection index.
        :param buttons: A tuple of button configurations. Each button is a tuple containing
                        the button text and a callback function.
        :param click_callback: A callback function triggered when the notification is clicked.
        """
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

    def send_native_notification(self, title: str, message: str) -> None:
        """
        Sends a simple notification using the operating system's native notification system.

        :param title: The title of the notification.
        :param message: The message content of the notification.

        :raises NotImplementedError: This method is not implemented for this operating system.
        """
        raise NotImplementedError("send_native_notification is not implemented for this os")

    def get_appdata_directory(self, app_dir: str, scope: _ty.Literal["user", "global"] = "global") -> str:
        """
        Get the appropriate appdata directory based on the specified scope (user-specific or global).

        :param app_dir: The name of the folder designated for your app's data.
        :param scope: Specifies whether the data is accessible by all users ('global') or only the current user ('user').

        :raises NotImplementedError: This method is not implemented for this operating system.
        """
        raise NotImplementedError("get_appdata_directory is not implemented for this os")

    def get_battery_status(self) -> dict[str, float | int | bool]:
        """
        Get the system's battery status information.

        :raises NotImplementedError: This method is not implemented for this operating system.
        """
        raise NotImplementedError("get_battery_status is not implemented for this os")

    def get_clipboard(self) -> str | None:
        """
        Get the current content of the system's clipboard.

        :raises NotImplementedError: This method is not implemented for this operating system.
        """
        raise NotImplementedError("get_clipboard is not implemented for this os")

    def set_clipboard(self, data: str) -> None:
        """
        Set the system clipboard with the specified data.

        :param data: The string data to set in the clipboard.

        :raises NotImplementedError: This method is not implemented for this operating system.
        """
        raise NotImplementedError("set_clipboard is not implemented for this os")

    def get_system_language(self) -> tuple[str | str | None, str | str | None]:
        """
        Get the current system language and encoding settings.

        :return: A tuple containing the language code and the encoding format.
        """
        language_code, encoding = _locale.getdefaultlocale()
        return language_code, encoding

    def hide_file(self, filepath: str | _Path) -> bool:
        """
        Hides a file by renaming it or setting the hidden attribute, depending on the operating system.

        For Unix-like systems (Linux, macOS, FreeBSD):
        - If the file is not already hidden, it renames the file by adding a dot (.) at the beginning
          of the filename. Files with a dot prefix are considered hidden on these systems.

        For Windows:
        - It uses the `ctypes` library to call the Windows API (`SetFileAttributesW`) to set the hidden
          attribute on the file without relying on subprocess calls. The hidden attribute (`0x02`) is applied,
          making the file invisible in the Windows File Explorer.

        Parameters:
        - filepath (str | _Path): The full path of the file to be hidden.

        Returns:
        - bool: Returns `True` if the file was successfully hidden, `False` otherwise.

        Notes:
        - On Unix-like systems, the method checks if the file is already hidden (i.e., starts with a dot)
          and does nothing if it is.
        - On Windows, an exception is caught and logged if the API call fails.
        - If the operating system is unsupported, the method prints an error message and returns `False`.

        Supported OS:
        - Linux, macOS (Darwin), FreeBSD for renaming files to hide them.
        - Windows for setting the hidden attribute via the Windows API.

        Example:
        >>> self.hide_file('/path/to/file.txt')  # On Linux/Mac/FreeBSD, renames to .file.txt
        >>> self.hide_file('C:\\path\\to\\file.txt')  # On Windows, sets the hidden attribute.
        """
        if self.os in {"Linux", "Darwin", "FreeBSD"}:
            # Rename the file by adding a dot at the beginning (if not already hidden)
            base_name = _os.path.basename(filepath)
            dir_name = _os.path.dirname(filepath)

            if not base_name.startswith("."):
                hidden_filepath = _os.path.join(dir_name, "." + base_name)
                _os.rename(filepath, hidden_filepath)
                return True
            return False
        elif self.os == "Windows":
            # Use ctypes to set the hidden attribute
            FILE_ATTRIBUTE_HIDDEN = 0x02
            try:
                # Get a handle to the file
                result = _ctypes.windll.kernel32.SetFileAttributesW(filepath, FILE_ATTRIBUTE_HIDDEN)
                if result:
                    return True
                return False
            except Exception as e:
                print(f"Error hiding the file on Windows: {e}")
                return False
        print(f"Unsupported OS: {self.os}")
        return False

    def get_shared_folder(self) -> str:
        """
        Determine and return the appropriate shared directory path for the operating system.

        This method selects a directory that is accessible to all users and suitable for shared files, such as lock files.

        - On **Windows**, it uses `C:\\Users\\Public`, which is a publicly accessible directory.
        - On **Linux**, **macOS** (Darwin), and **FreeBSD**:
          - It first attempts to use `/var/lock`, the standard location for lock files.
          - If `/var/lock` is not writable (due to permission issues), it falls back to `/srv/shared-locks`.
          - If `/srv/shared-locks` does not exist, it will be automatically created with permissions set to allow read and write access for all users (`777`).

        :return: The path to the shared directory.
        :raises OSError: If the operating system is unsupported or the directories cannot be created/accessed.
        """
        if self.os == "Windows":
            shared_dir = r"C:\Users\Public"
        elif self.os in {"Linux", "Darwin", "FreeBSD"}:
            # Try to use /var/lock, which is the appropriate place for lock files
            shared_dir = "/var/lock"

            # If /var/lock is not writable (permission denied), fallback to a custom directory
            if not _os.access(shared_dir, _os.W_OK):
                shared_dir = "/srv/shared-locks"  # Replace with a valid shared directory
                if not _os.path.exists(shared_dir):
                    _os.makedirs(shared_dir, mode=0o777, exist_ok=True)  # Create directory if it doesn't exist
        else:
            raise OSError(f"Unsupported operating system: {self.os}")
        return shared_dir

    def create_shared_file(self, filename: str) -> str:
        """
        Create a lock file that is accessible to all users on the system and will not be automatically deleted.

        The location depends on the operating system:
        - On Windows: C:\\Users\\Public
        - On Linux/macOS: /var/lock if accessible, or a custom shared directory like /srv/shared-locks

        :param filename: The name of the lock file to create.
        :return: The path to the created lock file.
        :raises PermissionError: If the file cannot be created due to permission issues.
        """
        shared_dir = self.get_shared_folder()

        # Ensure the shared directory exists
        if not _os.path.exists(shared_dir):
            raise OSError(f"Shared directory does not exist: {shared_dir}")

        # Construct the full file path
        file_path = _os.path.join(shared_dir, filename)
        if _os.path.exists(file_path):
            raise OSError(f"The filepath {file_path} already exists.")

        try:
            open(file_path, 'w').close()

            # On Windows, public files are generally shared by default
            if self.os in {"Linux", "Darwin", "FreeBSD"}:
                _os.chmod(file_path, 0o666)  # Set permissions to Read and write for everyone
            return file_path
        except PermissionError as e:
            raise PermissionError(f"Failed to create lock file at {file_path}. Permission denied.") from e
        except Exception as e:
            raise OSError(f"An error occurred while creating the lock file: {str(e)}") from e

    def is_os_drive(self, volume: str) -> bool:
        """
        Check if the given volume is the OS volume, depending on the operating system.

        :param volume: The volume to check (e.g., "C:\\" on Windows or "/" on Linux/macOS).
        :return: True if the volume is the OS volume, False otherwise.
        """
        if self.os == "Windows":
            system_root = _os.environ.get("SystemRoot", "")
            return system_root.startswith(volume)

        elif self.os in {"Linux", "Darwin", "FreeBSD"}:
            return _os.path.ismount("/") and _os.path.samefile("/", volume)

        else:
            raise OSError(f"Unsupported operating system: {self.os}")

    def is_valid_volume(self, volume: str) -> bool:
        """
        Determines whether the provided volume identifier is valid and currently exists
        on the system, depending on the operating system (Windows, Linux, macOS, FreeBSD).

        - **Windows**: The method verifies if the volume is a valid drive letter (e.g., "C:\\", "D:\\").
        - **Linux/macOS/FreeBSD**: The method checks if the volume is currently mounted and accessible
          by looking into the appropriate system files (`/proc/mounts` for Linux and macOS,
          `/etc/fstab` for FreeBSD).

        Args:
            volume (str): The volume identifier to check (e.g., "C:\\", "/mnt/mydrive").

        Returns:
            bool: True if the volume identifier is valid and currently mounted, otherwise False.

        Raises:
            NotImplementedError: If the method is called on an unsupported operating system.
        """
        if self.os == "Windows":
            volume = volume.lower().strip(":/\\")
            volume_path = f"{volume.upper()}:\\"

            if (False in (ord(letter) in range(97, 123) for letter in volume)
                    or not _os.path.exists(volume_path)):
                return False
            return True
        elif self.os in {"Linux", "Darwin", "FreeBSD"}:
            # Check if the volume is currently mounted (dynamic check)
            mount_file = "/proc/mounts" if self.os != "FreeBSD" else "/etc/fstab"

            # Normalize the volume path (e.g., /mnt/volume or /dev/sda1)
            volume_path = _os.path.normpath(volume)

            try:
                with open(mount_file, "r") as f:
                    mounted_volumes = [line.split()[1] for line in f.readlines()]
                    if volume in mounted_volumes and _os.path.exists(volume_path):
                        return True
            except FileNotFoundError:
                pass
            return False
        else:
            raise NotImplementedError(f"Unsupported system: {self.os}")

    def is_path_on_volume(self, path: str, volume: str) -> bool:
        """
        Checks whether the given path is located on the specified volume.

        - **Windows**: The method verifies if the path starts with the given volume drive letter
          (e.g., "C:\\", "D:\\").
        - **Linux/macOS/FreeBSD**: The method checks if the path is on a mounted filesystem and
          whether the specified volume is part of the path's mount point. The check is based on
          the currently mounted filesystems (from `/proc/mounts` on Linux/macOS or `/etc/fstab`
          on FreeBSD).

        Args:
            path (str): The full file path to check (e.g., "/mnt/mydrive/docs/file.txt").
            volume (str): The volume identifier to verify (e.g., "/mnt/mydrive").

        Returns:
            bool: True if the path belongs to the specified volume, otherwise False.

        Raises:
            NotImplementedError: If the method is called on an unsupported operating system.
        """
        if self.os == "Windows":
            # For Windows, check if the path is on the volume (e.g., C:\ or D:\)
            volume = volume.lower().strip(":/\\")
            volume_path = f"{volume.upper()}:\\"

            # Check if the path starts with the volume path
            return path.lower().startswith(volume_path.lower())
        elif self.os in {"Linux", "Darwin", "FreeBSD"}:
            # For Unix-like systems, check if the path is on a mounted filesystem
            with open("/proc/mounts" if self.os != "FreeBSD" else "/etc/fstab", "r") as mounts_file:
                mounts = [line.split()[1] for line in mounts_file.readlines()]

            # Find the longest mount point that is a prefix of the given path
            valid_mounts = [mount for mount in mounts if path.startswith(mount)]

            if valid_mounts:
                # Check if any of the valid mount points matches the volume
                return any(volume in valid_mount for valid_mount in valid_mounts)
            return False
        else:
            raise NotImplementedError(f"Unsupported system: {self.os}")

    def lock_file(self, filepath_or_fd: str | int, byte_range: range | None = None, blocking: bool = True, *,
                  open_flags: int = _os.O_RDWR | _os.O_CREAT, shared_lock: bool = False) -> None | int:
        """
        Attempt to lock the file for exclusive or shared access, with optional byte-range locking.

        Args:
            filepath_or_fd (str | int): The path to the file to lock or an existing file descriptor.
            byte_range (range): Optional range of bytes to lock.
            blocking (bool): Whether the lock should block or return immediately if unavailable.
            open_flags (int): File open flags.
            shared_lock (bool): Use a shared lock if True, exclusive lock if False.

        Returns:
            int: The file descriptor if the lock is successfully acquired.
            None: If the file is already locked (in non-blocking mode) or an error occurs.

        Raises:
            NotImplementedError: If the operating system is not supported.
        """
        fd = filepath_or_fd
        if isinstance(filepath_or_fd, str):
            fd: int = _os.open(filepath_or_fd, open_flags)

        if self.os == "Windows":
            if _win32con is None or _win32file is None:
                raise RuntimeError("Required dependency is not installed")
            try:
                old_pos = _os.lseek(fd, 0, _os.SEEK_CUR)
                lock_length = -0x10000
                seek_set = lock_flags = 0
                file_handle = _msvcrt.get_osfhandle(fd)

                if byte_range is not None:
                    seek_set = byte_range.start
                    lock_length = byte_range.stop - byte_range.start
                if seek_set != old_pos:
                    _os.lseek(fd, seek_set, _os.SEEK_SET)
                if not shared_lock:
                    lock_flags |= _win32con.LOCKFILE_EXCLUSIVE_LOCK
                else:  # If a shared lock using pywin32 gets opened by PyCharm and something is written than reverted,
                    lock_length = _os.path.getsize(fd)  # the file is truncated to 0,
                    if blocking:  # even though the lock was never lifted. This doesn't happen with msvcrt
                        _msvcrt.locking(fd, _msvcrt.LK_RLCK, lock_length)
                    else:  # Simulate non-blocking shared lock by trying to acquire exclusive lock first
                        # Try to acquire non-blocking exclusive lock
                        _msvcrt.locking(fd, _msvcrt.LK_NBLCK, lock_length)
                        # Release exclusive lock and switch to shared read lock
                        _msvcrt.locking(fd, _msvcrt.LK_UNLCK, lock_length)
                        _msvcrt.locking(fd, _msvcrt.LK_RLCK, lock_length)  # Acquire read lock
                    return fd
                if not blocking:
                    lock_flags |= _win32con.LOCKFILE_FAIL_IMMEDIATELY

                try:  # Attempt to lock the file
                    _win32file.LockFileEx(file_handle, lock_flags, 0, lock_length, _overlapped)
                except _pywintypes.error as e:
                    if e.winerror == _winerror.ERROR_LOCK_VIOLATION:
                        raise OSError("File already locked.") from e
                finally:
                    if seek_set != old_pos:
                        _os.lseek(fd, old_pos, _os.SEEK_SET)  # Make sure to respect the position of the open flags
                return fd
            except OSError:
                _os.close(fd)
                return None
        elif self.os in {"Linux", "Darwin", "FreeBSD"}:
            try:
                lock_type = _fcntl.LOCK_SH if shared_lock else _fcntl.LOCK_EX
                if not blocking:
                    lock_type |= _fcntl.LOCK_NB  # Non-blocking flag
                if byte_range is None:
                    _fcntl.flock(fd, lock_type)
                else:
                    old_pos = _os.lseek(fd, 0, _os.SEEK_CUR)
                    _os.lseek(fd, byte_range.start, _os.SEEK_SET)
                    lock_length = byte_range.stop - byte_range.start
                    _fcntl.lockf(fd, lock_type, lock_length)
                    _os.lseek(fd, old_pos, _os.SEEK_SET)  # Make sure to respect the position of the open flags
                return fd
            except BlockingIOError:
                _os.close(fd)
                return None
        else:
            raise NotImplementedError(f"Unsupported system: {self.os}")

    def unlock_file(self, fd: int, byte_range: range | None = None, keep_fd_open: bool = True) -> None:
        """
        Unlocks the file or a byte range and closes the file descriptor.

        Args:
            fd (int): The file descriptor to unlock.
            byte_range (range): The byte range to unlock (optional). If None, unlocks the entire file.
            keep_fd_open (bool): If the file descriptor should be closed.

        Raises:
            NotImplementedError: If the operating system is not supported.
        """
        try:
            if self.os == "Windows":
                old_pos = _os.lseek(fd, 0, _os.SEEK_CUR)
                lock_length = -0x10000
                seek_set = 0
                file_handle = _msvcrt.get_osfhandle(fd)

                if byte_range is not None:
                    seek_set = byte_range.start
                    lock_length = byte_range.stop - byte_range.start
                if seek_set != old_pos:
                    _os.lseek(fd, seek_set, _os.SEEK_SET)

                try:
                    _win32file.UnlockFileEx(file_handle, 0, lock_length, _overlapped)
                except _pywintypes.error as e:
                    if e.winerror != _winerror.ERROR_NOT_LOCKED:
                        raise e
                finally:
                    if seek_set != old_pos:
                        _os.lseek(fd, old_pos, _os.SEEK_SET)  # Make sure to respect the position
            elif self.os in {"Linux", "Darwin", "FreeBSD"}:
                if byte_range is None:
                    _fcntl.flock(fd, _fcntl.LOCK_UN)
                else:
                    old_pos = _os.lseek(fd, 0, _os.SEEK_CUR)
                    _os.lseek(fd, byte_range.start, _os.SEEK_SET)
                    _fcntl.lockf(fd, _fcntl.LOCK_UN, byte_range.stop - byte_range.start)
                    _os.lseek(fd, old_pos, _os.SEEK_SET)  # Restore file pointer
            else:
                raise NotImplementedError(f"Unsupported system: {self.os}")
        finally:
            if not keep_fd_open:
                _os.close(fd)

    def is_file_locked(self, filepath: str) -> bool:
        """
        Check if the file is currently locked by attempting a non-blocking lock.

        Returns:
            bool: True if the file is locked, False if not.

        Raises:
            NotImplementedError: If the operating system is not supported.
        """
        fd = _os.open(filepath, _os.O_RDWR | _os.O_CREAT)

        if self.os == "Windows":
            try:
                _msvcrt.locking(fd, _msvcrt.LK_NBLCK, _os.path.getsize(filepath) or 1)
                _msvcrt.locking(fd, _msvcrt.LK_UNLCK, _os.path.getsize(filepath) or 1)
                _os.close(fd)
                return False
            except OSError:
                _os.close(fd)
                return True
        elif self.os in {"Linux", "Darwin", "FreeBSD"}:
            try:
                _fcntl.flock(fd, _fcntl.LOCK_EX | _fcntl.LOCK_NB)
                _fcntl.flock(fd, _fcntl.LOCK_UN)
                _os.close(fd)
                return False
            except BlockingIOError:
                _os.close(fd)
                return True
        else:
            raise NotImplementedError(f"Unsupported system: {self.os}")

    def page_size(self) -> int:
        """
        Returns the system's memory page size in bytes based on the operating system.

        For Windows, it returns the allocation granularity. For Linux, macOS (Darwin),
        and FreeBSD, it uses the `sysconf` system call to get the page size.

        Returns:
            int: The system's memory page size in bytes.

        Raises:
            NotImplementedError: If the operating system is unsupported.
        """
        if self.os == "Windows":
            return _ALLOCATIONGRANULARITY  # Is a constant so it doesn't need caching
        elif self.os in {"Linux", "Darwin", "FreeBSD"}:
            return _os.sysconf("SC_PAGESIZE") or _os.sysconf("SC_PAGE_SIZE")
        else:
            raise NotImplementedError(f"Unsupported system: {self.os}")

    def is_virtual_machine(self) -> bool:
        """
        Detects whether the system is running inside a virtual machine (VM).

        Virtual machines are widely used for reverse engineering, malware analysis,
        and testing environments due to their controlled nature and ability to
        safely inspect software behaviors. However, many applications, particularly
        those involved in anti-analysis techniques or performance optimization,
        need to detect if they are running in a VM. Here are common reasons to check:

        1. **Anti-Analysis Techniques**: Some software detects virtual
           environments to avoid execution or analysis in sandboxes or VMs.
        2. **Optimization**: Some applications may behave differently when running in
           virtualized environments (e.g., disable hardware acceleration, modify
           performance-sensitive features).
        3. **Licensing Restrictions**: Some applications use VM detection to prevent
           running on virtual machines due to licensing restrictions.

        This method checks for various indicators such as:
        - VM-specific hardware, drivers, or system artifacts
        - Performance anomalies in CPU behavior, such as data access time, cache handling,
          or register interactions.
        - CPU instruction differences that are unique to virtual environments.

        Returns:
            bool: True if the system is detected as a virtual machine, False otherwise.
        """

        # 1. Check for VM-specific hardware or drivers
        def check_vm_drivers():
            vm_drivers = [
                "VBOX",  # VirtualBox
                "VMware",  # VMware
                "QEMU",  # QEMU
                "Microsoft Hyper-V",  # Hyper-V
            ]
            try:
                # On Linux/Unix, we can check `/proc/cpuinfo`
                if self.os == "Linux":
                    with open("/proc/cpuinfo") as f:
                        if any(driver in f.read() for driver in vm_drivers):
                            return True
                # On Windows, use wmic to check for virtual hardware
                elif self.os == "Windows":
                    result = _subprocess.check_output("wmic baseboard get product", shell=True)
                    if any(driver in str(result) for driver in vm_drivers):
                        return True
            except Exception as e:
                pass
            return False

        # 2. Check CPU instruction behavior (simplified detection)
        def check_cpu_behavior():
            try:
                # Check access times (simplified example, measure cache speed)
                start = _time.time()
                for _ in range(1000000):
                    _ = _os.urandom(1)  # Random data access to stress CPU
                elapsed_time = _time.time() - start
                # Virtual environments can have slower performance for such repetitive tasks
                if elapsed_time > 0.5:  # Arbitrary threshold for a VM (adjust as necessary)
                    return True
            except Exception as e:
                pass
            return False

        # 3. Check for CPU instruction differences (test an uncommon instruction)
        def check_cpu_instructions():
            try:
                # VM-specific instructions often show different results or errors
                if "hypervisor" in _platform.uname().version:
                    return True
            except Exception as e:
                pass
            return False

        # Combine the checks
        if check_vm_drivers() or check_cpu_behavior() or check_cpu_instructions():
            return True
        return False

    def lock_workstation(self) -> None:
        """
        Locks the workstation based on the operating system.

        This method locks the screen/workstation for Windows, Linux (GNOME/KDE), macOS, and FreeBSD systems. The appropriate system command is automatically chosen depending on the OS identified via the `platform.system()` call.

        Supported operating systems:
        - Windows: Uses the `LockWorkStation` function from the Windows API (user32.dll) to lock the screen.
        - Linux (GNOME-based): Uses `gnome-screensaver-command -l` to lock the screen.
        - Linux (KDE-based): If GNOME lock fails, tries the KDE command `qdbus org.freedesktop.ScreenSaver /ScreenSaver Lock`.
        - macOS: Uses AppleScript to simulate pressing `Control + Command + Q` to lock the screen.
        - FreeBSD: Assumes GNOME-based locking, using `gnome-screensaver-command -l`.

        Raises:
            NotImplementedError: If the operating system is not supported or recognized.

        Example usage:
            locker = WorkstationLocker()
            locker.lock_workstation()

        """
        if self.os == "Windows":
            user32 = _ctypes.windll.User32
            user32.LockWorkStation()
        elif self.os == "Linux":
            # Try to lock using Gnome or KDE specific commands
            if _os.system("gnome-screensaver-command -l") != 0:
                # If Gnome screensaver command fails, try KDE command
                _os.system("qdbus org.freedesktop.ScreenSaver /ScreenSaver Lock")
        elif self.os == "Darwin":  # macOS
            _os.system("""osascript -e 'tell application "System Events" to keystroke "q" using {control down, command down}'""")
        elif self.os == "FreeBSD":
            # Assuming FreeBSD would have similar command line utilities as Linux
            _os.system("gnome-screensaver-command -l")
        else:
            raise NotImplementedError(f"Unsupported system: {self.os}")

    def open_location(self, location: str) -> None:
        """
        Open the file location in the system's file explorer.

        Args:
            location: The file location to be opened.

        Returns:
            None
        """
        if self.os == "Windows":
            _subprocess.run(["explorer.exe", location])
        elif self.os == "Darwin":
            _subprocess.run(["open", location])
        elif self.os in {"Linux", "FreeBSD"}:  # Try common Linux file managers
            for file_manager in ["xdg-open", "nautilus", "dolphin", "thunar"]:
                try:
                    _subprocess.run([file_manager, location])
                    break
                except FileNotFoundError:
                    continue
        else:
            raise NotImplementedError(f"Unsupported system: {self.os}")


BaseSystemType: _BaseSystem = _BaseSystem


class _WindowsSystem(_BaseSystem):
    """
    A class representing Windows-specific system functionalities, such as retrieving CPU and GPU information,
    managing system theme, scheduling events, and sending notifications.
    """

    def get_cpu_brand(self) -> str:
        """
        Get the brand and model of the CPU specific to Windows systems.

        :return: A string representing the CPU brand and model.
        """
        return _platform.processor()

    def get_gpu_info(self) -> list[str]:
        """
        Get the GPU information for Windows systems using the WMIC (Windows Management Instrumentation Command).

        :return: A list of strings representing the names of the video controllers (GPUs) on the system.
        """
        command = "wmic path win32_VideoController get name"
        output = _subprocess.check_output(command.split(" ")).decode()
        return [line.strip() for line in output.split("\n") if line.strip()][1:]

    def get_system_theme(self) -> SystemTheme:
        """
        Get the current Windows system theme (light or dark) by checking the registry settings for theme preferences.

        :return: The system theme, either LIGHT, DARK, or UNKNOWN if the theme could not be determined.
        """
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

    def schedule_event(self, name: str, script_path: str, event_time: _ty.Literal["startup", "login"]) -> None:
        """
        Schedule an event to run at startup or login on a Windows system using the Task Scheduler.

        :param name: The name of the event to be scheduled.
        :param script_path: The path to the script that should run at the scheduled event time.
        :param event_time: The time to schedule the event, either 'startup' or 'login'.
        """
        task_name, command = f"{name} (APT-{event_time.capitalize()} Task)", ""
        if event_time == "startup":
            command = f'schtasks /create /tn "{task_name}" /tr "{script_path}" /sc onstart /rl highest /f'
        elif event_time == "login":
            command = f'schtasks /create /tn "{task_name}" /tr "{script_path}" /sc onlogon /rl highest /f'
        _subprocess.run(command.split(" "), check=True)

    def send_notification(self, title: str, message: str,
                          input_fields: tuple[tuple[str, str, str], ...] = (("input_arg", "Input", "Hint"),),
                          selections: tuple[tuple[str, str, list[tuple], int], ...] = (("selection_arg", "Sel Display Name", ["selection_name", "Selection Display Name"], 0),),
                          buttons: tuple[tuple[str, _a.Callable], ...] = (("Accept", lambda: None), ("Cancel", lambda: None),),
                          click_callback: _a.Callable = lambda: None) -> None:
        """
        Send a notification on Windows systems, supporting both simple and interactive notifications with input fields,
        selections, and buttons.

        :param title: The title of the notification.
        :param message: The message content to display in the notification.
        :param input_fields: A tuple of input field configurations for the notification (optional).
        :param selections: A tuple of selection field configurations for the notification (optional).
        :param buttons: A tuple of button configurations for the notification (optional).
        :param click_callback: A callback function triggered when the notification is clicked (optional).
        """
        if not (input_fields or selections or buttons):
            if _WindowsToaster is not None and _Toast is not None:
                toaster = _WindowsToaster(title)
                new_toast = _Toast()
                new_toast.text_fields = [message]
                new_toast.on_activated = click_callback
                toaster.show_toast(new_toast)
        else:
            if (_InteractableWindowsToaster is not None
                    and _Toast is not None
                    and _ToastInputTextBox is not None
                    and _ToastSelection is not None
                    and _ToastButton is not None):
                interactable_toaster = _InteractableWindowsToaster(title)
                new_toast = _Toast([message])

                for input_field in input_fields:
                    arg_name, display_name, input_hint = input_field
                    new_toast.AddInput(_ToastInputTextBox(arg_name, display_name, input_hint))

                for selection in selections:
                    selection_arg_name, selection_display_name, selection_options, default_selection_id = selection

                    selection_option_objects = []
                    for selection_option in selection_options:
                        selection_option_id, selection_option_display_name = selection_option
                        selection_option_objects.append(_ToastSelection(selection_option_id, selection_option_display_name))

                    new_toast.AddInput(_ToastInputSelectionBox(selection_arg_name, selection_display_name,
                                                              selection_option_objects,
                                                              selection_option_objects[default_selection_id]))

                response_lst = []
                for i, button in enumerate(buttons):
                    button_text, callback = button
                    response_lst.append(callback)
                    new_toast.AddAction(_ToastButton(button_text, str(i)))

                new_toast.on_activated = lambda activated_event_args: (response_lst[int(activated_event_args.arguments)]()
                                                                       or click_callback(**activated_event_args.inputs))

                interactable_toaster.show_toast(new_toast)

    def send_native_notification(self, title: str, message: str) -> None:
        """
        Send a simple native Windows notification using the Windows toast system.

        :param title: The title of the notification.
        :param message: The message content to display in the notification.
        """
        if _WindowsToaster is not None and _Toast is not None:
            toaster = _WindowsToaster(title)
            new_toast = _Toast()
            new_toast.text_fields = [message]
            toaster.show_toast(new_toast)
        else:
            print("You are not on a default windows machine")

    def get_battery_status(self) -> dict[str, float | int | bool]:
        """
        Get the battery status on a Windows system, including battery percentage, time left, and charging status.

        :return: A dictionary containing battery status information: 'percent', 'secsleft', and 'power_plugged'.
        """
        if _psutil is None:
            raise ValueError("Optional dependency psutil is not installed.")
        battery = _psutil.sensors_battery()
        if battery:
            return {"percent": battery.percent, "secsleft": battery.secsleft, "power_plugged": battery.power_plugged}

    def get_appdata_directory(self, app_dir: str, scope: _ty.Literal["user", "global"] = "global") -> str:
        """
        Get the appropriate AppData directory for storing application data based on the specified scope (user or global).

        :param app_dir: The name of the folder designated for the application's data.
        :param scope: The data scope, either 'user' for user-specific data or 'global' for data accessible to all users.

        :return: The path to the appropriate AppData directory.
        """
        if scope == "user":
            return _os.path.join(_os.environ.get("APPDATA"), app_dir)  # App data for the current user
        return _os.path.join(_os.environ.get("PROGRAMDATA"), app_dir)  # App data for all users

    def get_clipboard(self) -> str | None:
        """
        Get the content of the Windows clipboard.

        :return: The content of the clipboard as a string. If the clipboard is empty, returns None.
        """
        _win32clipboard.OpenClipboard()
        try:
            data = _win32clipboard.GetClipboardData()
        except TypeError:
            data = None
        _win32clipboard.CloseClipboard()
        return data

    def set_clipboard(self, data: str) -> None:
        """
        Set the Windows clipboard content with the specified string data.

        :param data: The string data to set in the clipboard.
        """
        _win32clipboard.OpenClipboard()
        _win32clipboard.EmptyClipboard()
        _win32clipboard.SetClipboardText(data)
        _win32clipboard.CloseClipboard()

    def get_system_language(self) -> tuple[str | str | None, str | str | None]:
        """
        Get the system language and encoding on a Windows system.

        :return: A tuple containing the language code and the encoding format. If not available, it retrieves the system's
                 default UI language.
        """
        language_code, encoding = super().get_system_language()
        if language_code:
            return language_code, encoding
        else:
            GetUserDefaultUILanguage = _ctypes.windll.kernel32.GetUserDefaultUILanguage
            lang_id = GetUserDefaultUILanguage()
            return _locale.windows_locale[lang_id], None


class _DarwinSystem(_BaseSystem):
    """System methods specific to macOS (Darwin)."""

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
            return SystemTheme.UNKNOWN

    def schedule_event(self, name: str, script_path: str, event_time: _ty.Literal["startup", "login"]):
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

    def get_appdata_directory(self, app_dir: str, scope: _ty.Literal["user", "global"] = "global"):
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
        result = _subprocess.run(['defaults', 'read', '-g', 'AppleLocale'], stdout=_subprocess.PIPE)
        return result.stdout.decode().strip(), None


class _LinuxSystem(_BaseSystem):
    """System methods specific to Linux."""

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
        """Get the current system theme by checking multiple desktop environments."""
        try:
            if "gnome" in _os.getenv("XDG_CURRENT_DESKTOP", "").lower():
                command = "gsettings get org.gnome.desktop.interface gtk-theme"
                theme = _subprocess.check_output(command.split(" ")).decode().strip().strip("'")
                return SystemTheme.DARK if "dark" in theme.lower() else SystemTheme.LIGHT
            elif "kde" in _os.getenv("XDG_CURRENT_DESKTOP", "").lower():
                command = "lookandfeeltool --current"
                theme = _subprocess.check_output(command.split(" ")).decode().strip()
                return SystemTheme.DARK if "dark" in theme.lower() else SystemTheme.LIGHT
            elif "xfce" in _os.getenv("XDG_CURRENT_DESKTOP", "").lower():
                command = "xfconf-query -c xsettings -p /Net/ThemeName"
                theme = _subprocess.check_output(command.split(" ")).decode().strip()
                return SystemTheme.DARK if "dark" in theme.lower() else SystemTheme.LIGHT
            raise _subprocess.CalledProcessError
        except _subprocess.CalledProcessError:
            # If theme detection fails for all, return unknown theme
            return SystemTheme.UNKNOWN

    def schedule_event(self, name: str, script_path: str, event_time: _ty.Literal["startup", "login"]):
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

    def get_appdata_directory(self, app_dir: str, scope: _ty.Literal["user", "global"] = "global"):
        if scope == "user":
            return _os.path.join(_os.path.expanduser("~"), ".local", "share", app_dir)  # App data for the current user
        return _os.path.join("/usr/local/share", app_dir)  # App data for all users

    def get_clipboard(self):
        command = "xclip -selection clipboard -o"
        try:
            return _subprocess.check_output(command.split(" ")).decode().strip()
        except _subprocess.CalledProcessError:
            return None

    def set_clipboard(self, data: str) -> None:
        command = f'echo "{data}" | xclip -selection clipboard'
        _subprocess.run(command.split(" "))

    def get_system_language(self) -> tuple[str | str | None, str | str | None]:
        language_code, encoding = super().get_system_language()
        return language_code or _os.getenv('LANG', 'en_US'), encoding


class _FreeBSDSystem(_LinuxSystem):
    """System methods specific to FreeBSD."""

    def get_cpu_brand(self) -> str:
        """Get CPU brand using sysctl."""
        command = "sysctl -n hw.model"
        return _subprocess.check_output(command.split(" ")).decode().strip()

    def get_gpu_info(self) -> list[str]:
        """Get GPU information for FreeBSD."""
        command = "pciconf -lv | grep -A 4 'display'"
        try:
            output = _subprocess.check_output(command, shell=True).decode()
            return [line.strip() for line in output.splitlines()]
        except _subprocess.CalledProcessError:
            return ["pciconf command not found"]

    def get_system_theme(self) -> SystemTheme:
        """Get the current system theme by checking multiple desktop environments."""
        try:
            if "gnome" in _os.getenv("XDG_CURRENT_DESKTOP", "").lower():
                command = "gsettings get org.gnome.desktop.interface gtk-theme"
                theme = _subprocess.check_output(command.split(" ")).decode().strip().strip("'")
                return SystemTheme.DARK if "dark" in theme.lower() else SystemTheme.LIGHT
            elif "kde" in _os.getenv("XDG_CURRENT_DESKTOP", "").lower():
                command = "lookandfeeltool --current"
                theme = _subprocess.check_output(command.split(" ")).decode().strip()
                return SystemTheme.DARK if "dark" in theme.lower() else SystemTheme.LIGHT
            elif "xfce" in _os.getenv("XDG_CURRENT_DESKTOP", "").lower():
                command = "xfconf-query -c xsettings -p /Net/ThemeName"
                theme = _subprocess.check_output(command.split(" ")).decode().strip()
                return SystemTheme.DARK if "dark" in theme.lower() else SystemTheme.LIGHT
            raise _subprocess.CalledProcessError
        except _subprocess.CalledProcessError:
            # If theme detection fails for all, return unknown theme
            return SystemTheme.UNKNOWN

    def get_appdata_directory(self, app_dir: str, scope: _ty.Literal["user", "global"] = "global") -> str:
        """Get application data directory for FreeBSD."""
        if scope == "user":
            return _os.path.join(_os.path.expanduser("~"), ".local", "share", app_dir)
        return _os.path.join("/usr/local/share", app_dir)

    def get_clipboard(self) -> str | None:
        """Get clipboard content using xclip or xsel (if available on FreeBSD)."""
        try:
            return _subprocess.check_output(["xclip", "-selection", "clipboard", "-o"]).decode().strip()
        except _subprocess.CalledProcessError:
            return None

    def set_clipboard(self, data: str) -> None:
        """Set clipboard content using xclip or xsel (if available)."""
        _subprocess.run(f'echo "{data}" | xclip -selection clipboard', shell=True)

    def get_system_language(self) -> tuple[str | None, str | None]:
        """Get system language for FreeBSD."""
        language_code, encoding = super().get_system_language()
        return language_code or _os.getenv('LANG', 'en_US'), encoding


def get_system() -> _WindowsSystem | _DarwinSystem | _LinuxSystem | _FreeBSDSystem | _BaseSystem:
    """Gets the appropriate system instance based on the operating system."""
    os_name = _platform.system()
    if os_name == "Windows":
        return _WindowsSystem()
    elif os_name == "Darwin":
        return _DarwinSystem()
    elif os_name == "Linux":
        return _LinuxSystem()
    elif os_name == "FreeBSD":
        return _FreeBSDSystem()
    else:
        _warnings.warn("Unsupported Operating System, returning _BaseSystem instance.", RuntimeWarning, 2)
        return _BaseSystem()


def diagnose_shutdown_blockers(suggestions: bool = True, return_result: bool = False) -> str | None:
    """
    Diagnose potential blockers that may prevent the Python process from shutting down cleanly.

    This function checks for common conditions that may block a Python application from exiting, such as:
    - Active threads
    - Active child processes
    - Open files
    - Open network connections

    If any blockers are found, they will be listed along with suggestions for resolving them (if `suggestions=True`).
    The function can either print the results or return them as a string.

    Args:
        suggestions (bool): Whether to include suggestions for resolving the blockers. Defaults to True.
        return_result (bool): Whether to return the results as a string instead of printing them.
                              If True, returns the result; otherwise, it prints the result. Defaults to False.

    Returns:
        str | None: A string describing the blockers if `return_result=True`, or `None` if the results are printed.
                    If no blockers are found, a message indicating no issues is returned.

    Example:
        >>> diagnose_shutdown_blockers(suggestions=True, return_result=False)
        Active threads: ['Thread-1', 'MainThread']
        Suggestion: Ensure all threads complete or are set as daemon threads.
        Active child processes: [12345, 12346]
        Suggestion: Ensure all child processes are properly terminated using process.terminate() or process.join().
        ...

    Notes:
        - This function uses the `threading`, `multiprocessing`, and `psutil` modules to inspect the current
          process's threads, child processes, open files, and network connections.
        - For proper cleanup, ensure that all resources (threads, processes, files, connections) are appropriately
          closed or terminated before attempting to shut down the Python process.

    """
    blockers = []

    # Check for active threads
    active_threads = _threading_enumerate()
    if len(active_threads) > 1:  # More than just the main thread
        blockers.append(f"Active threads: {[thread.name for thread in active_threads]}")
        blockers.append("Suggestion: Ensure all threads complete or are set as daemon threads.")

    # Check for active processes
    current_process = _multiprocessing_process()
    if _psutil is None:
        raise RuntimeError("Psutil is not installed")
    child_processes = _psutil.Process(_os.getpid()).children(recursive=True)
    if child_processes:
        blockers.append(f"Active child processes: {[proc.pid for proc in child_processes]}")
        blockers.append("Suggestion: Ensure all child processes are "
                        "properly terminated using process.terminate() or process.join().")

    # Check for open files
    open_files = _psutil.Process(_os.getpid()).open_files()
    if open_files:
        blockers.append(f"Open files: {[file.path for file in open_files]}")
        blockers.append("Suggestion: Ensure all files are properly closed using file.close().")

    # Check for open network connections
    open_connections = _psutil.Process(_os.getpid()).connections()
    if open_connections:
        blockers.append(f"Open network connections: {open_connections}")
        blockers.append("Suggestion: Ensure all network connections are properly closed.")

    if not blockers:
        returns = "No obvious blockers preventing Python from shutting down."
    else:
        returns = "\n".join(blockers if suggestions else blockers[::2])

    if return_result:
        return returns
    print(returns)


@_contextmanager
def suppress_warnings():
    """Context manager to suppress warnings."""
    _warnings.filterwarnings("ignore")
    try:
        yield
    finally:
        _warnings.filterwarnings("default")


def auto_repr(cls: type, *_, use_repr: bool = False):
    """
    Decorator that automatically generates a __repr__ method for a class.
    """
    if cls.__repr__ is object.__repr__:
        def __repr__(self):
            if not use_repr:
                attributes = ', '.join(f"{key}={getattr(self, key)}" for key in self.__dict__ if not key.startswith("_")
                                       or (key.startswith("__") and key.endswith("__")))
            else:
                attributes = ', '.join(f"{key}={repr(getattr(self, key))}" for key in self.__dict__ if not key.startswith("_")
                                       or (key.startswith("__") and key.endswith("__")))
            return f"{cls.__name__}({attributes})"

        cls.__repr__ = __repr__
    return cls


def auto_repr_with_privates(cls: type, use_repr: bool = False):
    """
    Decorator that automatically generates a __repr__ method for a class, including all private attributes.
    """
    if cls.__repr__ is object.__repr__:
        def __repr__(self):
            if not use_repr:
                attributes = ', '.join(f"{key}={getattr(self, key)}" for key in self.__dict__)
            else:
                attributes = ', '.join(f"{key}={repr(getattr(self, key))}" for key in self.__dict__)
            return f"{cls.__name__}({attributes})"

        cls.__repr__ = __repr__
    return cls


def is_accessible(path: str) -> bool:
    """
    Check if a path is accessible (has read/write permissions).

    :param path: The path to be checked.
    :return: True if accessible, False otherwise.
    """
    return _os.access(path, _os.R_OK | _os.W_OK)


class BasicSystemFunctions:
    """Encapsulates common system utilities and information retrieval methods."""

    @staticmethod
    def get_home_directory() -> str:
        """Retrieve the path to the user's home directory.

        Returns:
            str: The absolute path to the user's home directory.
        """
        return _os.path.expanduser("~")

    @staticmethod
    def get_running_processes() -> list[dict[str, int | str]]:
        """Retrieve a list of currently running processes, including PID and name.

        Returns:
            List[Dict[str, Union[int, str]]]: A list of dictionaries containing process information.
        """
        processes = []
        for proc in _psutil.process_iter(['pid', 'name']):
            try:
                processes.append(proc.as_dict(attrs=['pid', 'name']))
            except _psutil.NoSuchProcess:
                pass  # Process has terminated between iteration and retrieval
        return processes

    @classmethod
    def get_disk_usage(cls, path: str | None = None) -> dict[str, str]:
        """Retrieve disk usage statistics for a specified path.

        Args:
            path (Optional[str], optional): Path to check disk usage for. Defaults to the home directory.

        Returns:
            Dict[str, str]: A dictionary containing total, used, and free space.
        """
        if path is None:
            path = cls.get_home_directory()
        usage = _shutil.disk_usage(path)
        return {
            'total': _bytes_to_human_readable_binary_iec(usage.total),
            'used': _bytes_to_human_readable_binary_iec(usage.used),
            'free': _bytes_to_human_readable_binary_iec(usage.free)
        }

    @staticmethod
    def get_memory_info() -> dict[str, str]:
        """Retrieve memory usage statistics for the current system.

        Returns:
            Dict[str, str]: A dictionary containing total, available, percent used, used, and free memory.
        """
        memory = _psutil.virtual_memory()
        return {
            'total': _bytes_to_human_readable_binary_iec(memory.total),
            'available': _bytes_to_human_readable_binary_iec(memory.available),
            'percent': f"{memory.percent}%",
            'used': _bytes_to_human_readable_binary_iec(memory.used),
            'free': _bytes_to_human_readable_binary_iec(memory.free)
        }

    @staticmethod
    def get_network_info() -> dict[str, dict[str, bool | list[dict[str, str | None]]]]:
        """Retrieve information about network interfaces.

        Returns:
            Dict[str, Dict[str, Union[bool, List[Dict[str, Union[str, None]]]]]]:
                A dictionary with network interface information, including addresses and status.
        """
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
    def set_environment_variable(key: str, value: str) -> None:
        """Set an environment variable.

        Args:
            key (str): Name of the environment variable.
            value (str): Value to assign to the environment variable.
        """
        _os.environ[key] = value

    @staticmethod
    def get_environment_variable(key: str) -> str | None:
        """Retrieve an environment variable's value.

        Args:
            key (str): Name of the environment variable.

        Returns:
            Optional[str]: Value of the environment variable, or None if it is not set.
        """
        return _os.environ.get(key)

    @staticmethod
    def get_uptime() -> float:
        """Calculate the system uptime in minutes.

        Returns:
            float: System uptime in minutes.
        """
        return (_time.time() - _psutil.boot_time()) / 60

    @staticmethod
    def set_working_dir_to_main_script_location() -> None:
        """Set the current working directory to the main script's location.

        This considers whether the script is frozen (e.g., PyInstaller) or running
        as a normal Python script.
        """
        import __main__
        try:
            if getattr(_sys, 'frozen', False):
                main_dir = _os.path.dirname(_sys.executable)
            else:
                if hasattr(__main__, '__file__'):
                    main_dir = _os.path.dirname(_os.path.abspath(__main__.__file__))
                else:
                    main_dir = _os.getcwd()
                    _warnings.warn(
                        "Unable to set working directory to main script's location. Using current working directory.",
                        RuntimeWarning,
                        stacklevel=2
                    )
            _os.chdir(main_dir)
            print(f"Working directory set to {main_dir}")

        except Exception as e:
            print(f"An error occurred while changing the working directory: {e}")
            raise  # Re-raise the error

    @staticmethod
    def change_working_dir_to_script_location() -> None:
        """Set the current working directory to the script's directory.

        Uses the caller's file path, which may differ from the main script's location.
        """
        try:
            if getattr(_sys, 'frozen', False):
                script_dir = _os.path.dirname(_sys.executable)
            else:
                frame = _inspect.currentframe()
                caller_frame = frame.f_back
                caller_file = caller_frame.f_globals["__file__"]
                script_dir = _os.path.dirname(_os.path.abspath(caller_file))

            _os.chdir(script_dir)
            print(f"Working directory changed to {script_dir}")
        except Exception as e:
            print(f"An error occurred while changing the working directory: {e}")
            raise

    @staticmethod
    def change_working_dir_to_temp_folder() -> None:
        """Set the current working directory to the system's temporary folder."""
        try:
            temp_dir = _tempfile.gettempdir()
            _os.chdir(temp_dir)
            print(f"Working directory changed to {temp_dir}")

        except Exception as e:
            print(f"An error occurred while changing the working directory: {e}")
            raise

    @staticmethod
    def change_working_dir_to_new_temp_folder() -> str:
        """Create a new temporary folder and set it as the working directory.

        Returns:
            str: Path to the newly created temporary folder.
        """
        try:
            folder = _tempfile.mkdtemp()
            _os.chdir(folder)
            return folder
        except Exception as e:
            print(f"An error occurred while changing the working directory: {e}")
            raise

    @staticmethod
    def change_working_dir_to_userprofile_folder(folder: str) -> None:
        """Change the current working directory to a specified subfolder in the user's home directory.

        Args:
            folder (str): Name of the subfolder to navigate to within the home directory.

        Raises:
            OSError: If the operating system is unsupported.
        """
        try:
            if _os.name == 'posix':
                home_dir = _os.path.join(_os.path.expanduser("~"), folder)
            elif _os.name == 'nt':
                home_dir = _os.path.join(_os.environ['USERPROFILE'], folder)
            else:
                raise OSError(f"System {_os.name} is unsupported by this function.")
            _os.chdir(home_dir)
            print(f"Working directory changed to {home_dir}")
        except Exception as e:
            print(f"An error occurred while changing the working directory: {e}")
            raise


def is_compiled() -> bool:
    """
    Detects if the code is running in a compiled environment and identifies the compiler used.

    This function checks for the presence of attributes and environment variables specific
    to common Python compilers, including PyInstaller, cx_Freeze, and py2exe.
    :return: bool
    """
    return getattr(_sys, "frozen", False) and (hasattr(_sys, "_MEIPASS") or _sys.executable.endswith(".exe"))
