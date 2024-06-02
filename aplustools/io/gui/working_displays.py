from PySide6.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QScrollArea, QPushButton,
                               QApplication, QWidget, QSizePolicy, QScrollBar)
from PySide6.QtGui import QPixmap, QPainter, QWheelEvent, QKeyEvent, QPen, QFont, QTextOption
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Slot, QRectF, QByteArray, QObject, Signal
from typing import Literal, List, Optional
from aplustools.web.utils import url_validator
from aplustools.io.gui import QNoSpacingHBoxLayout, QNoSpacingVBoxLayout
import httpx
from concurrent.futures import ThreadPoolExecutor
import time
import os


class QKineticScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super(QKineticScrollArea, self).__init__(parent)
        # self.setVerticalScrollMode(QScrollArea.ScrollPerPixel)
        self.setWidgetResizable(True)
        self.flick_speed = 0
        self.deceleration = 0.90  # Deceleration factor
        self.timer = QTimer(self)
        self.timer.setInterval(20)  # Update interval in milliseconds
        self.timer.timeout.connect(self.performScroll)

    def wheelEvent(self, event):
        angle_delta = event.angleDelta().y()
        steps = angle_delta / 120  # Each step is 15 degrees, convert to scroll steps
        pixel_step = 1  # Pixels to scroll per step
        initial_speed = steps * pixel_step

        # Increase or set the flick speed based on the event
        self.flick_speed += initial_speed
        if not self.timer.isActive():
            self.timer.start()

        event.accept()  # Mark the event as handled

    @Slot()
    def performScroll(self):
        if abs(self.flick_speed) > 1:
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - int(self.flick_speed))
            # Apply deceleration
            self.flick_speed *= self.deceleration
        else:
            self.flick_speed = 0
            self.timer.stop()


class QSmoothScrollingArea(QScrollArea):
    def __init__(self, parent=None, sensitivity: int = 1):
        super().__init__(parent)
        self.setWidgetResizable(True)

        # Scroll animation setup
        self.scroll_animation = QPropertyAnimation(self.verticalScrollBar(), b"value")
        self.scroll_animation.setEasingCurve(QEasingCurve.OutCubic)  # Smoother deceleration
        self.scroll_animation.setDuration(500)  # Duration of the animation in milliseconds

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.sensitivity = sensitivity
        self.toScroll = 0  # Total amount left to scroll

    def change_scrollbar_state(self, scrollbar: Literal["vertical", "horizontal"], state: bool = False):
        state = Qt.ScrollBarPolicy.ScrollBarAsNeeded if state else Qt.ScrollBarPolicy.ScrollBarAlwaysOff

        if scrollbar == "vertical":
            self.setVerticalScrollBarPolicy(state)
        else:
            self.setHorizontalScrollBarPolicy(state)

    def wheelEvent(self, event: QWheelEvent):
        angle_delta = event.angleDelta().y()
        steps = angle_delta / 120
        pixel_step = int(self.verticalScrollBar().singleStep() * self.sensitivity)

        if self.scroll_animation.state() == QPropertyAnimation.Running:
            self.scroll_animation.stop()
            self.toScroll += self.scroll_animation.endValue() - self.verticalScrollBar().value()

        current_value = self.verticalScrollBar().value()
        max_value = self.verticalScrollBar().maximum()
        min_value = self.verticalScrollBar().minimum()

        # Inverted scroll direction calculation
        self.toScroll -= pixel_step * steps
        proposed_value = current_value + self.toScroll  # Reflecting changes

        if proposed_value > max_value and steps > 0:
            self.toScroll = 0
        elif proposed_value < min_value and steps < 0:
            self.toScroll = 0

        new_value = current_value + self.toScroll
        self.scroll_animation.setStartValue(current_value)
        self.scroll_animation.setEndValue(new_value)
        self.scroll_animation.start()
        self.toScroll = 0
        event.accept()


class QAdvancedSmoothScrollingArea(QScrollArea):
    def __init__(self, parent=None, sensitivity: int = 1):
        super().__init__(parent)
        self.setWidgetResizable(True)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

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

        if scrollbar == "vertical":
            self.setVerticalScrollBarPolicy(state)
        else:
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


class QSmoothScrollingGraphicsView(QGraphicsView):
    def __init__(self, parent=None, sensitivity: int = 1):
        super().__init__(parent)

        # Scroll animation setup
        self.scroll_animation = QPropertyAnimation(self.verticalScrollBar(), b"value")
        self.scroll_animation.setEasingCurve(QEasingCurve.OutCubic)  # Smoother deceleration
        self.scroll_animation.setDuration(500)  # Duration of the animation in milliseconds

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.sensitivity = sensitivity
        self.toScroll = 0  # Total amount left to scroll

    def change_scrollbar_state(self, scrollbar: Literal["vertical", "horizontal"], state: bool = False):
        state = Qt.ScrollBarPolicy.ScrollBarAsNeeded if state else Qt.ScrollBarPolicy.ScrollBarAlwaysOff

        if scrollbar == "vertical":
            self.setVerticalScrollBarPolicy(state)
        else:
            self.setHorizontalScrollBarPolicy(state)

    def wheelEvent(self, event: QWheelEvent):
        angle_delta = event.angleDelta().y()
        steps = angle_delta / 120
        pixel_step = int(self.verticalScrollBar().singleStep() * self.sensitivity)

        if self.scroll_animation.state() == QPropertyAnimation.Running:
            self.scroll_animation.stop()
            self.toScroll += self.scroll_animation.endValue() - self.verticalScrollBar().value()

        current_value = self.verticalScrollBar().value()
        max_value = self.verticalScrollBar().maximum()
        min_value = self.verticalScrollBar().minimum()

        # Inverted scroll direction calculation
        self.toScroll -= pixel_step * steps
        proposed_value = current_value + self.toScroll  # Reflecting changes

        if proposed_value > max_value and steps > 0:
            self.toScroll = 0
        elif proposed_value < min_value and steps < 0:
            self.toScroll = 0

        new_value = current_value + self.toScroll
        self.scroll_animation.setStartValue(current_value)
        self.scroll_animation.setEndValue(new_value)
        self.scroll_animation.start()
        self.toScroll = 0
        event.accept()


