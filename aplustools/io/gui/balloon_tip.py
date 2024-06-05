import os.path

from PySide6.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QWidget, QVBoxLayout, QLabel, QPushButton,
                               QLineEdit, QComboBox, QSizePolicy, QScrollArea)
from PySide6.QtCore import QTimer, QEasingCurve, QPropertyAnimation, Qt, QRect, QCoreApplication
from aplustools.io.gui import QNoSpacingHBoxLayout, UserActivityTracker
from aplustools.io.environment import System, Theme
from PySide6.QtGui import QIcon, QGuiApplication
import threading
import time
import sys


class BalloonTip(QWidget):
    FIXED_WIDTH = 300
    MAX_HEIGHT = 300

    def __init__(self, icon: QIcon, big_icon: QIcon, title, message, inputs=None, selections=None, buttons=None,
                 click_callback=None, auto_close_duration=5000):
        super().__init__()  # Add progress indicators (we will keep it open until the progress bars are done or a BOOL was send through the Qt signal it comes with)
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.click_callback = click_callback
        self.mouse_press_pos = None
        self.mouse_move_threshold = 3  # pixels

        self.theme = System.system().theme

        # Background widget
        self.background = QWidget(self)
        self.background.setObjectName("background")
        self.background.setStyleSheet(f"""
            QWidget#background {{
                background-color: {"white" if self.theme == Theme.LIGHT else "#222222"};
                border: 2px solid black;
                border-radius: 10px;
            }}
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
        title_layout.setSpacing(10)
        title_layout.setContentsMargins(5, 0, 5, 0)
        if not icon.isNull():
            icon_label = QLabel()
            icon_label.setPixmap(icon.pixmap(16, 16))
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title_layout.addWidget(icon_label)
            title_layout.addStretch()
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(
            f"font-weight: bold; font-size: 16px; color: {"black" if self.theme == Theme.LIGHT else "white"};")
        title_layout.addWidget(self.title_label)
        title_layout.addStretch(2)

        # Close button
        self.close_button = QPushButton("X", self.background)
        self.close_button.setFixedSize(30, 30)
        self.close_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent; 
                color: {"black" if self.theme == Theme.LIGHT else "white"}; 
                border: none; 
                font-size: 16px;
            }}
            QPushButton:hover {{
                color: red;
            }}
        """)
        self.close_button.clicked.connect(self.close_with_animation)
        title_layout.addWidget(self.close_button, alignment=Qt.AlignmentFlag.AlignRight)
        self.layout.addLayout(title_layout)

        # Display the message
        message_layout = QNoSpacingHBoxLayout()
        message_layout.setSpacing(10)
        if not big_icon.isNull():
            big_icon_label = QLabel()
            big_icon_label.setPixmap(big_icon.pixmap(64, 64))
            big_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            message_layout.addWidget(big_icon_label)
            message_layout.addStretch()
        self.message_label = QLabel(message)
        self.message_label.setStyleSheet(
            f"font-size: 14px; color: {"black" if self.theme == Theme.LIGHT else "white"};")
        message_layout.addWidget(self.message_label)
        message_layout.addStretch(2)
        self.layout.addLayout(message_layout)

        self.inputs = {}
        self.selections = {}

        # Initialize user activity tracker and attach it to relevant widgets
        self.activity_tracker = UserActivityTracker(self)
        self.activity_tracker.attach(self)

        # Connect activity signal to a slot
        self.activity_tracker.userActivityDetected.connect(self.reset_auto_close_timer)

        if inputs or selections or buttons:
            # Scroll area for inputs, selections, and buttons
            self.scroll_area = QScrollArea(self.background)
            self.scroll_area.setStyleSheet("""
                QWidget#content, QScrollArea {background: transparent;}""")
            self.scroll_area.setWidgetResizable(True)
            self.scroll_area.setFixedWidth(self.FIXED_WIDTH)
            self.scroll_area.setMaximumHeight(self.MAX_HEIGHT)
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.scroll_area.setFrameShape(QScrollArea.NoFrame)
            self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

            self.scroll_content = QWidget()
            self.scroll_content.setObjectName("content")
            self.scroll_layout = QVBoxLayout(self.scroll_content)
            self.scroll_layout.setContentsMargins(0, 0, 0, 0)
            self.scroll_layout.setSpacing(10)
            self.scroll_area.setWidget(self.scroll_content)
            self.layout.addWidget(self.scroll_area)

            # Add input fields
            if inputs:
                for input_name, input_display, input_hint in inputs:
                    input_field = QLineEdit(self.background)
                    input_field.setPlaceholderText(input_hint)
                    input_field.setStyleSheet(
                        f"font-size: 14px; color: {"black" if self.theme == Theme.LIGHT else "white"}; height: 30px;")
                    self.scroll_layout.addWidget(QLabel(input_display, self.scroll_content))
                    self.scroll_layout.addWidget(input_field)
                    self.inputs[input_name] = input_field
                    self.activity_tracker.attach(input_field)

            # Add selection boxes
            if selections:
                for selection_name, selection_display, selection_options, default_selection_id in selections:
                    selection_box = QComboBox(self.background)
                    selection_box.setStyleSheet(f"""
                        QComboBox {{
                            font-size: 14px;
                            color: {"black" if self.theme == Theme.LIGHT else "white"};
                            height: 30px;
                        }}
                        QComboBox QAbstractItemView {{
                            border: 1px solid #808080;
                            background-color: white;
                            border-radius: 5px;
                            margin-top: -5px;
                        }}""")
                    for option_name, option_display in selection_options:
                        selection_box.addItem(option_display, option_name)
                    selection_box.setCurrentIndex(default_selection_id)
                    self.scroll_layout.addWidget(QLabel(selection_display, self.scroll_content))
                    self.scroll_layout.addWidget(selection_box)
                    self.selections[selection_name] = selection_box
                    self.activity_tracker.attach(selection_box)

            # Add buttons
            self.button_callbacks = []
            if buttons:
                for button_text, callback in buttons:
                    button = QPushButton(button_text, self.background)
                    button.setStyleSheet(f"""
                        QPushButton {{
                            font-size: 14px;
                            color: {"black" if self.theme == Theme.LIGHT else "white"};
                            height: 40px;
                            background-color: {'#3c3c3c' if self.theme == Theme.DARK else '#f0f0f0'};
                            border-radius: 5px;
                        }}
                        QPushButton:hover {{
                            background-color: {'#333333' if self.theme == Theme.DARK else '#e0e0e0'};
                        }}""")
                    self.scroll_layout.addWidget(button)
                    button.clicked.connect(self.create_button_callback(callback))
                    self.button_callbacks.append(callback)
                    self.activity_tracker.attach(button)
            self.background.resize(self.FIXED_WIDTH, self.MAX_HEIGHT)
            self.background.adjustSize()
        else:
            self.background.resize(self.FIXED_WIDTH, self.MAX_HEIGHT)
            self.background.adjustSize()
            self.background.resize(self.FIXED_WIDTH + 20, self.background.height() + 10)

        # Animation setup
        self.show_animation = QPropertyAnimation(self, b"geometry")
        self.show_animation.setDuration(1000)
        self.show_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.close_animation = QPropertyAnimation(self, b"geometry")
        self.close_animation.setDuration(1000)
        self.close_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.close_animation.finished.connect(self.close)

        # Visual indication animations
        self.shrink_animation = QPropertyAnimation(self.background, b"geometry")
        self.shrink_animation.setDuration(200)
        self.shrink_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.darkening_effect = self.background.graphicsEffect()

        # Position the notification
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        self.notification_height = self.background.height()
        self.notification_width = self.background.width()
        self.start_rect = QRect(screen_geometry.width() - self.notification_width - 10, screen_geometry.height() + 60,
                                self.notification_width, self.notification_height)
        self.end_rect = QRect(screen_geometry.width() - self.notification_width - 10,
                              screen_geometry.height() - self.notification_height - 10, self.notification_width,
                              self.notification_height)
        self.setGeometry(self.start_rect)
        self.send = False

        # Display the notification
        self.show()
        self.animate_show()

        # Set up auto-close timer
        self.auto_close_timer = QTimer(self)
        self.auto_close_timer.setSingleShot(True)
        self.auto_close_timer.timeout.connect(self.close_with_animation)
        self.auto_close_timer.start(auto_close_duration)

    def reset_auto_close_timer(self):
        self.auto_close_timer.start()

    def animate_show(self):
        self.show_animation.setStartValue(self.start_rect)
        self.show_animation.setEndValue(self.end_rect)
        self.show_animation.start()

    def close_with_animation(self):
        self.send = True
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

        self.background.setStyleSheet(f"""
            QWidget#background {{
                background-color: {"#1c1c1c" if self.theme == Theme.DARK else "#d3d3d3"};
                border: 2px solid black;
                border-radius: 10px;
            }}
        """)

        self.reset_auto_close_timer()

    def handle_mouse_release(self, event):
        if self.mouse_press_pos:
            delta = (event.globalPosition().toPoint() - self.mouse_press_pos).manhattanLength()
            if delta < self.mouse_move_threshold:
                if not self.send:
                    self.send = True
                    if self.click_callback:
                        input_values = {name: field.text() for name, field in self.inputs.items()}
                        selection_values = {name: box.currentData() for name, box in self.selections.items()}
                        self.click_callback(inputs=input_values, selections=selection_values)
                    self.close_with_animation()
            else:
                self.reset_visual_indicators()
            self.mouse_press_pos = None

        self.reset_auto_close_timer()

    def handle_mouse_move(self, event):
        pass  # Placeholder for potential drag handling

    def reset_visual_indicators(self):
        self.shrink_animation.setStartValue(self.background.geometry())
        self.shrink_animation.setEndValue(QRect(0, 0, self.notification_width, self.notification_height))
        self.shrink_animation.start()

        self.background.setStyleSheet(f"""
            QWidget#background {{
                background-color: {"white" if self.theme == Theme.LIGHT else "#222222"};
                border: 2px solid black;
                border-radius: 10px;
            }}
        """)

    def create_button_callback(self, callback):
        def wrapped_callback():
            if not self.send:
                self.send = True
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
        self.notification_widget = None

    def show_notification(self, abs_icon_path, abs_big_icon_path, title, message, inputs=None, selections=None, buttons=None,
                          click_callback=None, auto_close_duration=5000):
        self.notification_widget = BalloonTip(QIcon(abs_icon_path), QIcon(abs_big_icon_path), title, message, inputs,
                                              selections, buttons, click_callback, auto_close_duration)


