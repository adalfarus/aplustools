"""TBA"""
from traceback import format_exc as _format_exc
from pathlib import Path as _PLPath
import logging as _logging
import sys as _sys
import os as _os
import re as _re

from .qtquick import QQuickMessageBox as _QQuickMessageBox
from .env import get_system as _get_system, SystemTheme as _SystemTheme
from . import ActLogger
from ..package import enforce_hard_deps as _enforce_hard_deps
from ..data.storage import (StorageMedium, JSONStorage, SQLite3Storage, BinaryStorage,
                            SimpleStorageMedium, SimpleJSONStorage, SimpleSQLite3Storage, SimpleBinaryStorage)

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

__deps__: list[str] = []
__hard_deps__: list[str] = ["PySide6>=6.7.0"]
_enforce_hard_deps(__hard_deps__, __name__)

from PySide6.QtWidgets import QApplication as _QApplication, QMainWindow as _QMainWindow, QMessageBox as _QMessageBox
from PySide6.QtGui import (QCloseEvent as _QCloseEvent, QResizeEvent as _QResizeEvent, QMoveEvent as _QMoveEvent,
                           QFocusEvent as _QFocusEvent, QKeyEvent as _QKeyEvent, QMouseEvent as _QMouseEvent,
                           QEnterEvent as _QEnterEvent, QPaintEvent as _QPaintEvent,
                           QDragEnterEvent as _QDragEnterEvent, QDragMoveEvent as _QDragMoveEvent,
                           QDropEvent as _QDropEvent, QDragLeaveEvent as _QDragLeaveEvent, QShowEvent as _QShowEvent,
                           QHideEvent as _QHideEvent, QContextMenuEvent as _QContextMenuEvent,
                           QWheelEvent as _QWheelEvent, QTabletEvent as _QTabletEvent)
from PySide6.QtCore import QTimer as _QTimer, QEvent as _QEvent, QTimerEvent as _QTimerEvent


class AppFSModifier:
    """FileSystemManager Modifiers"""
    UNMANAGED = 0
    MANAGED = 1
    SECURE = 2
    OSLOCK = 4


class AppFile:
    modifiers: int = AppFSModifier.UNMANAGED

    def __init__(self, location: str, parent: "AppDir", secure: bool = False, oslock: bool = False,
                 managed: bool = True) -> None:
        self.location: str = location
        self.parent: "AppDir" = parent
        self.modifiers = (self.modifiers  # True is 1, False is 0
                          | (AppFSModifier.MANAGED * managed)
                          | (AppFSModifier.SECURE * secure)
                          | (AppFSModifier.OSLOCK * oslock))

    def write(self):
        ...

    def append(self):
        ...

    def read(self, from_: int):
        ...

    def encrypt(self, key: bytes):  # Key can be stored as a secret of the framework
        if not self.modifiers & AppFSModifier.SECURE:
            raise ValueError("Your manged instance does not support this method")
        ...  # Encrypt / Decrypt on the fly

    def decrypt(self, key: bytes):  # Key can be stored as a secret of the framework
        if not self.modifiers & AppFSModifier.SECURE:
            raise ValueError("Your manged instance does not support this method")
        ...  # Encrypt / Decrypt on the fly

    def lock(self):
        if not self.modifiers & AppFSModifier.OSLOCK:
            raise ValueError("Your manged instance does not support this method")
        ...

    def unlock(self):
        if not self.modifiers & AppFSModifier.OSLOCK:
            raise ValueError("Your manged instance does not support this method")
        ...