class QAdvancedSmoothScrollingGraphicsView(QGraphicsView):
    def __init__(self, parent=None, sensitivity: int = 1):
        super().__init__(parent)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

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

    def setPrimaryScrollbar(self, new_primary_scrollbar: Literal["vertical", "horizontal"]):
        self.primary_scrollbar = new_primary_scrollbar

    def setScrollbarState(self, scrollbar: Literal["vertical", "horizontal"], state: bool = False):
        state = Qt.ScrollBarPolicy.ScrollBarAsNeeded if state else Qt.ScrollBarPolicy.ScrollBarAlwaysOff

        if scrollbar == "vertical":
            self.setVerticalScrollBarPolicy(state)
        else:
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


class QScalingGraphicPixmapItem(QGraphicsPixmapItem, QObject):
    pixmapLoaded = Signal(QPixmap)

    def __init__(self, abs_pixmap_path_or_url: str, width_scaling_threshold: float = 0.1,
                 height_scaling_threshold: float = 0.1, lq_resize_count_threshold: int = 1000):
        QGraphicsPixmapItem.__init__(self)
        QObject.__init__(self)
        self.abs_pixmap_path_or_url = os.path.abspath(abs_pixmap_path_or_url) if not (
            url_validator(abs_pixmap_path_or_url)) else abs_pixmap_path_or_url
        self.original_pixmap: QPixmap = None
        self.width_scaling_threshold = max(0.0, min(0.99, width_scaling_threshold))
        self.height_scaling_threshold = max(0.0, min(0.99, height_scaling_threshold))
        self.lower_width_limit = self.upper_width_limit = 0
        self.lower_height_limit = self.upper_height_limit = 0
        self.width: int = None
        self.height: int = None
        self.true_width: float = None
        self.true_height: float = None
        self.int_attr = "width"
        self.lq_resize_count_threshold = lq_resize_count_threshold
        self.lq_resize_count = 0
        self.is_loaded = False
        self.load(True)
        self.reload()

        self.pixmapLoaded.connect(self.setPixmap)

    def load(self, first_load: bool = False):
        if not url_validator(self.abs_pixmap_path_or_url):
            self.original_pixmap = QPixmap(self.abs_pixmap_path_or_url)
        else:
            client = httpx.Client(http2=True)
            response = client.get(self.abs_pixmap_path_or_url)
            if response.status_code == 200:
                image_data = QByteArray(response.content)
                pixmap = QPixmap()
                pixmap.loadFromData(image_data)
                self.original_pixmap = pixmap
            else:
                print('Failed to load image!')
        self.is_loaded = True
        if self.original_pixmap.isNull():
            raise ValueError("Image could not be loaded.")
        if not first_load:
            self.pixmapLoaded.emit(self.original_pixmap.scaled(self.width, self.height))

    def unload(self):
        self.original_pixmap = QPixmap(self.original_pixmap.width(), self.original_pixmap.height())
        self.original_pixmap.fill(Qt.transparent)
        self.pixmapLoaded.emit(self.original_pixmap.scaled(self.width, self.height))
        self.is_loaded = False

    def ensure_loaded(self):
        if not self.is_loaded:
            self.load()

    def ensure_unloaded(self):
        if self.is_loaded:
            self.unload()

    def scale_original_size_to(self, width: Optional[int] = None, height: Optional[int] = None,
                               keep_aspect_ration: bool = False):
        if width:
            aspect_ratio = self.original_height / self.original_width
            return width, int(width * aspect_ratio)
        elif height:
            aspect_ratio = self.original_width / self.original_height
            return int(height * aspect_ratio), height
        elif width and height:
            if keep_aspect_ration:
                if width < height:
                    return self.scale_original_size_to(width=width)
                else:
                    return self.scale_original_size_to(height=height)
            else:
                return width, height

    def get_true_width(self):
        return self.pixmap().width() * self.transform().m11()  # m11() is the horizontal scaling factor

    def get_true_height(self):
        return self.pixmap().height() * self.transform().m22()  # m22() is the vertical scaling factor

    def _true_size(self):
        return self.pixmap().width() * self.transform().m11(), self.pixmap().height() * self.transform().m22()

    def reload(self):
        self.true_width = self.pixmap().width() * self.transform().m11()
        self.true_height = self.pixmap().height() * self.transform().m22()
        self.width = int(self.true_width)
        self.height = int(self.true_height)

    def scaledToWidth(self, width):
        # self.prepareGeometryChange()
        if (width < self.lower_width_limit or width > self.upper_width_limit
                or self.lq_resize_count > self.lq_resize_count_threshold):
            # Use high-quality pixmap scaling when significant downscaling is required
            scaled_pixmap = self.original_pixmap.scaledToWidth(width, Qt.TransformationMode.SmoothTransformation)
            self.setPixmap(scaled_pixmap)
            self.lower_width_limit = width * (1.0 - self.width_scaling_threshold)
            self.upper_width_limit = width * (1.0 + self.width_scaling_threshold)
            self.lq_resize_count = 0
        elif self.get_true_width() != width:
            # Use transformations for minor scaling adjustments
            current_width = self.get_true_width()
            scale_factor = width / current_width
            new_transform = self.transform().scale(scale_factor, scale_factor)
            self.setTransform(new_transform)
            self.lq_resize_count += 1

        # Update width and height based on the transformation
        self.width = self.true_width = width
        self.true_height = self.get_true_height()
        self.height = int(self.true_height)
        # self.update()

    def scaledToHeight(self, height):
        # self.prepareGeometryChange()
        if (height < self.lower_height_limit or height > self.upper_height_limit
                or self.lq_resize_count > self.lq_resize_count_threshold):
            # Use high-quality pixmap scaling when significant downscaling is required
            scaled_pixmap = self.original_pixmap.scaledToHeight(height, Qt.TransformationMode.SmoothTransformation)
            self.setPixmap(scaled_pixmap)
            self.lower_height_limit = height * (1.0 - self.height_scaling_threshold)
            self.upper_height_limit = height * (1.0 + self.height_scaling_threshold)
            self.lq_resize_count = 0
        elif self.get_true_height() != height:
            # Use transformations for minor scaling adjustments
            current_height = self.get_true_height()
            scale_factor = height / current_height
            new_transform = self.transform().scale(scale_factor, scale_factor)
            self.setTransform(new_transform)
            self.lq_resize_count += 1

        # Update width and height based on the transformation
        self.height = self.true_height = height
        self.true_width = self.get_true_width()
        self.width = int(self.true_width)
        # self.update()

    def scaled(self, width, height, keep_aspect_ratio: bool = False):
        # self.prepareGeometryChange()
        # Check if either dimension requires high-quality scaling
        needs_width_scaling = width < self.lower_width_limit or width > self.upper_width_limit
        needs_height_scaling = height < self.lower_height_limit or height > self.upper_height_limit

        if needs_width_scaling or needs_height_scaling or self.lq_resize_count > self.lq_resize_count_threshold:
            # If either dimension is significantly reduced, use high-quality scaling
            aspect_mode = Qt.AspectRatioMode.KeepAspectRatio if keep_aspect_ratio else (
                Qt.AspectRatioMode.IgnoreAspectRatio)

            scaled_pixmap = self.original_pixmap.scaled(width, height, aspect_mode,
                                                        Qt.TransformationMode.SmoothTransformation)
            self.setPixmap(scaled_pixmap)
            self.lower_width_limit = width * (1.0 - self.width_scaling_threshold)
            self.upper_width_limit = width * (1.0 + self.width_scaling_threshold)
            self.lower_height_limit = height * (1.0 - self.height_scaling_threshold)
            self.upper_height_limit = height * (1.0 + self.height_scaling_threshold)
            self.lq_resize_count = 0
        elif self.get_true_width() != width or self.get_true_height() != height:
            # Calculate scale factors for both dimensions
            scale_factor_width = width / self.get_true_width()
            scale_factor_height = height / self.get_true_height()
            if keep_aspect_ratio:
                # Apply the smallest scaling factor to maintain aspect ratio
                scale_factor_width = scale_factor_height = min(scale_factor_width, scale_factor_height)
            new_transform = self.transform().scale(scale_factor_width, scale_factor_height)
            self.setTransform(new_transform)
            self.lq_resize_count += 1

        self.true_width = self.get_true_width()
        self.width = int(self.true_width)
        self.true_height = self.get_true_height()
        self.height = int(self.true_height)
        # self.update()

    def setInt(self, output: Literal["width", "height"]):
        if output in ["width", "height"]:
            self.int_attr = output
        else:
            raise ValueError("Output must be 'width' or 'height'")

    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)

    def paint(self, painter, option, widget):
        if self.is_loaded:
            super().paint(painter, option, widget)
        else:
            rect = self.boundingRect()  # Get the current bounding rectangle
            painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))  # Set the pen for the border
            painter.drawRect(rect)  # Draw the placeholder rectangle

            # Set the painter for drawing text
            painter.setPen(Qt.black)
            painter.setFont(QFont("Arial", 14, QFont.Bold))  # Set font size and style
            text_option = QTextOption(Qt.AlignCenter)  # Align text to center
            painter.drawText(rect, "Image not loaded", text_option)  # Draw the text within the rectangle

    def __int__(self):
        return getattr(self, self.int_attr)

    def __lt__(self, other):
        if not isinstance(other, QScalingGraphicPixmapItem):
            return NotImplemented
        return getattr(self, self.int_attr) < getattr(other, self.int_attr)

    def __le__(self, other):
        if not isinstance(other, QScalingGraphicPixmapItem):
            return NotImplemented
        return getattr(self, self.int_attr) <= getattr(other, self.int_attr)

    def __eq__(self, other):
        if not isinstance(other, QScalingGraphicPixmapItem):
            return NotImplemented
        return getattr(self, self.int_attr) == getattr(other, self.int_attr)

    def __ne__(self, other):
        if not isinstance(other, QScalingGraphicPixmapItem):
            return NotImplemented
        return getattr(self, self.int_attr) != getattr(other, self.int_attr)

    def __gt__(self, other):
        if not isinstance(other, QScalingGraphicPixmapItem):
            return NotImplemented
        return getattr(self, self.int_attr) > getattr(other, self.int_attr)

    def __ge__(self, other):
        if not isinstance(other, QScalingGraphicPixmapItem):
            return NotImplemented
        return getattr(self, self.int_attr) >= getattr(other, self.int_attr)


