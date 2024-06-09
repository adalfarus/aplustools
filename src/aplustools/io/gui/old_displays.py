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