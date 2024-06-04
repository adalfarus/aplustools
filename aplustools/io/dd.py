import sys
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QComboBox
from PySide6.QtGui import QIcon, QGuiApplication, QColor
from PySide6.QtCore import QTimer, QEasingCurve, QPropertyAnimation, Qt, QRect, QPoint
from aplustools.io.gui import QNoSpacingHBoxLayout

class BalloonTip(QWidget):
    def __init__(self, title, message, inputs=None, selections=None, buttons=None, click_callback=None):
        super().__init__()
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self.click_callback = click_callback
        self.mouse_press_pos = None
        self.mouse_move_threshold = 5  # pixels

        # Background widget
        self.background = QWidget(self)
        self.background.setObjectName("background")
        self.background.setGeometry(0, 0, 300, 300)
        self.background.setStyleSheet("""
            QWidget#background {
                background-color: white;
                border: 2px solid black;
                border-radius: 10px;
            }
        """)
        self.background.mousePressEvent = self.handle_mouse_press
        self.background.mouseReleaseEvent = self.handle_mouse_release
        self.background.mouseMoveEvent = self.handle_mouse_move

        # Layout for the content
        self.layout = QVBoxLayout(self.background)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # Display the title
        title_layout = QNoSpacingHBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 16px; color: black;")
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()

        # Close button
        self.close_button = QPushButton("X", self.background)
        self.close_button.setFixedSize(30, 30)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent; 
                color: black; 
                border: none; 
                font-size: 16px;
            }
            QPushButton:hover {
                color: red;
            }
        """)
        self.close_button.clicked.connect(self.close_with_animation)
        title_layout.addWidget(self.close_button, alignment=Qt.AlignRight)
        self.layout.addLayout(title_layout)

        # Display the message
        self.message_label = QLabel(message)
        self.message_label.setStyleSheet("font-size: 14px; color: black;")
        self.layout.addWidget(self.message_label)

        self.inputs = {}
        self.selections = {}

        # Add input fields
        if inputs:
            for input_name, input_display, input_hint in inputs:
                input_field = QLineEdit(self.background)
                input_field.setPlaceholderText(input_hint)
                input_field.setStyleSheet("font-size: 14px; color: black; height: 30px;")
                self.layout.addWidget(QLabel(input_display, self.background))
                self.layout.addWidget(input_field)
                self.inputs[input_name] = input_field

        # Add selection boxes
        if selections:
            for selection_name, selection_display, selection_options, default_selection_id in selections:
                selection_box = QComboBox(self.background)
                selection_box.setStyleSheet("font-size: 14px; color: black; height: 30px;")
                for option_name, option_display in selection_options:
                    selection_box.addItem(option_display, option_name)
                selection_box.setCurrentIndex(default_selection_id)
                self.layout.addWidget(QLabel(selection_display, self.background))
                self.layout.addWidget(selection_box)
                self.selections[selection_name] = selection_box

        # Add buttons
        self.button_callbacks = []
        if buttons:
            for button_text, callback in buttons:
                button = QPushButton(button_text, self.background)
                button.setStyleSheet("font-size: 14px; color: black; height: 40px;")
                self.layout.addWidget(button)
                button.clicked.connect(self.create_button_callback(callback))
                self.button_callbacks.append(callback)

        # Animation setup
        self.show_animation = QPropertyAnimation(self, b"geometry")
        self.show_animation.setDuration(1000)
        self.show_animation.setEasingCurve(QEasingCurve.InOutQuad)

        self.close_animation = QPropertyAnimation(self, b"geometry")
        self.close_animation.setDuration(1000)
        self.close_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.close_animation.finished.connect(self.close)

        # Visual indication animations
        self.shrink_animation = QPropertyAnimation(self.background, b"geometry")
        self.shrink_animation.setDuration(200)
        self.shrink_animation.setEasingCurve(QEasingCurve.InOutQuad)

        self.darkening_effect = self.background.graphicsEffect()

        # Position the notification
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        notification_height = self.background.geometry().height()
        notification_width = self.background.geometry().width()
        self.start_rect = QRect(screen_geometry.width() - notification_width - 10, screen_geometry.height() + 60, notification_width, notification_height)
        self.end_rect = QRect(screen_geometry.width() - notification_width - 10, screen_geometry.height() - notification_height - 10, notification_width, notification_height)
        self.setGeometry(self.start_rect)

        # Display the notification
        self.show()
        self.animate_show()

    def animate_show(self):
        self.show_animation.setStartValue(self.start_rect)
        self.show_animation.setEndValue(self.end_rect)
        self.show_animation.start()

    def close_with_animation(self):
        self.close_animation.setStartValue(self.end_rect)
        self.close_animation.setEndValue(self.start_rect)
        self.close_animation.start()

    def handle_mouse_press(self, event):
        self.mouse_press_pos = event.globalPosition().toPoint()
        # Start shrinking and darkening animations
        shrink_end_rect = QRect(self.background.geometry().adjusted(5, 5, -5, -5))
        self.shrink_animation.setStartValue(self.background.geometry())
        self.shrink_animation.setEndValue(shrink_end_rect)
        self.shrink_animation.start()

        self.background.setStyleSheet("""
            QWidget#background {
                background-color: #d3d3d3;
                border: 2px solid black;
                border-radius: 10px;
            }
        """)

    def handle_mouse_release(self, event):
        if self.mouse_press_pos:
            delta = (event.globalPosition().toPoint() - self.mouse_press_pos).manhattanLength()
            if delta < self.mouse_move_threshold:
                if self.click_callback:
                    input_values = {name: field.text() for name, field in self.inputs.items()}
                    selection_values = {name: box.currentData() for name, box in self.selections.items()}
                    self.click_callback(inputs=input_values, selections=selection_values)
                self.close_with_animation()
            else:
                self.reset_visual_indicators()
            self.mouse_press_pos = None

    def handle_mouse_move(self, event):
        pass  # Placeholder for potential drag handling

    def reset_visual_indicators(self):
        self.shrink_animation.setStartValue(self.background.geometry())
        self.shrink_animation.setEndValue(QRect(0, 0, 300, 300))
        self.shrink_animation.start()

        self.background.setStyleSheet("""
            QWidget#background {
                background-color: white;
                border: 2px solid black;
                border-radius: 10px;
            }
        """)

    def create_button_callback(self, callback):
        def wrapped_callback():
            callback()
            if self.click_callback:
                input_values = {name: field.text() for name, field in self.inputs.items()}
                selection_values = {name: box.currentData() for name, box in self.selections.items()}
                self.click_callback(inputs=input_values, selections=selection_values)

            self.close_with_animation()
        return wrapped_callback

class NotificationSystem(QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        super().__init__(icon, parent)
        self.setToolTip('Notification System')
        self.menu = QMenu(parent)
        self.setContextMenu(self.menu)

    def show_notification(self, title, message, inputs=None, selections=None, buttons=None, click_callback=None):
        self.notification_widget = BalloonTip(title, message, inputs, selections, buttons, click_callback)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Create and display the notification system tray icon
    trayIcon = QIcon("path_to_icon.png")
    notification_system = NotificationSystem(trayIcon)
    notification_system.show()

    # Show a sample notification with inputs, selections, buttons, and click callback
    inputs = [("name", "Name", "Enter your name")]
    selections = [("choice", "Choice", [("option1", "Option 1"), ("option2", "Option 2")], 0)]
    buttons = [("OK", lambda: print("OK clicked")), ("Cancel", lambda: print("Cancel clicked"))]

    notification_system.show_notification(
        "Sample Notification",
        "This is a sample notification message.",
        inputs=inputs,
        selections=selections,
        buttons=buttons,
        click_callback=lambda inputs, selections: print(f"Clicked with inputs: {inputs}, selections: {selections}")
    )

    sys.exit(app.exec())
