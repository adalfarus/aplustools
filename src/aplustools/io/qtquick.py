"""TBA"""  # Qt done quick

from ..package import enforce_hard_deps as _enforce_hard_deps

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

__deps__: list[str] = []
__hard_deps__: list[str] = ["PySide6>=6.7.0"]
_enforce_hard_deps(__hard_deps__, __name__)

from PySide6.QtWidgets import (QMessageBox as _QMessageBox, QCheckBox as _QCheckBox, QBoxLayout as _QBoxLayout,
                               QWidget as _QWidget, QLayout as _QLayout)
from PySide6.QtCore import Qt as _Qt, QTimer as _QTimer, QObject as _QObject, Signal as _Signal


MBoxIcon = _QMessageBox.Icon
MBoxButton = _QMessageBox.StandardButton


class QQuickMessageBox(_QMessageBox):
    """TBA"""
    def __init__(self, parent=None, icon: MBoxIcon | None = None, window_title: str = "", text: str = "",
                 detailed_text: str = "", checkbox: _QCheckBox | None = None,
                 standard_buttons: MBoxButton | None = MBoxButton.Ok,
                 default_button: MBoxButton | None = None):
        """
        An advanced QMessageBox with additional configuration options.

        :param parent: The parent widget.
        :param icon: The icon to display.
        :param window_title: The title of the message box window.
        :param text: The text to display.
        :param detailed_text: The detailed text to display.
        :param checkbox: A QCheckBox instance.
        :param standard_buttons: The standard buttons to include.
        :param default_button: The default button.
        """
        super().__init__(parent)
        for arg, func in zip([standard_buttons, icon, window_title, text, detailed_text, checkbox, default_button],
                             ["setStandardButtons", "setIcon", "setWindowTitle", "setText", "setDetailedText",
                              "setCheckBox", "setDefaultButton"]):
            if arg:
                getattr(self, func)(arg)

        # Set the window to stay on top initially
        self.setWindowState(self.windowState() & ~_Qt.WindowState.WindowMaximized)

        self.raise_()
        self.activateWindow()


QBoxDirection = _QBoxLayout.Direction


class QQuickBoxLayout(_QBoxLayout):
    """TBA"""
    def __init__(self, direction: _QBoxLayout.Direction, spacing: int = 9,
                 margins: tuple[int, int, int, int] = (9, 9, 9, 9), *contents: _QLayout | _QWidget,
                 apply_layout_to: _QWidget | None = None, parent: _QWidget | None = None):
        super().__init__(direction, parent)
        self.setContentsMargins(*margins)
        self.setSpacing(spacing)

        for content in contents:
            if isinstance(content, _QLayout):
                self.addLayout(content)
            elif isinstance(content, _QWidget):
                self.addWidget(content)

        if apply_layout_to is not None:
            apply_layout_to.setLayout(self)


class QNoSpacingBoxLayout(QQuickBoxLayout):
    """TBA"""
    def __init__(self, direction: _QBoxLayout.Direction, *contents: _QLayout | _QWidget,
                 apply_layout_to: _QWidget | None = None, parent: _QWidget | None = None):
        super().__init__(direction, 0, (0, 0, 0, 0), *contents,
                         apply_layout_to=apply_layout_to, parent=parent)


class QtTimidTimer(_QObject):
    """
    A Qt-based version of TimidTimer using QTimer for seamless integration with the Qt event loop.
    """
    timeout = _Signal(int)  # Signal emitted on timeout, with index of timer.

    def __init__(self, parent: _QWidget | None = None) -> None:
        super().__init__(parent)
        self._timers: dict[int, _QTimer | None] = {}  # dict of active timers

    def start(self, interval_ms: int, index: int = None):
        """
        Start a timer with the given interval.

        Args:
            interval_ms (int): Timer interval in milliseconds.
            index (int): Optional index to identify the timer.
        """
        timer = _QTimer(self)
        timer.setInterval(interval_ms)
        timer.setSingleShot(False)
        timer.timeout.connect(lambda: self._on_timeout(index if index is not None else len(self._timers)))
        self._timers[index] = timer
        timer.start()

    def stop(self, index: int):
        """
        Stop a timer by its index.

        Args:
            index (int): The index of the timer to stop.
        """
        if index in self._timers:
            self._timers[index].stop()
            self._timers[index].deleteLater()
            self._timers[index] = None
        else:
            raise Exception("Invalid index")

    def _on_timeout(self, index: int):
        """
        Internal method called when a timer times out.

        Args:
            index (int): The index of the timer that timed out.
        """
        self.timeout.emit(index)  # Emit signal with the timer index.

    def stop_all(self):
        """
        Stop all active timers.
        """
        for timer in self._timers.values():
            if timer is not None:
                timer.stop()
                timer.deleteLater()
        self._timers.clear()

    def is_active(self, index: int) -> bool:
        """
        Check if a specific timer is active.

        Args:
            index (int): The index of the timer.

        Returns:
            bool: True if the timer is active, False otherwise.
        """
        return index in self._timers and self._timers[index] is not None and self._timers[index].isActive()
