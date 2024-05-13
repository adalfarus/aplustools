from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QScrollArea, QPushButton, QApplication
from PySide6.QtGui import QPixmap, QPainter, QWheelEvent, QKeyEvent, QPen, QFont, QTextOption
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Slot, QRectF, QByteArray
from typing import Literal, List, Optional
from aplustools.web.utils import url_validator
import httpx
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


class QScalingGraphicPixmapItem(QGraphicsPixmapItem):
    def __init__(self, abs_pixmap_path_or_url: str, width_scaling_threshold: float = 0.1,
                 height_scaling_threshold: float = 0.1, lq_resize_count_threshold: int = 1000):
        super().__init__()
        self.abs_pixmap_path_or_url = os.path.abspath(abs_pixmap_path_or_url) if not (
            url_validator(abs_pixmap_path_or_url)) else abs_pixmap_path_or_url
        self.original_pixmap: QPixmap = None
        self.width_scaling_threshold = max(0.0, min(0.99, width_scaling_threshold))
        self.height_scaling_threshold = max(0.0, min(0.99, height_scaling_threshold))
        self.lower_width_limit = self.upper_width_limit = 0
        self.lower_height_limit = self.upper_height_limit = 0
        self.width: int = None
        self.height: int = None
        self.int_attr = "width"
        self.lq_resize_count_threshold = lq_resize_count_threshold
        self.lq_resize_count = 0
        self.is_loaded = False
        self.load(True)
        self.reload()

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
            pixmap = self.original_pixmap.scaled(self.width, self.height)
            self.setPixmap(pixmap)

    def unload(self):
        self.original_pixmap = QPixmap(self.original_pixmap.width(), self.original_pixmap.height())
        self.original_pixmap.fill(Qt.transparent)
        pixmap = self.original_pixmap.scaled(self.width, self.height)
        self.setPixmap(pixmap)
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

    def true_width(self):
        return self.pixmap().width() * self.transform().m11()  # m11() is the horizontal scaling factor

    def true_height(self):
        return self.pixmap().height() * self.transform().m22()  # m22() is the vertical scaling factor

    def true_size(self):
        return self.pixmap().width() * self.transform().m11(), self.pixmap().height() * self.transform().m22()

    def reload(self):
        self.width = self.pixmap().width() * self.transform().m11()
        self.height = self.pixmap().height() * self.transform().m22()

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
        elif self.true_width() != width:
            # Use transformations for minor scaling adjustments
            current_width = self.true_width()
            scale_factor = width / current_width
            new_transform = self.transform().scale(scale_factor, scale_factor)
            self.setTransform(new_transform)
            self.lq_resize_count += 1

        # Update width and height based on the transformation
        self.width = width
        transformed_height = self.true_height()
        self.height = int(transformed_height)
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
        elif self.true_height() != height:
            # Use transformations for minor scaling adjustments
            current_height = self.true_height()
            scale_factor = height / current_height
            new_transform = self.transform().scale(scale_factor, scale_factor)
            self.setTransform(new_transform)
            self.lq_resize_count += 1

        # Update width and height based on the transformation
        self.height = height
        transformed_width = self.true_width()
        self.width = int(transformed_width)
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
        elif self.true_width() != width or self.true_height() != height:
            # Calculate scale factors for both dimensions
            scale_factor_width = width / self.true_width()
            scale_factor_height = height / self.true_height()
            if keep_aspect_ratio:
                # Apply the smallest scaling factor to maintain aspect ratio
                scale_factor_width = scale_factor_height = min(scale_factor_width, scale_factor_height)
            new_transform = self.transform().scale(scale_factor_width, scale_factor_height)
            self.setTransform(new_transform)
            self.lq_resize_count += 1

        transformed_width = self.true_width()
        self.width = int(transformed_width)
        transformed_height = self.true_height()
        self.height = int(transformed_height)
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