class QGraphicsScrollView(QWidget):
    def __init__(self, parent=None, sensitivity: int = 1):
        super().__init__(parent)
        # Create a layout for the widget
        layout = QNoSpacingVBoxLayout()
        self.setLayout(layout)

        # Create a QGraphicsView
        self.graphics_view = QAdvancedSmoothScrollingGraphicsView(sensitivity=sensitivity)
        self.graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.graphics_view.setRenderHint(QPainter.Antialiasing)  # Optional, enables anti-aliasing for smoother rendering
        self.graphics_view.setScene(QGraphicsScene())
        self.graphics_view.setStyleSheet("QGraphicsView { border: 0px; }")

        # Set size policy to Ignored to allow resizing freely
        self.graphics_view.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)

        self._v_scrollbar = QScrollBar()
        self._v_scrollbar.setOrientation(Qt.Orientation.Vertical)
        self._v_scrollbar.setVisible(False)

        # Create a layout for the QGraphicsView with additional spacing
        graphics_layout = QNoSpacingHBoxLayout()

        graphics_layout.addWidget(self.graphics_view)
        graphics_layout.addWidget(self._v_scrollbar)
        layout.addLayout(graphics_layout)

        self._h_scrollbar = QScrollBar()
        self._h_scrollbar.setOrientation(Qt.Orientation.Horizontal)
        self._h_scrollbar.setVisible(False)

        self.corner_widget = QWidget()
        self.corner_widget.setAutoFillBackground(True)
        self.corner_widget.setFixedSize(self._v_scrollbar.width(), self._h_scrollbar.height())

        hor_scroll_layout = QNoSpacingHBoxLayout()
        hor_scroll_layout.addWidget(self._h_scrollbar)
        hor_scroll_layout.addWidget(self.corner_widget)

        # Add scrollbar to the layout
        layout.addLayout(hor_scroll_layout)

        # Connect scrollbar value changed signal to update content position
        self._v_scrollbar.valueChanged.connect(self.updateVerticalContentPosition)
        self._h_scrollbar.valueChanged.connect(self.updateHorizontalContentPosition)
        self.graphics_view.verticalScrollBar().valueChanged.connect(self.updateVerticalPosition)
        self.graphics_view.horizontalScrollBar().valueChanged.connect(self.updateHorizontalPosition)

        self._scrollbars_background_redraw = False
        self._vert_scroll_pol = "as"
        self._hor_scroll_pol = "as"
        self.updateScrollbars()

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
        self.updateScrollbars()

    def setHorizontalScrollBarPolicy(self, policy):
        if policy == Qt.ScrollBarPolicy.ScrollBarAsNeeded:
            self._hor_scroll_pol = "as"
        elif policy == Qt.ScrollBarPolicy.ScrollBarAlwaysOff:
            self._hor_scroll_pol = "off"
        else:
            self._hor_scroll_pol = "on"
        self.updateScrollbars()

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

    def updateVerticalContentPosition(self, value):
        # Update the position of the content based on the scrollbar value
        self.graphics_view.verticalScrollBar().setValue(value)

    def updateHorizontalContentPosition(self, value):
        # Update the position of the content based on the scrollbar value
        self.graphics_view.horizontalScrollBar().setValue(value)

    def updateVerticalPosition(self, value):
        # Update the position of the content based on the scrollbar value
        self._v_scrollbar.setValue(value)

    def updateHorizontalPosition(self, value):
        # Update the position of the content based on the scrollbar value
        self._h_scrollbar.setValue(value)

    def updateScrollbarss(self):
        gv_size_hint = self.graphics_view.sizeHint()

        # Check if scrollbars are needed
        if (gv_size_hint.height() > self.height() and self._vert_scroll_pol == "as") or self._vert_scroll_pol == "on":
            self._v_scrollbar.setVisible(True)
            self._v_scrollbar.setPageStep(self.height())
        else:
            self._v_scrollbar.setVisible(False)
        max_v_scroll = max(0, gv_size_hint.height() - self.height())
        self._v_scrollbar.setRange(0, max_v_scroll)

        if (gv_size_hint.width() > self.width() and self._hor_scroll_pol == "as") or self._hor_scroll_pol == "on":
            self._h_scrollbar.setVisible(True)
            self._h_scrollbar.setPageStep(self.width())
        else:
            self._h_scrollbar.setVisible(False)
        max_h_scroll = max(0, gv_size_hint.width() - self.width())
        self._h_scrollbar.setRange(0, max_h_scroll)

        if self._h_scrollbar.isVisible() and self._v_scrollbar.isVisible():
            self.corner_widget.show()
        else:
            self.corner_widget.hide()
        self.corner_widget.setFixedSize(self._v_scrollbar.width(), self._h_scrollbar.height())
        self.updateHorizontalContentPosition(self._v_scrollbar.value())
        self.updateVerticalContentPosition(self._h_scrollbar.value())

        self._v_scrollbar.setRange(0, self.graphics_view.verticalScrollBar().maximum())
        self._h_scrollbar.setRange(0, self.graphics_view.horizontalScrollBar().maximum())

    def updateScrollbars(self):
        vertical_content_size = self.graphics_view.verticalScrollBar().maximum()
        horizontal_content_size = self.graphics_view.horizontalScrollBar().maximum()

        # Check if scrollbars are needed
        if (vertical_content_size > self.height() and self._vert_scroll_pol == "as") or self._vert_scroll_pol == "on":
            self._v_scrollbar.setVisible(True)
            self._v_scrollbar.setPageStep(self.height())
        else:
            self._v_scrollbar.setVisible(False)
        max_v_scroll = max(0, vertical_content_size)
        self._v_scrollbar.setRange(0, max_v_scroll)

        if (horizontal_content_size > self.width() and self._hor_scroll_pol == "as") or self._hor_scroll_pol == "on":
            self._h_scrollbar.setVisible(True)
            self._h_scrollbar.setPageStep(self.width())
        else:
            self._h_scrollbar.setVisible(False)
        max_h_scroll = max(0, horizontal_content_size)
        self._h_scrollbar.setRange(0, max_h_scroll)

        if self._h_scrollbar.isVisible() and self._v_scrollbar.isVisible():
            self.corner_widget.show()
        else:
            self.corner_widget.hide()
        self.corner_widget.setFixedSize(self._v_scrollbar.width(), self._h_scrollbar.height())
        self._v_scrollbar.setValue(self.graphics_view.verticalScrollBar().value())
        self._h_scrollbar.setValue(self.graphics_view.horizontalScrollBar().value())

    def scrollBarsBackgroundRedraw(self, value: bool):
        self._scrollbars_background_redraw = value
        self.corner_widget.setAutoFillBackground(not value)

    def resizeEvent(self, event):
        event_size = event.size()
        if not self._scrollbars_background_redraw:
            event_size.setWidth(event_size.width() - self._v_scrollbar.width())
            event_size.setHeight(event_size.height() - self._h_scrollbar.height())

        # Update scrollbar range and page step
        self.graphics_view.resize(event_size)
        self.updateScrollbars()


