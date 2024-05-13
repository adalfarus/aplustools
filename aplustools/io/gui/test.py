import sys
from PyQt5.QtWidgets import (QApplication, QGraphicsView, QGraphicsScene, QVBoxLayout, QWidget, QSpacerItem,
                             QSizePolicy, QPushButton, QHBoxLayout, QGraphicsOpacityEffect)
from PyQt5.QtCore import Qt, QPropertyAnimation


class ChapterNavigation(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.prev_button = QPushButton("Previous Chapter")
        self.next_button = QPushButton("Next Chapter")

        layout = QHBoxLayout(self)
        print(layout.spacing(), layout.contentsMargins().left(), layout.contentsMargins().right(), layout.contentsMargins().bottom(), layout.contentsMargins().top())
        layout.addWidget(self.prev_button)
        layout.addWidget(self.next_button)
        self.setLayout(layout)

        # Setup fade effects for visibility
        self.prev_button.setGraphicsEffect(QGraphicsOpacityEffect(self))
        self.next_button.setGraphicsEffect(QGraphicsOpacityEffect(self))
        self.prev_button.graphicsEffect().setOpacity(0)
        self.next_button.graphicsEffect().setOpacity(0)

    def fade_in_buttons(self):
        # Fade in animation for both buttons
        fade_in_anim = QPropertyAnimation(self.prev_button.graphicsEffect(), b"opacity")
        fade_in_anim.setDuration(500)
        fade_in_anim.setStartValue(0)
        fade_in_anim.setEndValue(1)
        fade_in_anim.start()

        fade_in_anim = QPropertyAnimation(self.next_button.graphicsEffect(), b"opacity")
        fade_in_anim.setDuration(500)
        fade_in_anim.setStartValue(0)
        fade_in_anim.setEndValue(1)
        fade_in_anim.start()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle('Chapter Navigation Test')
        self.setup_ui()

    def setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)

        # Graphics view setup
        self.view = QGraphicsView()
        scene = QGraphicsScene()
        self.view.setScene(scene)
        scene.setSceneRect(0, 0, 1000, 1000)  # Arbitrary size

        # Chapter navigation setup
        self.chapter_nav = ChapterNavigation(self)

        # Adding widgets to the layout
        main_layout.addWidget(self.view)

        # Spacer item
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        main_layout.addSpacerItem(spacer)

        # Add chapter navigation
        main_layout.addWidget(self.chapter_nav)

        # Simulating end of chapter
        self.chapter_nav.fade_in_buttons()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