class BaseContainer(QGraphicsView):
    def __init__(self, parent=None, sensitivity: int = 1, downscale_images: bool = True, upscale_images: bool = False):
        super().__init__(parent)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
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
        self.resizing = False

        self.timer = QTimer(self)
        self.timer.start(500)
        self.timer.timeout.connect(self.timer_tick)
        self.force_rescaling = False
        QTimer.singleShot(50, self.onScroll)
        QTimer.singleShot(150, self.rescaleImages)

        self._downscale_images = downscale_images
        self._upscale_images = upscale_images

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

    def setPrimaryScrollbar(self, new_primary_scrollbar: Literal["vertical", "horizontal"]):
        self.primary_scrollbar = new_primary_scrollbar

    def setScrollbarState(self, scrollbar: Literal["vertical", "horizontal"], state: bool = False):
        state = Qt.ScrollBarPolicy.ScrollBarAsNeeded if state else Qt.ScrollBarPolicy.ScrollBarAlwaysOff

        if scrollbar == "vertical":
            self.setVerticalScrollBarPolicy(state)
        else:
            self.setHorizontalScrollBarPolicy(state)

    def addImagePath(self, image_path: str):
        image = QScalingGraphicPixmapItem(image_path)
        self.addImageToScene(image)

    def addImageToScene(self, image: QScalingGraphicPixmapItem):
        self.scene.addItem(image)
        self.rescaleImages()

    def rescaleImages(self):
        width = self.viewport().width()
        height = self.viewport().height()
        for item in self.scene.items():
            if isinstance(item, QGraphicsPixmapItem):
                item.scaled(width, height)

    def adjustSceneBounds(self):
        return

    def onScroll(self):
        pass

    def resizeEvent(self, event):
        self.resizing = self.force_rescaling = True
        super().resizeEvent(event)
        self.rescaleImages()
        self.adjustSceneBounds()
        self.resizing = False

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

    def timer_tick(self):
        self.rescaleImages()
        # self.adjustSceneBounds()
        self.onScroll()


class HorizontalScrollingContainer(BaseContainer):
    def __init__(self, sensitivity: int = 1, downscale_images: bool = True, upscale_images: bool = False,
                 base_height: int = 640, use_original_image_height: bool = False, lazy_loading: bool = True):
        super().__init__(sensitivity=sensitivity, downscale_images=downscale_images, upscale_images=upscale_images)
        self.setPrimaryScrollbar("horizontal")

        self._base_height = base_height
        self._use_original_image_height = use_original_image_height
        self.lazy_loading = lazy_loading

        self.horizontalScrollBar().valueChanged.connect(self.onScroll)

    @property
    def base_height(self):
        return self._base_height

    @base_height.setter
    def base_height(self, base_height: int):
        self._base_height = base_height
        self.force_rescaling = True

    @property
    def use_original_image_height(self):
        return self._use_original_image_height

    @use_original_image_height.setter
    def use_original_image_height(self, use_original_image_height: bool):
        self._use_original_image_height = use_original_image_height
        self.force_rescaling = True

    def addImageToScene(self, image: QScalingGraphicPixmapItem):
        image.setInt("height")
        self.scene.addItem(image)
        image.scaledToHeight(self.viewport().height())

        if self.lazy_loading:
            image.ensure_unloaded()

    def onScroll(self):
        images = self.scene.items()

        if self.lazy_loading:
            scrollbar = self.horizontalScrollBar()
            curr_scroll = scrollbar.value()
            max_scroll = scrollbar.maximum()

            if max_scroll == 0:
                return

            # Estimate the index of the potentially visible image
            percentage = curr_scroll / max_scroll
            estimated_index = int((len(images) - 1) * percentage)

            # Refine estimated index based on visibility checks
            estimated_index = self.refine_estimated_index(estimated_index, images)

            # Load images around the refined index
            self.loadImagesAroundIndex(estimated_index, images)

            self.scene.update()
            self.update()
        else:
            for image in images:
                image.ensure_loaded()

    def refine_estimated_index(self, estimated_index, images):
        # Adjust index to ensure it points to a visible image
        for i in range(max(0, estimated_index - 5), min(len(images), estimated_index + 5)):
            if self.isVisibleInViewport(images[i]):
                return i
        return estimated_index

    def isVisibleInViewport(self, item: QScalingGraphicPixmapItem):
        # Map item rect to scene coordinates
        item_rect = item.mapToScene(item.boundingRect()).boundingRect()
        # Get the viewport rectangle in scene coordinates
        viewport_rect = self.mapToScene(self.viewport().rect()).boundingRect()

        # Check intersection
        return viewport_rect.intersects(item_rect)

    def loadImagesAroundIndex(self, index, images: List[QScalingGraphicPixmapItem]):
        images[index].ensure_loaded()
        # Load images in the estimated range
        for item in images[index+1:]:
            if self.isVisibleInViewport(item):
                item.ensure_loaded()
            else:
                item.ensure_unloaded()
        for item in images[:index:-1]:
            if self.isVisibleInViewport(item):
                item.ensure_loaded()
            else:
                item.ensure_unloaded()

    def get_wanted_size(self, item: QScalingGraphicPixmapItem, viewport_height: int, last_item: bool = False):
        base_image_height = item.original_pixmap.width() if self.use_original_image_height else self.base_height

        if self.force_rescaling:
            proposed_image_height = base_image_height

            if self.downscale_images and base_image_height > viewport_height:
                proposed_image_height = viewport_height
            elif self.upscale_images and base_image_height < viewport_height:
                proposed_image_height = viewport_height
            if last_item:
                self.force_rescaling = False
            return proposed_image_height
        return item.height

    def rescaleImages(self):
        total_width = 0
        viewport_height = self.viewport().height()
        scene_items = self.scene.items().copy()
        scene_items.reverse()
        self.force_rescaling = True

        for i, item in enumerate(scene_items):
            if isinstance(item, QScalingGraphicPixmapItem):
                wanted_height = self.get_wanted_size(item, viewport_height, True if i == len(scene_items) - 1 else False)
                item.scaledToHeight(wanted_height)
                item.setPos(total_width, 0)

                total_width += item.true_width()
            self.scene.update()
            self.update()

    def adjustSceneBounds(self):
        items: List[QScalingGraphicPixmapItem] = self.scene.items()

        if items:
            width = sum(item.width for item in items if isinstance(item, QGraphicsPixmapItem))
            height = max(items).height
            self.scene.setSceneRect(0, 0, width, height)