class TargetContainer(QGraphicsScrollView):
    def __init__(self, parent=None, sensitivity: int = 1, downscale_images: bool = True, upscale_images: bool = False,
                 base_size: int = 640, use_original_image_size: bool = False, lazy_loading: bool = True):
        super().__init__(parent, sensitivity)
        self.scene = self.graphics_view.scene()
        self.graphics_view.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.resizing = False

        self.timer = QTimer(self)
        self.timer.start(500)
        self.timer.timeout.connect(self.timer_tick)
        self.force_rescaling = False
        QTimer.singleShot(50, self.onScroll)
        QTimer.singleShot(150, self.rescaleImages)

        self._downscale_images = downscale_images
        self._upscale_images = upscale_images
        self._base_size = base_size
        self._use_original_image_size = use_original_image_size
        self.lazy_loading = lazy_loading
        self.management = None

        self.images = []

        self.thread_pool = ThreadPoolExecutor(max_workers=4)

    def setManagement(self, management):
        self.management = management
        self.management.initialize(self)

    @property
    def downscale_images(self):
        return self._downscale_images

    @downscale_images.setter
    def downscale_images(self, downscale_images: bool):
        self._downscale_images = downscale_images
        self.force_rescaling = True

    @property
    def upscale_images(self):
        return self._upscale_images

    @upscale_images.setter
    def upscale_images(self, upscale_images: bool):
        self._upscale_images = upscale_images
        self.force_rescaling = True

    @property
    def base_size(self):
        return self._base_size

    @base_size.setter
    def base_size(self, base_size: int):
        self._base_size = base_size
        self.force_rescaling = True

    @property
    def use_original_image_size(self):
        return self._use_original_image_size

    @use_original_image_size.setter
    def use_original_image_size(self, use_original_image_size: bool):
        self._use_original_image_size = use_original_image_size
        self.force_rescaling = True

    def addImagePath(self, image_path: str):
        image = QScalingGraphicPixmapItem(image_path)
        self.addImageToScene(image)

    # Management methods
    def addImageToScene(self, image: QScalingGraphicPixmapItem):
        self.scene.addItem(image)
        self.images.append(image)
        if self.lazy_loading:
            image.ensure_unloaded()
        self.management.addImageToScene(image, self)

    def rescaleImages(self, event_size=None):
        event_size = event_size or self.graphics_view.viewport().size()
        width = event_size.width()  # self.graphics_view.viewport().width() + self.verticalScrollBar().width()
        height = event_size.height()  # self.graphics_view.viewport().height() + self.horizontalScrollBar().height()
        images = self.images.copy()
        self.management.rescaleImages(width, height, images, self)

    def adjustSceneBounds(self):
        items: List[QScalingGraphicPixmapItem] = self.scene.items()
        self.management.adjustSceneBounds(items, self)

    def onScroll(self):
        images = self.images.copy()
        self.management.onScroll(images, self)

    def keyPressEvent(self, event: QKeyEvent):
        self.management.keyPressEvent(event, self)

    def resizeEvent(self, event):
        self.resizing = self.force_rescaling = True
        self.rescaleImages(event.size())
        self.adjustSceneBounds()
        self.resizing = False
        self.onScroll()
        self.management.resizeEvent(self)
        super().resizeEvent(event)

    # Rest
    def timer_tick(self):
        self.rescaleImages()
        # self.adjustSceneBounds()
        self.onScroll()


