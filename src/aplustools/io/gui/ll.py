from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLayout, QScrollBar, QSizePolicy, QApplication, QLabel, QScrollArea
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QWheelEvent, QPixmap
from typing import Literal
import os


class QNoSpacingVBoxLayout(QVBoxLayout):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(0)


class QNoSpacingHBoxLayout(QHBoxLayout):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(0)


class CustomScrollArea(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.layout = QNoSpacingVBoxLayout()
        self.layout.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        self.setLayout(self.layout)

        # Create a content widget that will hold the scrollable content
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_widget.setLayout(self.content_layout)

        # Set the size policy of the content widget to be Ignored
        self.content_widget.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Ignored
        )

        # Set the size policy of the content layout to be Ignored
        self.content_layout.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)

        # Create vertical scrollbar
        self._v_scrollbar = QScrollBar()
        self._v_scrollbar.setOrientation(Qt.Vertical)
        self._v_scrollbar.setVisible(False)

        # Create horizontal scrollbar
        self._h_scrollbar = QScrollBar()
        self._h_scrollbar.setOrientation(Qt.Horizontal)
        self._h_scrollbar.setVisible(False)

        self.corner_widget = QWidget()
        self.corner_widget.setStyleSheet("background: transparent;")
        # self.corner_widget.setAutoFillBackground(True)

        h_scrollbar_layout = QNoSpacingHBoxLayout()
        h_scrollbar_layout.addWidget(self._h_scrollbar)
        h_scrollbar_layout.addWidget(self.corner_widget)
        h_scrollbar_layout.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)

        self.corner_widget.setFixedSize(self._v_scrollbar.width(), self._h_scrollbar.height())

        hbox = QNoSpacingHBoxLayout()
        hbox.addWidget(self.content_widget)
        hbox.addWidget(self._v_scrollbar)
        hbox.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)

        vbox = QNoSpacingVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addLayout(h_scrollbar_layout)
        vbox.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)

        self.layout.addLayout(vbox)

        # Connect scrollbar value changed signal to update content widget position
        self._v_scrollbar.valueChanged.connect(self.updateContentPosition)
        self._h_scrollbar.valueChanged.connect(self.updateContentPosition)

        # self._view = DummyViewport(self.content_widget, self)

        self._vert_scroll_pol = "as"
        self._hor_scroll_pol = "as"

    # def viewport(self):
    #     return self._view

    def setWidgetResizable(self, value: bool):
        return

    def contentWidget(self):
        return self.content_widget

    def verticalScrollBar(self):
        return self._v_scrollbar

    def horizontalScrollBar(self):
        return self._h_scrollbar

    def setVerticalScrollBarPolicy(self, policy):
        if policy == Qt.ScrollBarPolicy.ScrollBarAsNeeded:
            self._vert_scroll_pol = "as"
        elif policy == Qt.ScrollBarPolicy.ScrollBarAlwaysOff:
            self._vert_scroll_pol = "off"
        else:
            self._vert_scroll_pol = "on"
        self.reload_scrollbars()
        self.content_widget.resize(self.content_widget.sizeHint())

    def setHorizontalScrollBarPolicy(self, policy):
        if policy == Qt.ScrollBarPolicy.ScrollBarAsNeeded:
            self._hor_scroll_pol = "as"
        elif policy == Qt.ScrollBarPolicy.ScrollBarAlwaysOff:
            self._hor_scroll_pol = "off"
        else:
            self._hor_scroll_pol = "on"
        self.reload_scrollbars()
        self.content_widget.resize(self.content_widget.sizeHint())

    def verticalScrollBarPolicy(self):
        if self._vert_scroll_pol == "as":
            return Qt.ScrollBarPolicy.ScrollBarAsNeeded
        elif self._vert_scroll_pol == "off":
            return Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        else:
            return Qt.ScrollBarPolicy.ScrollBarAlwaysOn

    def horizontalScrollBarPolicy(self):
        if self._hor_scroll_pol == "as":
            return Qt.ScrollBarPolicy.ScrollBarAsNeeded
        elif self._hor_scroll_pol == "off":
            return Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        else:
            return Qt.ScrollBarPolicy.ScrollBarAlwaysOn

    def updateContentPosition(self, value):
        # Update the position of the content widget based on the scrollbar values
        self.content_widget.move(-self._h_scrollbar.value(), -self._v_scrollbar.value())

    def reload_scrollbars(self):
        # print(self._v_scrollbar.value())
        # print(self._h_scrollbar.value())
        content_size = self.content_widget.sizeHint()
        content_size_2 = self.content_widget.size()

        # Check if scrollbars are needed
        if (content_size.height() > self.height() and self._vert_scroll_pol == "as") or self._vert_scroll_pol == "on":
            self._v_scrollbar.setVisible(True)
            self._v_scrollbar.setPageStep(self.height())
        else:
            self._v_scrollbar.setVisible(False)
        max_v_scroll = max(0, content_size.height() - self.height())
        self._v_scrollbar.setRange(0, max_v_scroll)

        if (content_size_2.width() > self.width() and self._hor_scroll_pol == "as") or self._hor_scroll_pol == "on":
            self._h_scrollbar.setVisible(True)
            self._h_scrollbar.setPageStep(self.width())
        else:
            self._h_scrollbar.setVisible(False)
        max_h_scroll = max(0, content_size_2.width() - self.width())
        self._h_scrollbar.setRange(0, max_h_scroll)

        if self._h_scrollbar.isVisible() and self._v_scrollbar.isVisible():
            self.corner_widget.show()
        else:
            self.corner_widget.hide()
        self.corner_widget.setFixedSize(self._v_scrollbar.width(), self._h_scrollbar.height())
        self.updateContentPosition(0)

    def resizeEvent(self, event):
        # Get the original size of the content widget
        original_content_size = self.content_widget.sizeHint()
        original_content_size.setWidth(event.size().width())

        self.recorded_default_size = original_content_size

        # Resize the content widget to match the original size
        self.content_widget.resize(original_content_size)

        #for widget in [self.content_widget.layout().itemAt(i).widget() for i in range(self.content_widget.layout().count())]:
        #    if hasattr(widget, "pixmap") and widget.pixmap():
        #        widget.resize(widget.pixmap().width(), widget.pixmap().height())

        self.reload_scrollbars()

        event.accept()

    def wheelEvent(self, event):
        # Scroll with the mouse wheel
        delta = event.angleDelta().y()
        self._v_scrollbar.setValue(self._v_scrollbar.value() - delta // 8)


class QAdvancedSmoothScrollingArea(CustomScrollArea):
    def __init__(self, parent=None, sensitivity: int = 1):
        super().__init__(parent)
        # self.setWidgetResizable(True)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.horizontalScrollBar().setSingleStep(24)
        self.verticalScrollBar().setSingleStep(24)

        # Scroll animations for both scrollbars
        self.v_scroll_animation = QPropertyAnimation(self.verticalScrollBar(), b"value")
        self.h_scroll_animation = QPropertyAnimation(self.horizontalScrollBar(), b"value")
        for anim in (self.v_scroll_animation, self.h_scroll_animation):
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.setDuration(500)

        self.sensitivity = sensitivity

        # Scroll accumulators
        self.v_toScroll = 0
        self.h_toScroll = 0

        self.primary_scrollbar = "vertical"

    def set_primary_scrollbar(self, new_primary_scrollbar: Literal["vertical", "horizontal"]):
        self.primary_scrollbar = new_primary_scrollbar

    def change_scrollbar_state(self, scrollbar: Literal["vertical", "horizontal"], state: bool = False):
        state = Qt.ScrollBarPolicy.ScrollBarAsNeeded if state else Qt.ScrollBarPolicy.ScrollBarAlwaysOff

        self.setVerticalScrollBarPolicy(state)
        self.setHorizontalScrollBarPolicy(state)

    def wheelEvent(self, event: QWheelEvent):
        horizontal_event_dict = {
            "scroll_bar": self.horizontalScrollBar(),
            "animation": self.h_scroll_animation,
            "toScroll": self.h_toScroll
        }
        vertical_event_dict = {
            "scroll_bar": self.verticalScrollBar(),
            "animation": self.v_scroll_animation,
            "toScroll": self.v_toScroll
        }

        # Choose scroll bar based on right mouse button state
        if event.buttons() & Qt.MouseButton.RightButton:
            event_dict = horizontal_event_dict if self.primary_scrollbar == "vertical" else vertical_event_dict
        else:
            event_dict = vertical_event_dict if self.primary_scrollbar == "vertical" else horizontal_event_dict

        angle_delta = event.angleDelta().y()
        steps = angle_delta / 120
        pixel_step = int(event_dict.get("scroll_bar").singleStep() * self.sensitivity)

        if event_dict.get("animation").state() == QPropertyAnimation.Running:
            event_dict.get("animation").stop()
            event_dict["toScroll"] += event_dict.get("animation").endValue() - event_dict.get("scroll_bar").value()

        current_value = event_dict.get("scroll_bar").value()
        max_value = event_dict.get("scroll_bar").maximum()
        min_value = event_dict.get("scroll_bar").minimum()

        # Inverted scroll direction calculation
        event_dict["toScroll"] -= pixel_step * steps
        proposed_value = current_value + event_dict["toScroll"]  # Reflecting changes

        if proposed_value > max_value and steps > 0:
            event_dict["toScroll"] = 0
        elif proposed_value < min_value and steps < 0:
            event_dict["toScroll"] = 0

        new_value = current_value + event_dict["toScroll"]
        event_dict.get("animation").setStartValue(current_value)
        event_dict.get("animation").setEndValue(new_value)
        event_dict.get("animation").start()

        event.accept()  # Prevent further processing of the event


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = QAdvancedSmoothScrollingArea()
    window.setWindowTitle('Custom Scroll Area')
    window.setGeometry(100, 100, 300, 200)

    # Add some example content
    for item in os.listdir("_test_images"):
        test_image = QPixmap(os.path.join("_test_images", item))
        label = QLabel()
        label.setPixmap(test_image)
        window.content_layout.addWidget(label)

    window.show()
    sys.exit(app.exec_())

