"""TBA"""  # Qt done quick

from ..package import enforce_hard_deps as _enforce_hard_deps

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

__deps__ = []
__hard_deps__ = ["PySide6>=6.7.0"]
_enforce_hard_deps(__hard_deps__, __name__)

from PySide6.QtWidgets import (QMessageBox as _QMessageBox, QCheckBox as _QCheckBox, QBoxLayout as _QBoxLayout,
                               QWidget as _QWidget, QLayout as _QLayout)
from PySide6.QtCore import Qt as _Qt


MBoxIcon = _QMessageBox.Icon
MBoxButton = _QMessageBox.StandardButton


class QQuickMessageBox(_QMessageBox):
    """TBA"""
    def __init__(self, parent=None, icon: MBoxIcon | None = None, window_title: str = "", text: str = "",
                 detailed_text: str = "", checkbox: _QCheckBox | None = None,
                 standard_buttons: list[MBoxButton] | MBoxButton = MBoxButton.Ok,
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
        self.setStandardButtons(standard_buttons)
        for arg, func in zip([icon, window_title, text, detailed_text, checkbox, default_button],
                             ["setIcon", "setWindowTitle", "setText", "setDetailedText", "setCheckBox", "setDefaultButton"]):
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