class BaseManagement:
    @staticmethod
    def initialize(target):
        pass

    @staticmethod
    def addImageToScene(image, target):
        pass

    @classmethod
    def rescaleImages(cls, width, height, scene_items, target):
        pass

    @staticmethod
    def adjustSceneBounds(items, target):
        pass

    @classmethod
    def onScroll(cls, images, target):
        pass

    @staticmethod
    def resizeEvent(target):
        pass


class HorizontalManagement(BaseManagement):
    @staticmethod
    def initialize(target):
        target.graphics_view.setPrimaryScrollbar("horizontal")

    @staticmethod
    def addImageToScene(image, target):
        image.setInt("height")
        image.scaledToHeight(target.graphics_view.viewport().height())

    @staticmethod
    def _get_wanted_size(target, item: QScalingGraphicPixmapItem, viewport_height: int, last_item: bool = False):
        base_image_height = item.original_pixmap.width() if target.use_original_image_size else target.base_size

        if target.force_rescaling:
            proposed_image_height = base_image_height

            if target.downscale_images and base_image_height > viewport_height:
                proposed_image_height = viewport_height
            elif target.upscale_images and base_image_height < viewport_height:
                proposed_image_height = viewport_height
            if last_item:
                target.force_rescaling = False
            return proposed_image_height
        return item.height

    @classmethod
    def rescaleImages(cls, width, height, images, target):
        total_width = 0
        # images.reverse()
        target.force_rescaling = True
        # height += target.horizontalScrollBar().height()

        for i, item in enumerate(images):
            if isinstance(item, QScalingGraphicPixmapItem):
                wanted_height = cls._get_wanted_size(target, item, height, True if i == len(images) - 1 else False)

                if abs(item.get_true_height() - wanted_height) >= 0.5:
                    # print(item.true_height, "->", wanted_height)
                    item.scaledToHeight(wanted_height)
                    item.setPos(total_width, 0)

                total_width += item.true_width
            # target.scene.update()
            # target.graphics_view.update()

    @staticmethod
    def adjustSceneBounds(items, target):
        if not items:
            return
        width = sum(item.width for item in items if isinstance(item, QGraphicsPixmapItem))
        height = max(items).height
        target.scene.setSceneRect(0, 0, width, height)

    @staticmethod
    def _isVisibleInViewport(target, item: QScalingGraphicPixmapItem):
        # Map item rect to scene coordinates
        item_rect = item.mapToScene(item.boundingRect()).boundingRect()
        # Get the viewport rectangle in scene coordinates
        viewport_rect = target.graphics_view.mapToScene(target.graphics_view.viewport().rect()).boundingRect()

        # Check intersection
        return viewport_rect.intersects(item_rect)

    @classmethod
    def _refine_estimated_index(cls, target, estimated_index, images):
        # Adjust index to ensure it points to a visible image
        for i in range(max(0, estimated_index - 5), min(len(images), estimated_index + 5)):
            if cls._isVisibleInViewport(target, images[i]):
                return i
        return estimated_index

    @classmethod
    def _loadImagesAroundIndex(cls, target, index, images: List[QScalingGraphicPixmapItem]):
        # images.reverse()
        last_loaded = 0
        first_loaded_index = None
        for i, image in enumerate(images):
            if cls._isVisibleInViewport(target, image):
                target.thread_pool.submit(image.ensure_loaded)
                last_loaded = 2
                if first_loaded_index is None:
                    first_loaded_index = i
            elif last_loaded:
                target.thread_pool.submit(image.ensure_loaded)
                last_loaded -= 1
            else:
                target.thread_pool.submit(image.ensure_unloaded)

        # print(first_loaded_index, "->", tuple(i for i in range(max(0, first_loaded_index - 2), first_loaded_index)))

        for i in range(max(0, first_loaded_index - 2), first_loaded_index):
            target.thread_pool.submit(images[i].ensure_loaded)

        return

        images[index].ensure_loaded()
        # Load images in the estimated range
        i = j = 0
        for index, item in enumerate(images[index+1:]):
            if cls._isVisibleInViewport(target, item):
                item.ensure_loaded()
                i = index
            else:
                item.ensure_unloaded()
        for index, item in enumerate(images[:index:-1]):
            if cls._isVisibleInViewport(target, item):
                item.ensure_loaded()
                j = index
            else:
                item.ensure_unloaded()

        buffer_images = 10

        for index in range(index + i + 1, index + i + buffer_images):
            if len(images) > index:
                images[index].ensure_loaded()

        for index in range(index - j - 1, index - j - buffer_images, -1):
            if len(images) > index > 0:
                images[index].ensure_loaded()

    @classmethod
    def onScroll(cls, images, target):
        if target.lazy_loading:
            scrollbar = target.horizontalScrollBar()
            curr_scroll = scrollbar.value()
            max_scroll = scrollbar.maximum()

            if max_scroll == 0:
                return

            # Estimate the index of the potentially visible image
            percentage = curr_scroll / max_scroll
            estimated_index = int((len(images) - 1) * percentage)

            # Refine estimated index based on visibility checks
            estimated_index = cls._refine_estimated_index(target, estimated_index, images)

            # Load images around the refined index
            cls._loadImagesAroundIndex(target, estimated_index, images)

            target.scene.update()
            target.graphics_view.update()
        else:
            for image in images:
                image.ensure_loaded()

    @staticmethod
    def resizeEvent(target):
        pass


