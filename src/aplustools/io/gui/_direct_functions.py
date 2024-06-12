from PySide6.QtCore import QTimer, Signal, QObject, QEvent, QDateTime, QSize, Qt, QRect
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLayout, QWidget, QTextEdit
from typing import Optional, Tuple


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


class QUserActivityTracker(QObject):
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


class QCenteredLayout(QLayout):
    def __init__(self, margin: int = 0, parent=None):
        super().__init__(parent)
        self.margin = margin
        self.item_list = []

    def addItem(self, item):
        self.item_list.append(item)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize(0, 0)
        for item in self.item_list:
            size = size.expandedTo(item.minimumSize())
        size += QSize(2 * self.margin, 2 * self.margin)
        return size

    def setGeometry(self, rect):
        super().setGeometry(rect)
        x = rect.x() + self.margin
        y = rect.y() + self.margin
        width = rect.width() - 2 * self.margin
        height = rect.height() - 2 * self.margin

        centered_rect = QRect(x, y, width, height)
        for item in self.item_list:
            item_size = item.sizeHint()
            item_x = x + (width - item_size.width()) // 2
            item_y = y + (height - item_size.height()) // 2
            item.setGeometry(QRect(item_x, item_y, item_size.width(), item_size.height()))

    def count(self):
        return len(self.item_list)

    def itemAt(self, index):
        if 0 <= index < len(self.item_list):
            return self.item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self.item_list):
            return self.item_list.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Horizontal | Qt.Vertical


class QQuickVBoxLayout(QVBoxLayout):
    def __init__(self, spacing: int = 9, margins: Tuple[int, int, int, int] = (9, 9, 9, 9), *contents,
                 apply_layout_to: Optional[QWidget] = None, parent=None):
        super().__init__(parent=parent)
        self.setSpacing(spacing)
        self.setContentsMargins(*margins)

        for content in contents:
            if isinstance(content, QLayout):
                self.addLayout(content)
            elif isinstance(content, QWidget):
                self.addWidget(content)
                
        if apply_layout_to is not None:
            apply_layout_to.setLayout(self)


class QQuickHBoxLayout(QHBoxLayout):
    def __init__(self, spacing: int = 9, margins: Tuple[int, int, int, int] = (9, 9, 9, 9), *contents,
                 apply_layout_to: Optional[QWidget] = None, parent=None):
        super().__init__(parent=parent)
        self.setSpacing(spacing)
        self.setContentsMargins(*margins)

        for content in contents:
            if isinstance(content, QLayout):
                self.addLayout(content)
            elif isinstance(content, QWidget):
                self.addWidget(content)

        if apply_layout_to is not None:
            apply_layout_to.setLayout(self)


class BulletPointTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(False)
        self.insertBulletPoint()

    def insertBulletPoint(self):
        cursor = self.textCursor()
        cursor.insertText("• ")
        self.setTextCursor(cursor)

    def keyPressEvent(self, event):
        if event.key() in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
            super().keyPressEvent(event)
            self.insertBulletPoint()
        elif event.key() == Qt.Key.Key_Backspace:
            cursor = self.textCursor()
            if cursor.positionInBlock() <= 2:  # Position in block considers bullet point
                return
            super().keyPressEvent(event)
        elif event.key() == Qt.Key.Key_Delete:
            cursor = self.textCursor()
            if cursor.atBlockEnd():
                return
            super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)