class AppDir:
    modifiers: int = AppFSModifier.UNMANAGED

    def __init__(self, location: str, parent: _ty.Self | None = None, secure: bool = False,
                 oslock: bool = False, managed: bool = True) -> None:
        self.location: str = location
        self.parent: _ty.Self | None = parent
        if parent is None:
            self.tree: dict = {}  # Only used by the parent (for backups, as well as for a redundant parity file)
            # Unmanaged are not in it (e.g. a temp folder)
        self.modifiers = (self.modifiers  # True is 1, False is 0
                          | (AppFSModifier.MANAGED * managed)
                          | (AppFSModifier.SECURE * secure)
                          | (AppFSModifier.OSLOCK * oslock))

    def app_dir(self, relative_location: str, secure: bool, oslock: bool, *_, unmanaged: bool = False) -> _ty.Self:
        return type(self)(
            self.default_dir(relative_location),
            self.parent or self,
            self.modifiers & AppFSModifier.SECURE or secure,
            self.modifiers & AppFSModifier.OSLOCK or oslock,
            not unmanaged)

    def default_dir(self, relative_location: str) -> str:
        new_loc = _os.path.join(self.location, relative_location)
        _os.makedirs(new_loc, exist_ok=True)
        return new_loc

    def app_file(self, relative_location: str, secure: bool, oslock: bool, *_, unmanaged: bool = False) -> AppFile:
        return AppFile(
            self.default_file(relative_location),
            self.parent or self,
            self.modifiers & AppFSModifier.SECURE or secure,
            self.modifiers & AppFSModifier.OSLOCK or oslock,
            not unmanaged)

    def default_file(self, relative_location: str) -> str:
        new_loc = _os.path.join(self.location, relative_location)
        if not _os.path.exists(new_loc):
            open(new_loc, "w").close()
        return new_loc

    def app_storage(self, relative_location: str, multiuser: bool = False, unmanged: bool = False,
                    storage_type: _ty.Literal["json", "sqlite3", "binary"] = "json"
                    ) -> StorageMedium | SimpleStorageMedium:
        mediums = {"json": SimpleJSONStorage, "sqlite3": SimpleSQLite3Storage, "binary": SimpleBinaryStorage}
        if multiuser:
            mediums = {"json": JSONStorage, "sqlite3": SQLite3Storage, "binary": BinaryStorage}
        instance = mediums[storage_type](self.default_file(relative_location))
        if not unmanged:
            self.parent.tree[relative_location] = True  # How?
        return instance

    def encrypt(self, key: bytes):  # Key can be stored as a secret of the framework
        if not self.modifiers & AppFSModifier.SECURE:
            raise ValueError("Your manged instance does not support this method")
        ...  # Encrypt / Decrypt on the fly

    def decrypt(self, key: bytes):  # Key can be stored as a secret of the framework
        if not self.modifiers & AppFSModifier.SECURE:
            raise ValueError("Your manged instance does not support this method")
        ...  # Encrypt / Decrypt on the fly

    def lock(self):
        if not self.modifiers & AppFSModifier.OSLOCK:
            raise ValueError("Your manged instance does not support this method")
        ...

    def unlock(self):
        if not self.modifiers & AppFSModifier.OSLOCK:
            raise ValueError("Your manged instance does not support this method")
        ...


class MainWindowInterface(_QMainWindow):
    """
    Interface for main window functionality. This class is not meant to be instantiated directly
    and should only be used as a base for other classes. Attempting to initialize this class
    will raise an exception.

    Raises:
        Exception: If an attempt is made to instantiate this class directly.
    """
    def __new__(cls: type, *args: _ty.Any, **kwargs: _ty.Any) -> None:
        raise Exception("This class can't be initialized; it is just an Interface.")