class VerticalManagement(BaseManagement):
    @staticmethod
    def initialize(target):
        target.graphics_view.setPrimaryScrollbar("vertical")

    @staticmethod
    def addImageToScene(image, target):
        image.setInt("width")
        image.scaledToWidth(target.graphics_view.viewport().width())

    @staticmethod
    def _get_wanted_size(target, item: QScalingGraphicPixmapItem, viewport_width: int, last_item: bool = False):
        base_image_width = item.original_pixmap.width() if target.use_original_image_size else target.base_size

        if target.force_rescaling:
            proposed_image_width = base_image_width

            if target.downscale_images and base_image_width > viewport_width:
                proposed_image_width = viewport_width
            elif target.upscale_images and base_image_width < viewport_width:
                proposed_image_width = viewport_width
            if last_item:
                target.force_rescaling = False
            return proposed_image_width
        return item.width

    @classmethod
    def rescaleImages(cls, width, height, images, target):
        total_height = 0
        # images.reverse()
        target.force_rescaling = True
        # height += target.horizontalScrollBar().height()

        for i, item in enumerate(images):
            if isinstance(item, QScalingGraphicPixmapItem):
                wanted_width = cls._get_wanted_size(target, item, width, True if i == len(images) - 1 else False)

                if abs(item.get_true_width() - wanted_width) >= 0.5:
                    # print(item.true_width, "->", wanted_width)
                    item.scaledToWidth(wanted_width)
                    item.setPos(0, total_height)

                total_height += item.true_height
            # target.scene.update()
            # target.graphics_view.update()

    @staticmethod
    def adjustSceneBounds(items, target):
        if not items:
            return
        width = max(items).width
        height = sum(item.height for item in items if isinstance(item, QGraphicsPixmapItem))
        target.scene.setSceneRect(0, 0, width, height)

    @staticmethod
    def _isVisibleInViewport(target, item: QScalingGraphicPixmapItem):
        # Map item rect to scene coordinates
        item_rect = item.mapToScene(item.boundingRect()).boundingRect()
        # Get the viewport rectangle in scene coordinates
        viewport_rect = target.graphics_view.mapToScene(target.graphics_view.viewport().rect()).boundingRect()

        # Check intersection
        return viewport_rect.intersects(item_rect)

    @classmethod
    def _refine_estimated_index(cls, target, estimated_index, images):
        # Adjust index to ensure it points to a visible image
        for i in range(max(0, estimated_index - 5), min(len(images), estimated_index + 5)):
            if cls._isVisibleInViewport(target, images[i]):
                return i
        return estimated_index

    @classmethod
    def _loadImagesAroundIndex(cls, target, center_index, images: List[QScalingGraphicPixmapItem]):
        # images.reverse()
        last_loaded = 0
        first_loaded_index = None
        for i, image in enumerate(images):
            if cls._isVisibleInViewport(target, image):
                target.thread_pool.submit(image.ensure_loaded)
                last_loaded = 2
                if first_loaded_index is None:
                    first_loaded_index = i
            elif last_loaded:
                target.thread_pool.submit(image.ensure_loaded)
                last_loaded -= 1
            else:
                target.thread_pool.submit(image.ensure_unloaded)

        # print(first_loaded_index, "->", tuple(i for i in range(max(0, first_loaded_index - 2), first_loaded_index)))

        for i in range(max(0, first_loaded_index - 2), first_loaded_index):
            target.thread_pool.submit(images[i].ensure_loaded)

        return

        # Ensure the current image is loaded
        images[center_index].ensure_loaded()

        # Constants
        num_buffer_images = 2

        # Load visible images forward from center_index and unload the rest
        last_visible_index = center_index
        for i in range(center_index + 1, len(images)):
            if cls._isVisibleInViewport(target, images[i]):
                target.thread_pool.submit(images[i].ensure_loaded)
                last_visible_index = i
            else:
                images[i].ensure_unloaded()
                break

        # Load visible images backward from center_index and unload the rest
        first_visible_index = center_index
        for i in range(center_index - 1, -1, -1):
            if cls._isVisibleInViewport(target, images[i]):
                target.thread_pool.submit(images[i].ensure_loaded)
                first_visible_index = i
            else:
                images[i].ensure_unloaded()
                break

        # Load buffer images after the last visible image
        for i in range(last_visible_index + 1, min(last_visible_index + 1 + num_buffer_images, len(images))):
            target.thread_pool.submit(images[i].ensure_loaded)

        # Load buffer images before the first visible image
        for i in range(first_visible_index - 1, max(first_visible_index - 1 - num_buffer_images, -1), -1):
            target.thread_pool.submit(images[i].ensure_loaded)

    @classmethod
    def onScroll(cls, images, target):
        if target.lazy_loading:
            scrollbar = target.verticalScrollBar()
            curr_scroll = scrollbar.value()
            max_scroll = scrollbar.maximum()

            if max_scroll == 0:
                return

            # Estimate the index of the potentially visible image
            percentage = curr_scroll / max_scroll
            estimated_index = int((len(images) - 1) * percentage)

            # Refine estimated index based on visibility checks
            estimated_index = cls._refine_estimated_index(target, estimated_index, images)

            # Load images around the refined index
            cls._loadImagesAroundIndex(target, estimated_index, images)

            target.scene.update()
            target.graphics_view.update()
        else:
            for image in images:
                image.ensure_loaded()

    @staticmethod
    def resizeEvent(target):
        pass