class VerticalScrollingContainer(BaseContainer):
    def __init__(self, sensitivity: int = 1, downscale_images: bool = True, upscale_images: bool = False,
                 base_width: int = 640, use_original_image_width: bool = False, lazy_loading: bool = True):
        super().__init__(sensitivity=sensitivity, downscale_images=downscale_images, upscale_images=upscale_images)
        self.setPrimaryScrollbar("vertical")

        self._base_width = base_width
        self._use_original_image_width = use_original_image_width
        self.lazy_loading = lazy_loading

        self.verticalScrollBar().valueChanged.connect(self.onScroll)

    @property
    def base_width(self):
        return self._base_width

    @base_width.setter
    def base_width(self, base_width: int):
        self._base_width = base_width
        self.force_rescaling = True

    @property
    def use_original_image_width(self):
        return self._use_original_image_width

    @use_original_image_width.setter
    def use_original_image_width(self, use_original_image_width: bool):
        self._use_original_image_width = use_original_image_width
        self.force_rescaling = True

    def addImageToScene(self, image: QScalingGraphicPixmapItem):
        image.setInt("width")
        self.scene.addItem(image)
        image.scaledToWidth(self.viewport().width())

        if self.lazy_loading:
            image.ensure_unloaded()

    def onScroll(self):
        images = self.scene.items()

        if self.lazy_loading:
            scrollbar = self.verticalScrollBar()
            curr_scroll = scrollbar.value()
            max_scroll = scrollbar.maximum()

            if max_scroll == 0:
                return

            # Estimate the index of the potentially visible image
            percentage = curr_scroll / max_scroll
            estimated_index = int((len(images) - 1) * percentage)

            # Refine estimated index based on visibility checks
            estimated_index = self.refine_estimated_index(estimated_index, images)

            # Load images around the refined index
            self.loadImagesAroundIndex(estimated_index, images)

            self.scene.update()
            self.update()
        else:
            for image in images:
                image.ensure_loaded()

    def refine_estimated_index(self, estimated_index, images):
        # Adjust index to ensure it points to a visible image
        for i in range(max(0, estimated_index - 5), min(len(images), estimated_index + 5)):
            if self.isVisibleInViewport(images[i]):
                return i
        return estimated_index

    def verticalDistanceToViewport(self, item):
        # Map the viewport rectangle to scene coordinates
        viewport_polygon = self.mapToScene(self.viewport().rect())
        viewport_rect = viewport_polygon.boundingRect()

        # Map the item rectangle to scene coordinates
        item_polygon = item.mapToScene(item.boundingRect())
        item_rect = item_polygon.boundingRect()

        # Calculate the vertical distance with direction
        if item_rect.top() > viewport_rect.bottom():
            # Item is below the viewport
            distance = item_rect.top() - viewport_rect.bottom()
        elif item_rect.bottom() < viewport_rect.top():
            # Item is above the viewport
            distance = item_rect.bottom() - viewport_rect.top()
        else:
            # Overlapping or touching
            distance = 0

        return distance

    def isVisibleInViewport(self, item: QScalingGraphicPixmapItem):
        # Map item rect to scene coordinates
        item_rect = item.mapToScene(item.boundingRect()).boundingRect()
        # Get the viewport rectangle in scene coordinates
        viewport_rect = self.mapToScene(self.viewport().rect()).boundingRect()

        # Check intersection
        return viewport_rect.intersects(item_rect)

    def loadImagesAroundIndex(self, index, images: List[QScalingGraphicPixmapItem]):
        images[index].ensure_loaded()
        # Load images in the estimated range
        for item in images[index+1:]:
            if self.isVisibleInViewport(item):
                item.ensure_loaded()
            else:
                item.ensure_unloaded()
        for item in images[:index:-1]:
            if self.isVisibleInViewport(item):
                item.ensure_loaded()
            else:
                item.ensure_unloaded()

    def get_wanted_size(self, item: QScalingGraphicPixmapItem, viewport_width: int, last_item: bool = False):
        base_image_width = item.original_pixmap.width() if self.use_original_image_width else self.base_width

        if self.force_rescaling:
            proposed_image_width = base_image_width

            if self.downscale_images and base_image_width > viewport_width:
                proposed_image_width = viewport_width
            elif self.upscale_images and base_image_width < viewport_width:
                proposed_image_width = viewport_width
            if last_item:
                self.force_rescaling = False
            return proposed_image_width
        return item.width

    def rescaleImages(self):
        total_height = 0
        viewport_width = self.viewport().width()
        scene_items = self.scene.items().copy()
        scene_items.reverse()
        self.force_rescaling = True

        for i, item in enumerate(scene_items):
            if isinstance(item, QScalingGraphicPixmapItem):
                wanted_width = self.get_wanted_size(item, viewport_width, True if i == len(scene_items) - 1 else False)
                item.scaledToWidth(wanted_width)
                item.setPos(0, total_height)

                total_height += item.true_height()
        self.scene.update()
        self.update()

    def adjustSceneBounds(self):
        items: List[QScalingGraphicPixmapItem] = self.scene.items()

        if items:
            width = max(items).width
            height = sum(item.height for item in items if isinstance(item, QGraphicsPixmapItem))
            self.scene.setSceneRect(0, 0, width, height)


