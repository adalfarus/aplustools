import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QLineEdit, QGraphicsView, QGraphicsScene, QGraphicsEllipseItem
from PySide6.QtGui import QMovie, QColor, QBrush
from PySide6.QtCore import QTimer, Qt

class SystemTheme:
    LIGHT = "light"
    DARK = "dark"

class StdTheme:
    DEFAULT_MODERN_LIGHT = {
        "text_color": "#000000",
        "background_color": "#fbfbfb",
        "selection_background_color": "#f2f2f2",
        "border_color": "#808080",
        "general_background_color": "#f3f3f3",
        "disabled_color": "#7f7f7f",
        "disabled_background_color": "#e0e0e0",
        "opposite_color": "#ffffff",
        "button_background_color": "#f0f0f0",
        "button_hover_background_color": "#e0e0e0",
        "input_background_color": "#ffffff",
        "input_hover_background_color": "#f2f2f2",
        "dropdown_background_color": "#ffffff",
        "label_color": "#000000"
    }

_default_base_stylesheet = """
QPushButton {{
    font-size: 14px;
    color: {text_color};
    height: 40px;
    background-color: {button_background_color};
    border-radius: 5px;
}}
QPushButton:hover {{
    background-color: {button_hover_background_color};
}}
QComboBox {{
    font-size: 14px;
    color: {text_color};
    height: 30px;
}}
QComboBox QAbstractItemView {{
    border: 1px solid {border_color};
    background-color: {dropdown_background_color};
    border-radius: 5px;
    margin-top: -5px;
}}
QLineEdit {{
    font-size: 14px;
    color: {text_color};
    background-color: {input_background_color};
    height: 30px;
}}
QLineEdit:hover {{
    background-color: {input_hover_background_color};
}}
QLabel {{
    font-size: 14px;
    color: {label_color};
}}
QWidget#background {{
    background-color: {background_color};
    border: 2px solid {border_color};
    border-radius: 10px;
}}
"""

class ParticleSystem(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.add_particle)
        self.timer.start(100)

    def add_particle(self):
        particle = QGraphicsEllipseItem(0, 0, 10, 10)
        particle.setBrush(QBrush(QColor(255, 0, 0)))
        particle.setPos(self.scene.width() / 2, self.scene.height() / 2)
        self.scene.addItem(particle)
        # You would typically animate the particle here

class MainWindow(QMainWindow):
    def __init__(self, theme):
        super().__init__()
        self.theme = theme

        self._current_style_sheet = _default_base_stylesheet.format(**self.theme)
        self.setStyleSheet(self._current_style_sheet)

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        self.background_label = QLabel()
        self.set_background_animation("path/to/your/animated/background.gif")

        self.particle_system = ParticleSystem()

        button = QPushButton("Button")
        selection_box = QComboBox()
        selection_box.addItems(["Option 1", "Option 2"])
        input_field = QLineEdit("Input")
        self.message_label = QLabel("Message")
        background = QWidget()
        background.setObjectName("background")

        layout.addWidget(self.background_label)
        layout.addWidget(button)
        layout.addWidget(selection_box)
        layout.addWidget(input_field)
        layout.addWidget(self.message_label)
        layout.addWidget(self.particle_system)
        layout.addWidget(background)

        self.setCentralWidget(central_widget)

    def set_background_animation(self, file_path):
        self.movie = QMovie(file_path)
        self.background_label.setMovie(self.movie)
        self.movie.start()

if __name__ == "__main__":
    app = QApplication([])

    selected_theme = StdTheme.DEFAULT_MODERN_LIGHT
    window = MainWindow(selected_theme)
    window.show()

    sys.exit(app.exec())