class SingleHorizontalManagement(BaseManagement):
    @staticmethod
    def initialize(target):
        target.self.setPrimaryScrollbar("horizontal")
        target.currentIndex = 0

    @staticmethod
    def _update_view(target):
        for i, image in enumerate(target.images):
            item.setVisible(i == target.currentIndex)
            if not target.lazy_loading or i == target.currentIndex:
                item.ensure_loaded()
            else:
                item.ensure_unloaded()
        target.rescaleImages()
        target.adjustSceneBounds()

    @classmethod
    def addImageToScene(cls, image, target):
        image.scaledToHeight(target.graphics_view.viewport().height())
        cls._update_view(target)

    @staticmethod
    def _get_wanted_size(target, item: QScalingGraphicPixmapItem, viewport_height: int, last_item: bool = False):
        base_image_height = item.original_pixmap.width() if target.use_original_image_size else target.base_size

        if target.force_rescaling:
            proposed_image_height = base_image_height

            if target.downscale_images and base_image_height > viewport_height:
                proposed_image_height = viewport_height
            elif target.upscale_images and base_image_height < viewport_height:
                proposed_image_height = viewport_height
            if last_item:
                target.force_rescaling = False
            return proposed_image_height
        return item.height

    @classmethod
    def rescaleImages(cls, width, height, scene_items, target):
        if target.images:
            current_image = target.images[self.currentIndex]
        total_width = 0
        scene_items.reverse()
        target.force_rescaling = True
        # height += target.horizontalScrollBar().height()

        for i, item in enumerate(scene_items):
            if isinstance(item, QScalingGraphicPixmapItem):
                wanted_height = cls._get_wanted_size(target, item, height, True if i == len(scene_items) - 1 else False)

                if abs(item.true_height - wanted_height) >= 0.5:
                    # print(item.true_height, "->", wanted_height)
                    item.scaledToHeight(wanted_height)
                    item.setPos(total_width, 0)

                total_width += item.true_width
            # target.scene.update()
            # target.graphics_view.update()

    @staticmethod
    def adjustSceneBounds(items, target):
        if not items:
            return
        width = sum(item.width for item in items if isinstance(item, QGraphicsPixmapItem))
        height = max(items).height
        target.scene.setSceneRect(0, 0, width, height)

    @staticmethod
    def _isVisibleInViewport(target, item: QScalingGraphicPixmapItem):
        # Map item rect to scene coordinates
        item_rect = item.mapToScene(item.boundingRect()).boundingRect()
        # Get the viewport rectangle in scene coordinates
        viewport_rect = target.graphics_view.mapToScene(target.graphics_view.viewport().rect()).boundingRect()

        # Check intersection
        return viewport_rect.intersects(item_rect)

    @classmethod
    def _refine_estimated_index(cls, target, estimated_index, images):
        # Adjust index to ensure it points to a visible image
        for i in range(max(0, estimated_index - 5), min(len(images), estimated_index + 5)):
            if cls._isVisibleInViewport(target, images[i]):
                return i
        return estimated_index

    @classmethod
    def _loadImagesAroundIndex(cls, target, index, images: List[QScalingGraphicPixmapItem]):
        images.reverse()
        last_loaded = 0
        first_loaded_index = None
        for i, image in enumerate(images):
            if cls._isVisibleInViewport(target, image):
                target.thread_pool.submit(image.ensure_loaded)
                last_loaded = 2
                if first_loaded_index is None:
                    first_loaded_index = i
            elif last_loaded:
                target.thread_pool.submit(image.ensure_loaded)
                last_loaded -= 1
            else:
                target.thread_pool.submit(image.ensure_unloaded)

        # print(first_loaded_index, "->", tuple(i for i in range(max(0, first_loaded_index - 2), first_loaded_index)))

        for i in range(max(0, first_loaded_index - 2), first_loaded_index):
            target.thread_pool.submit(images[i].ensure_loaded)

        return

        images[index].ensure_loaded()
        # Load images in the estimated range
        i = j = 0
        for index, item in enumerate(images[index+1:]):
            if cls._isVisibleInViewport(target, item):
                item.ensure_loaded()
                i = index
            else:
                item.ensure_unloaded()
        for index, item in enumerate(images[:index:-1]):
            if cls._isVisibleInViewport(target, item):
                item.ensure_loaded()
                j = index
            else:
                item.ensure_unloaded()

        buffer_images = 10

        for index in range(index + i + 1, index + i + buffer_images):
            if len(images) > index:
                images[index].ensure_loaded()

        for index in range(index - j - 1, index - j - buffer_images, -1):
            if len(images) > index > 0:
                images[index].ensure_loaded()

    @classmethod
    def onScroll(cls, images, target):
        if target.lazy_loading:
            scrollbar = target.horizontalScrollBar()
            curr_scroll = scrollbar.value()
            max_scroll = scrollbar.maximum()

            if max_scroll == 0:
                return

            # Estimate the index of the potentially visible image
            percentage = curr_scroll / max_scroll
            estimated_index = int((len(images) - 1) * percentage)

            # Refine estimated index based on visibility checks
            estimated_index = cls._refine_estimated_index(target, estimated_index, images)

            # Load images around the refined index
            cls._loadImagesAroundIndex(target, estimated_index, images)

            target.scene.update()
            target.graphics_view.update()
        else:
            for image in images:
                image.ensure_loaded()

    @staticmethod
    def resizeEvent(target):
        pass


