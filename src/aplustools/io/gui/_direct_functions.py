from PySide6.QtCore import QTimer, Signal, QObject, QEvent, QDateTime, QSize, Qt, QRect
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLayout, QWidget, QTextEdit
from PySide6.QtGui import QTextCursor
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


class QBulletPointTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(False)
        self.ensure_bullet_point()

    def ensure_bullet_point(self, new: bool = False):
        cursor = self.textCursor()
        if cursor.block().text().strip() == "":
            cursor.insertText("• ")
        else:
            block_text = cursor.block().text()
            if not block_text.startswith("• "):
                cursor.movePosition(QTextCursor.MoveOperation.NextBlock)
                if cursor.block().text() != "":
                    cursor.movePosition(QTextCursor.MoveOperation.PreviousBlock)
                cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                cursor.insertText("• ")
        self.setTextCursor(cursor)

    def keyPressEvent(self, event):
        cursor = self.textCursor()

        if event.key() in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
            super().keyPressEvent(event)
            self.ensure_bullet_point()
        elif event.key() == Qt.Key.Key_Backspace:
            block_text = cursor.block().text().strip()
            if cursor.blockNumber() == 0 and (block_text + " ").startswith("• ") and cursor.positionInBlock() == 2:  # If at the first block with only a bullet point
                return
            elif cursor.positionInBlock() == 2 and (block_text + " ").startswith("• "):  # If the line only contains a bullet point
                cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
                cursor.removeSelectedText()
                cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
                cursor.insertText(block_text[2:])
                cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
                cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.MoveAnchor, len(block_text[2:]))
                self.setTextCursor(cursor)
                # cursor.deletePreviousChar()
            else:
                super().keyPressEvent(event)
        elif event.key() in [Qt.Key.Key_Delete]:
            if cursor.atBlockEnd():
                position_in_block = cursor.positionInBlock()
                start_block = cursor.block()
                cursor.movePosition(QTextCursor.MoveOperation.NextBlock)
                if cursor.blockNumber() == 0 or start_block == cursor.block():  # If at the first block with only a bullet point or the last point
                    return

                next_block_text = cursor.block().text()
                cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
                cursor.removeSelectedText()
                rest = next_block_text[2:]

                cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
                cursor.insertText(rest)
                cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor, position_in_block)
                self.setTextCursor(cursor)
            elif cursor.blockNumber() == 0:  # If at the first block with only a bullet point
                return
            else:
                super().keyPressEvent(event)
        else:
            if cursor.hasSelection():
                start = cursor.selectionStart()
                end = cursor.selectionEnd()
                cursor.setPosition(start)
                # Check if the selection includes the bullet point
                if cursor.block().text().startswith("•") and start < cursor.block().position() + 2:
                    return

            super().keyPressEvent(event)
            self.ensure_bullet_point()  # Ensure a space after bullet point if missing

    def get_bullet_points(self) -> list:
        bullet_points = []
        cursor = QTextCursor(self.document())
        cursor.movePosition(QTextCursor.MoveOperation.Start)

        while True:
            block = cursor.block()
            text = block.text().strip()
            if text.startswith("• "):
                bullet_points.append(text[2:])
            if not cursor.movePosition(QTextCursor.MoveOperation.NextBlock):
                break
        return bullet_points