class ActApp:
    """TBA"""
    logger: ActLogger | None = None
    _persistent_app_storage: StorageMedium | None = None
    _framework: "ActFramework | None" = None
    app_directory: str | None = None
    exit_code: int = 0
    name: str = "ActApp"

    def __init__(self, _: list[str], window: MainWindowInterface) -> None:
        self.window: _QMainWindow = window
        self.popups: list[_ty.Any] = []
        self.linked = False
        self.link()

    def closeEvent(self, event: _QCloseEvent) -> None:
        ...

    def resizeEvent(self, event: _QResizeEvent) -> None:
        ...

    def moveEvent(self, event: _QMoveEvent) -> None:
        ...

    def focusInEvent(self, event: _QFocusEvent) -> None:
        ...

    def focusOutEvent(self, event: _QFocusEvent) -> None:
        ...

    def keyPressEvent(self, event: _QKeyEvent) -> None:
        ...

    def keyReleaseEvent(self, event: _QKeyEvent) -> None:
        ...

    def mousePressEvent(self, event: _QMouseEvent) -> None:
        ...

    def mouseReleaseEvent(self, event: _QMouseEvent) -> None:
        ...

    def mouseDoubleClickEvent(self, event: _QMouseEvent) -> None:
        ...

    def mouseMoveEvent(self, event: _QMouseEvent) -> None:
        ...

    def enterEvent(self, event: _QEnterEvent) -> None:
        ...

    def leaveEvent(self, event: _QEvent) -> None:
        ...

    def paintEvent(self, event: _QPaintEvent) -> None:
        ...

    def dragEnterEvent(self, event: _QDragEnterEvent) -> None:
        ...

    def dragMoveEvent(self, event: _QDragMoveEvent) -> None:
        ...

    def dropEvent(self, event: _QDropEvent) -> None:
        ...

    def dragLeaveEvent(self, event: _QDragLeaveEvent) -> None:
        ...

    def showEvent(self, event: _QShowEvent) -> None:
        ...

    def hideEvent(self, event: _QHideEvent) -> None:
        ...

    def contextMenuEvent(self, event: _QContextMenuEvent) -> None:
        ...

    def wheelEvent(self, event: _QWheelEvent) -> None:
        ...

    def tabletEvent(self, event: _QTabletEvent) -> None:
        ...

    def timerEvent(self, event: _QTimerEvent) -> None:
        ...

    def _create_link_event(self, event_handler, eventFunc) -> _a.Callable:
        return lambda e: (event_handler(e), getattr(self, eventFunc)(e))

    def link(self):  # Link self.window with the internal method of updating
        if not self.linked:
            self.linked = True
            for eventFunc in ("closeEvent", "resizeEvent", "moveEvent", "focusInEvent", "focusOutEvent",
                              "keyPressEvent", "keyReleaseEvent", "mousePressEvent", "mouseReleaseEvent",
                              "mouseDoubleClickEvent", "mouseMoveEvent", "enterEvent", "leaveEvent", "paintEvent",
                              "dragEnterEvent", "dragMoveEvent", "dropEvent", "dragLeaveEvent", "showEvent",
                              "hideEvent", "contextMenuEvent", "wheelEvent", "tabletEvent", "timerEvent"):
                event_handler = getattr(self.window, eventFunc)
                setattr(self.window, eventFunc, self._create_link_event(event_handler, eventFunc))

    def start(self) -> None:
        self.window.show()

    def stop(self) -> None:
        ...

    def set_light_mode(self, window: _QMainWindow) -> None:
        ...

    def set_dark_mode(self, window: _QMainWindow) -> None:
        ...

    def set_light_theme_setter(self, theme_name: str, light_theme_setter: _a.Callable) -> None:
        ...

    def set_dark_theme_setter(self, theme_name: str, dark_theme_setter: _a.Callable) -> None:
        ...

    def store(self, key: str, data: str, secret: bool = False) -> None:
        self._persistent_app_storage.store({key: data})

    def store_many(self, items: dict[str, str], secrets: bool = False) -> None:
        self._persistent_app_storage.store(items)

    def load(self, key: str, secret: bool = False) -> str | None:
        return self._persistent_app_storage.retrieve([key])[0]

    def load_many(self, keys: list[str], secrets: bool = False) -> list[str | None]:
        return self._persistent_app_storage.retrieve(keys)

    def clear_storage(self) -> None:
        _os.remove(self._persistent_app_storage.filepath())
        self._persistent_app_storage.create_storage(self._persistent_app_storage.filepath())

    def create_popup(self) -> int:  # Return the popup-index
        ...

    def destroy_popup(self, index) -> bool:  # Remove popup by index with bool for if the popup was in the list
        ...

    def handle_error(self, error: BaseException) -> bool:
        ...