if __name__ == "__main___":
    from PySide6.QtWidgets import QVBoxLayout, QWidget
    app = QApplication([])

    kinetic_scroll_area = QKineticScrollArea()

    # Create a QVBoxLayout instance
    content_widget = QWidget()
    content_layout = QVBoxLayout()

    # Add some buttons to the content layout
    for i in range(20):
        button = QPushButton(f"Button {i}")
        content_layout.addWidget(button)

    # Set the layout of the content widget
    content_widget.setLayout(content_layout)

    kinetic_scroll_area.setWidget(content_widget)
    # kinetic_scroll_area.show()

    if "vertical" == "vertical":
        vertical_container = HorizontalScrollingContainer()

        # vertical_container.addImageToScene(QScalingGraphicPixmapItem("https://enhance.io/015f/MainAfter.jpg", cache))
        #for image in os.listdir("./images"):
        #    vertical_container.addImageToScene(QScalingGraphicPixmapItem(f"images/{image}"))
        # vertical_container.addImageToScene(QScalingGraphicPixmapItem("https://letsenhance.io/static/8f5e523ee6b2479e26ecc91b9c25261e/1015f/MainAfter.jpg"))

        vertical_container.show()
    else:
        horizontal_container = HorizontalScrollingContainer()

        horizontal_container.addImageToScene(QScalingGraphicPixmapItem("images/003.png"))
        horizontal_container.addImageToScene(QScalingGraphicPixmapItem("images/003.png"))
        horizontal_container.addImageToScene(QScalingGraphicPixmapItem("images/003.png"))

        horizontal_container.show()

    app.exec_()


if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QGraphicsSimpleTextItem
    app = QApplication(sys.argv)
    window = TargetContainer(sensitivity=4)
    window.setManagement(HorizontalManagement)
    window.scrollBarsBackgroundRedraw(True)

    for item in os.listdir("./test_images"):
        test_image = QScalingGraphicPixmapItem(os.path.join("./test_images", item))
        window.addImageToScene(test_image)

    # window.setManagement(VerticalManagement)
    window.show()
    sys.exit(app.exec())

if __name__ == '__main___':
    import sys
    from PySide6.QtWidgets import QGraphicsSimpleTextItem
    app = QApplication(sys.argv)
    window = QGraphicsView()
    window.setScene(QGraphicsScene())
    window.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    window.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    #window = TargetContainer(sensitivity=4)
    #window.setManagement(HorizontalManagement)
    # window.scrollBarsBackgroundRedraw(True)

    total_height = 0
    for item in os.listdir("./test_images"):
        test_image = QScalingGraphicPixmapItem(os.path.join("./test_images", item))
        #window.addImageToScene(test_image)
        window.scene().addItem(test_image)
        test_image.scaledToWidth(1000)
        test_image.setPos(total_height, 0)
        total_height += test_image.true_width
        window.scene().update()
        window.update()

    #window.setManagement(VerticalManagement)
    window.show()
    sys.exit(app.exec())