class NotificationManager:
    notification_system = None

    @staticmethod
    def show_notification(icon_path, title, message, inputs=None, selections=None, buttons=None,
                          click_callback=None, auto_close_duration=5000):
        def run_app():
            app = QApplication(sys.argv)
            notification_system = NotificationSystem(QIcon("None"))  # Leave this as None to make it not show up
            notification_system.show()

            notification_system.show_notification(
                os.path.abspath(icon_path), "",
                title,
                message,
                inputs=inputs,
                selections=selections,
                buttons=buttons,
                click_callback=click_callback,
                auto_close_duration=auto_close_duration
            )
            NotificationManager.notification_system = notification_system

            app.exec()

        def check_notification_done():
            while NotificationManager.notification_system is None:
                time.sleep(0.1)
            while not NotificationManager.notification_system.notification_widget.send:
                time.sleep(0.1)
            time.sleep(2)
            QCoreApplication.quit()

        # Run the app in a separate thread
        app_thread = threading.Thread(target=run_app)
        app_thread.start()

        # Check if the notification is done
        check_notification_done()


if __name__ == "__main__":
    # Show a sample notification with inputs, selections, buttons, and click callback
    inputs = [("name", "Name", "Enter your name")]
    selections = [("choice", "Choice", [("option1", "Option 1"), ("option2", "Option 2")], 0)]
    buttons = [("OK", lambda: print("OK clicked")), ("Cancel", lambda: print("Cancel clicked"))]

    NotificationManager.show_notification(
        "",
        "Sample Notification",
        "This is a sample notification message.",
        inputs=inputs,
        selections=selections,
        buttons=buttons,
        click_callback=lambda inputs, selections: print(f"Clicked with inputs: {inputs}, selections: {selections}"),
        auto_close_duration=7000  # Auto close after 7 seconds
    )