class ActFramework:
    """TBA"""
    class CODES:
        """TBA"""  # Shutdown codes
        RESTART = 1010
        IMMEDIATE_CLOSE = 2020

    def __init__(self, app: _ty.Type[ActApp], argv: list[str], *_,
                 default_storage: _ty.Type[StorageMedium] = StorageMedium):
        if app.name == "ActApp":
            raise RuntimeError("App-Name is unset")
        self._qapp_params, rargv = self._extract_params(argv, "qapp:")
        aa_params, rargv = self._extract_params(rargv, "actapp:")
        self._actapp_params: dict[str, str] = {x.split("=")[0]: x.split("=")[1] for x in aa_params}

        self._qapp: _QApplication = _QApplication(self._qapp_params)
        self._system = _get_system()
        self.app_path: str = self._system.get_appdata_directory(f"ActFrame/{app.name}", "user")
        _os.makedirs(self.app_path, exist_ok=True)
        self._default_storage = default_storage
        self._default_file_ext = {JSONStorage: "json", SQLite3Storage: "db", BinaryStorage: "bin"}.get(default_storage, "file")
        self._persistent_storage = default_storage(_os.path.join(self.app_path, f"config.{self._default_file_ext}"))
        self._persistent_app_storage = default_storage(_os.path.join(self.app_path, f"app_config.{self._default_file_ext}"))

        self.logs_dir: str = _os.path.join(self.app_path + "/logs")
        self._order_logs(self.logs_dir)
        self.logger: ActLogger = ActLogger(log_to_file=True, filename=self.logs_dir + "/latest.log")
        self.logger.setLevel(_logging.DEBUG)
        self.logger.monitor_pipe(_sys.stdout, level=_logging.DEBUG)
        self.logger.monitor_pipe(_sys.stderr, level=_logging.ERROR)

        self._timer = _QTimer()
        self._timer.timeout.connect(self.check_state)
        self._timer.start(int(self._actapp_params.get("check_timer_ms") or 100))

        app.logger = self.logger
        app.set_light_theme_setter = self.set_light_theme_setter
        app.set_dark_theme_setter = self.set_dark_theme_setter
        app._persistent_app_storage = self._persistent_app_storage
        app._framework = self
        app.app_directory = self.app_path
        self._aapp: ActApp = app(rargv)
        self.app_theme = self._system.get_system_theme()
        self.exit_code = None

        self.set_dark_theme_setter("default_dark", lambda: 1)
        self.set_light_theme_setter("default_light", lambda: 1)

    @staticmethod
    def _extract_params(argv: list[str], prefix: str) -> tuple[list[str], list[str]]:
        """
        Extract parameters from the command-line arguments that start with a specific prefix,
        remove the prefix, and split them by ';'. Returns a list of lists.
        """
        params = set()
        remaining_argv = []

        for arg in argv:
            if arg.startswith(prefix):
                param_args = arg.removeprefix(prefix).split(";")
                for param_arg in param_args:
                    params.add(param_arg)
            else:
                remaining_argv.append(arg)
        return list(params), remaining_argv

    @staticmethod
    def _order_logs(directory: str) -> None:
        logs_dir = _PLPath(directory)
        to_log_file = logs_dir / "latest.log"

        if not to_log_file.exists():
            return

        with open(to_log_file, "rb") as f:
            # (solution from https://stackoverflow.com/questions/46258499/how-to-read-the-last-line-of-a-file-in-python)
            first_line = f.readline().decode()
            try:  # catch OSError in case of a one line file
                f.seek(-2, _os.SEEK_END)
                while f.read(1) != b"\n":
                    f.seek(-2, _os.SEEK_CUR)
            except OSError:
                f.seek(0)
            last_line = f.readline().decode()

        try:
            date_pattern = r"^[\[(](\d{4}-\d{2}-\d{2})"
            start_date = _re.search(date_pattern, first_line).group(1)
            end_date = _re.search(date_pattern, last_line).group(1)
        except AttributeError:
            print("Removing malformed latest.log")
            _os.remove(to_log_file)
            return

        date_name = f"{start_date}_{end_date}"
        date_logs = list(logs_dir.rglob(f"{date_name}*.log"))

        if not date_logs:
            new_log_file_name = logs_dir / f"{date_name}.log"
        else:
            max_num = max(
                (int(_re.search(r"#(\d+)$", p.stem).group(1)) for p in date_logs if
                 _re.search(r"#(\d+)$", p.stem)),
                default=0
            )
            max_num += 1
            base_log_file = logs_dir / f"{date_name}.log"
            if base_log_file.exists():
                _os.rename(base_log_file, logs_dir / f"{date_name}#{max_num}.log")
                max_num += 1
            new_log_file_name = logs_dir / f"{date_name}#{max_num}.log"

        _os.rename(to_log_file, new_log_file_name)
        print(f"Renamed latest.log to {new_log_file_name}")

    def set_light_theme_setter(self, theme_name: str, light_theme_setter: _a.Callable) -> None:
        self._persistent_storage.store({"default_light_theme": theme_name})

    def set_dark_theme_setter(self, theme_name: str, dark_theme_setter: _a.Callable) -> None:
        self._persistent_storage.store({"default_dark_theme": theme_name})

    def store_secret(self, name: str, secret: bytes):
        ...  # Using user password, refuse if unset; The secret is stored centrally within the app folder as ./secret.bin

    def retrieve_secret(self, name: str) -> bytes:
        ...  # Using user password, refuse if unset; The secret is stored centrally within the app folder as ./secret.bin

    def check_state(self):
        current_theme = self._system.get_system_theme()  # Check for theme changes
        if current_theme != self.app_theme:
            print("Theme changed")
            self.app_theme = current_theme
            if current_theme == _SystemTheme.LIGHT:
                self._aapp.set_light_mode(self._aapp.window)
                for popup in self._aapp.popups:
                    self._aapp.set_light_mode(popup)
            else:  # SystemTheme.DARK and SystemTheme.UNKNOWN
                self._aapp.set_dark_mode(self._aapp.window)
                for popup in self._aapp.popups:
                    self._aapp.set_dark_mode(popup)

    def start(self) -> int:
        current_exit_code = 1
        try:
            self._aapp.start()
            current_exit_code = self._qapp.exec()
            app_exit_code = self._aapp.exit_code
            match (app_exit_code or current_exit_code):
                case self.CODES.RESTART:
                    _os.execv(_sys.executable, [_sys.executable] + _sys.argv)
                case self.CODES.IMMEDIATE_CLOSE:
                    self.exit_code = 1
                case _:
                    pass
        except Exception as e:  # look if there was any error
            error = _format_exc()
            self.logger.error(error)
            if not self._aapp.handle_error(e):
                self._timer.stop()
                title = "Info"
                text = (f"There was an error while running the app {self._aapp.name}. "
                        f"Please submit the details to our GitHub issues page.")
                description = error
                msg_box = _QQuickMessageBox(None, _QMessageBox.Icon.Warning, title, text, description,
                                            standard_buttons=_QMessageBox.StandardButton.Ok,
                                            default_button=_QMessageBox.StandardButton.Ok)
                msg_box.setWindowIcon(self._aapp.window.windowIcon())
                msg_box.exec()
        self._aapp.stop()
        self.exit_code = current_exit_code
        return current_exit_code

    def force_stop(self):
        self.exit_code = -1
        self._aapp.stop()
        self._qapp.quit()