class SingleHorizontalContainer(BaseContainer):
    def __init__(self, sensitivity: int = 1, downscale_images: bool = True, upscale_images: bool = False,
                 base_height: int = 640, use_original_image_height: bool = False, lazy_loading: bool = True):
        super().__init__(parent=None, sensitivity=sensitivity)
        self.setPrimaryScrollbar("horizontal")

        self.downscale_images = downscale_images
        self.upscale_images = upscale_images
        self.base_height = base_height
        self.use_original_image_height = use_original_image_height
        self.lazy_loading = lazy_loading

        self.images = []  # List of QScalingGraphicPixmapItems
        self.currentIndex = 0

        # Setup UI for navigation
        self.prevButton = None
        self.nextButton = None
        self.setupNavigationControls()

    def setupNavigationControls(self):
        self.prevButton = QPushButton(parent=self)
        self.nextButton = QPushButton(parent=self)

        self.prevButton.clicked.connect(self.prev_image)
        self.nextButton.clicked.connect(self.next_image)

        # Customize button styles
        self.prevButton.setStyleSheet("QPushButton:disabled { background-color: transparent; }")
        self.nextButton.setStyleSheet("QPushButton:disabled { background-color: transparent; }")

        # Set initial visibility
        self.prevButton.setVisible(True)
        self.nextButton.setVisible(True)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key_Right, Qt.Key_Down):
            self.simulateButtonClick(self.nextButton)
        elif event.key() in (Qt.Key_Left, Qt.Key_Up):
            self.simulateButtonClick(self.prevButton)

    def simulateButtonClick(self, button):
        if button.isEnabled():
            button.setDown(True)  # Simulate the button being pressed down
            QApplication.processEvents()  # Process UI events to update the button appearance
            time.sleep(0.1)
            button.clicked.emit()  # Emit the clicked signal

            button.setDown(False)

    def addImageToScene(self, image_item: QScalingGraphicPixmapItem):
        super().addImageToScene(image_item)
        self.images.append(image_item)
        image_item.scaledToHeight(self.viewport().height())
        if self.lazy_loading:
            image_item.ensure_unloaded()
        self.update_view()

    def next_image(self):
        if self.currentIndex < len(self.images) - 1:
            self.currentIndex += 1
            self.update_view()
            self.horizontalScrollBar().setValue(0)

    def prev_image(self):
        if self.currentIndex > 0:
            self.currentIndex -= 1
            self.update_view()
            self.horizontalScrollBar().setValue(self.images[self.currentIndex].width)

    def update_view(self):
        for i, item in enumerate(self.images):
            item.setVisible(i == self.currentIndex)
            if not self.lazy_loading or i == self.currentIndex:
                item.ensure_loaded()
            else:
                item.ensure_unloaded()
        self.rescaleImages()
        self.adjustSceneBounds()
        self.update_button_states()

    def update_button_states(self):
        # Disable 'Previous' button if at the start
        self.prevButton.setEnabled(self.currentIndex > 0)
        self.prevButton.setText("<" if self.prevButton.isEnabled() else "")

        # Disable 'Next' button if at the end
        self.nextButton.setEnabled(self.currentIndex < len(self.images) - 1)
        self.nextButton.setText(">" if self.nextButton.isEnabled() else "")

    def rescaleImages(self):
        viewport_height = self.viewport().height()

        if self.images:
            current_image = self.images[self.currentIndex]
            if self.use_original_image_height:
                base_height = current_image.original_pixmap.height()
            else:
                base_height = self.base_height

            needs_upscaling = self.upscale_images and current_image.height <= viewport_height
            needs_downscaling = self.downscale_images and current_image.height >= viewport_height

            if needs_upscaling or needs_downscaling:
                current_image.scaledToHeight(viewport_height)
            else:
                current_image.scaledToHeight(base_height)

    def adjustSceneBounds(self):
        if self.images:
            current_image = self.images[self.currentIndex]

            width = current_image.width
            height = current_image.height
            self.scene.setSceneRect(0, 0, width, height)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        button_width = min(35, max(25, self.width() // 8))
        button_height = self.height() - 1

        self.prevButton.setFixedWidth(button_width)
        self.nextButton.setFixedWidth(button_width)
        self.prevButton.setFixedHeight(button_height)
        self.nextButton.setFixedHeight(button_height)

        self.prevButton.move(0, 0)
        self.nextButton.move(self.width() - button_width, 0)


class SingleVerticalContainer(BaseContainer):
    def __init__(self, sensitivity: int = 1, downscale_images: bool = True, upscale_images: bool = False,
                 base_width: int = 640, use_original_image_width: bool = False, lazy_loading: bool = True):
        super().__init__(parent=None, sensitivity=sensitivity)
        self.setPrimaryScrollbar("vertical")

        self.downscale_images = downscale_images
        self.upscale_images = upscale_images
        self.base_width = base_width
        self.use_original_image_width = use_original_image_width
        self.lazy_loading = lazy_loading

        self.images = []  # List of QScalingGraphicPixmapItems
        self.currentIndex = 0

        # Setup UI for navigation
        self.prevButton = None
        self.nextButton = None
        self.setupNavigationControls()

    def setupNavigationControls(self):
        self.prevButton = QPushButton(parent=self)
        self.nextButton = QPushButton(parent=self)

        self.prevButton.clicked.connect(self.prev_image)
        self.nextButton.clicked.connect(self.next_image)

        # Customize button styles
        self.prevButton.setStyleSheet("QPushButton:disabled { background-color: transparent; }")
        self.nextButton.setStyleSheet("QPushButton:disabled { background-color: transparent; }")

        # Set initial visibility
        self.prevButton.setVisible(True)
        self.nextButton.setVisible(True)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key_Right, Qt.Key_Down):
            self.simulateButtonClick(self.nextButton)
        elif event.key() in (Qt.Key_Left, Qt.Key_Up):
            self.simulateButtonClick(self.prevButton)

    def simulateButtonClick(self, button):
        if button.isEnabled():
            button.setDown(True)  # Simulate the button being pressed down
            QApplication.processEvents()  # Process UI events to update the button appearance
            time.sleep(0.1)
            button.clicked.emit()  # Emit the clicked signal

            button.setDown(False)

    def addImageToScene(self, image_item: QScalingGraphicPixmapItem):
        super().addImageToScene(image_item)
        self.images.append(image_item)
        image_item.scaledToWidth(self.viewport().width())
        if self.lazy_loading:
            image_item.ensure_unloaded()
        self.update_view()

    def next_image(self):
        if self.currentIndex < len(self.images) - 1:
            self.currentIndex += 1
            self.update_view()
            self.verticalScrollBar().setValue(0)

    def prev_image(self):
        if self.currentIndex > 0:
            self.currentIndex -= 1
            self.update_view()
            self.verticalScrollBar().setValue(self.images[self.currentIndex].height)

    def update_view(self):
        for i, item in enumerate(self.images):
            item.setVisible(i == self.currentIndex)
            if not self.lazy_loading or i == self.currentIndex:
                item.ensure_loaded()
            else:
                item.ensure_unloaded()
        self.rescaleImages()
        self.adjustSceneBounds()
        self.update_button_states()

    def update_button_states(self):
        # Disable 'Previous' button if at the start
        self.prevButton.setEnabled(self.currentIndex > 0)
        self.prevButton.setText("▲" if self.prevButton.isEnabled() else "")

        # Disable 'Next' button if at the end
        self.nextButton.setEnabled(self.currentIndex < len(self.images) - 1)
        self.nextButton.setText("▼" if self.nextButton.isEnabled() else "")

    def rescaleImages(self):
        viewport_width = self.viewport().width()

        if self.images:
            current_image = self.images[self.currentIndex]
            if self.use_original_image_width:
                base_width = current_image.original_pixmap.width()
            else:
                base_width = self.base_width

            needs_upscaling = self.upscale_images and current_image.width <= viewport_width
            needs_downscaling = self.downscale_images and current_image.width >= viewport_width

            if needs_upscaling or needs_downscaling:
                current_image.scaledToWidth(viewport_width)
            else:
                current_image.scaledToWidth(base_width)

    def adjustSceneBounds(self):
        if self.images:
            current_image = self.images[self.currentIndex]

            width = current_image.width
            height = current_image.height
            self.scene.setSceneRect(0, 0, width, height)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        button_width = self.width() - 1
        button_height = min(35, max(25, self.width() // 8))

        self.prevButton.setFixedWidth(button_width)
        self.nextButton.setFixedWidth(button_width)
        self.prevButton.setFixedHeight(button_height)
        self.nextButton.setFixedHeight(button_height)

        self.prevButton.move(0, 0)
        self.nextButton.move(0, self.height() - button_height)


if __name__ == "__main__":
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
        for image in os.listdir("./images"):
            vertical_container.addImageToScene(QScalingGraphicPixmapItem(f"images/{image}"))
        # vertical_container.addImageToScene(QScalingGraphicPixmapItem("https://letsenhance.io/static/8f5e523ee6b2479e26ecc91b9c25261e/1015f/MainAfter.jpg"))

        vertical_container.show()
    else:
        horizontal_container = HorizontalScrollingContainer()

        horizontal_container.addImageToScene(QScalingGraphicPixmapItem("images/003.png"))
        horizontal_container.addImageToScene(QScalingGraphicPixmapItem("images/003.png"))
        horizontal_container.addImageToScene(QScalingGraphicPixmapItem("images/003.png"))

        horizontal_container.show()

    app.exec_()
