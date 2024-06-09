from PySide6.QtCore import QTimer, Signal, QObject, QEvent, QDateTime
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout


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


class UserActivityTracker(QObject):
    userActivityDetected = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.activity_timer = QTimer(self)
        self.activity_timer.timeout.connect(self.check_user_activity)
        self.activity_timer.start(1000)  # check every second
        self.last_activity_time = None

    def attach(self, widget):
        widget.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() in {QEvent.Type.MouseButtonPress, QEvent.Type.KeyPress, QEvent.Type.FocusIn,
                            QEvent.Type.FocusOut, QEvent.Type.WindowActivate, QEvent.Type.WindowDeactivate}:
            self.last_activity_time = QDateTime.currentDateTime()
            self.userActivityDetected.emit()
        return super().eventFilter(obj, event)

    def check_user_activity(self):
        if self.last_activity_time:
            # Reset activity time after detecting activity
            self.last_activity_time = None
