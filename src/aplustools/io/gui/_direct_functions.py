from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLayout, QWidget, QTextEdit, QPushButton, QFrame, QScrollArea,
                               QLabel)
from PySide6.QtCore import QTimer, Signal, QObject, QEvent, QDateTime, QSize, Qt, QRect, QUrl
from PySide6.QtGui import QTextCursor, QPixmap
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView

from aplustools.io.environment import get_system, SystemTheme
from aplustools.package.timid import TimidTimer

from typing import Optional, Tuple
import itertools
import os


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
        return Qt.Orientation.Horizontal | Qt.Orientation.Vertical


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


class QThemeSensor(QObject):
    themeChanged = Signal()

    def __init__(self):
        super().__init__()
        self.timer = TimidTimer(start_now=False)

        self.system = get_system()
        self.theme = self.system.get_system_theme()

        self.timer.fire(1, self.check_theme)

    def check_theme(self):
        current_theme = self.system.get_system_theme()
        if current_theme != self.theme:
            self.theme = current_theme
            self.themeChanged.emit()

    def cleanup(self):
        self.__del__()

    def __del__(self):
        self.timer.stop_fire()


global_theme_sensor = QThemeSensor()


class QSmartTextEdit(QTextEdit):
    def __init__(self, max_height=100, parent=None):
        super().__init__(parent)
        self.max_height = max_height
        self.textChanged.connect(self.adjustHeight)

    def adjustHeight(self):
        doc_height = self.document().size().height()
        if doc_height > self.max_height:
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.setFixedHeight(self.max_height)
        else:
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.setFixedHeight(int(doc_height))

    def showEvent(self, event):
        super().showEvent(event)
        self.adjustHeight()

    def text(self) -> str:
        return self.toPlainText()


class QBaseDocumentViewerControls(QWidget):
    fit_changed = Signal(str)
    pop_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Document Viewer')

        self.mode_iterator = itertools.cycle(("./assets/fit_both.svg", "./assets/no_limit.svg", "./assets/fit_width.svg", "./assets/fit_height.svg"))
        self.popout_iterator = itertools.cycle(("./assets/pop_out.svg", "./assets/pop_in.svg"))

        self.main_layout = QHBoxLayout(self)
        self.controls_layout = QVBoxLayout(self)

        self.pop_button = QPushButton()
        self.pop_button.setIcon(QPixmap(next(self.popout_iterator)))
        self.pop_button.clicked.connect(self.change_pop)
        self.pop_button.setFixedSize(40, 40)
        self.controls_layout.addWidget(self.pop_button)

        self.fit_button = QPushButton()
        self.fit_button.setIcon(QPixmap(next(self.mode_iterator)))
        self.fit_button.clicked.connect(self.change_fit)
        self.fit_button.setFixedSize(40, 40)
        self.controls_layout.addWidget(self.fit_button)

        self.fit_window_button = QPushButton()
        self.fit_window_button.setIcon(QPixmap("assets/fit_window.svg"))
        self.FIT_WINDOW = self.fit_window_button.clicked
        self.fit_window_button.setFixedSize(40, 40)
        self.controls_layout.addWidget(self.fit_window_button)

        self.controls_frame = QFrame()
        self.controls_frame.setMaximumWidth(60)
        self.controls_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.controls_frame.setFrameShadow(QFrame.Shadow.Raised)
        self.controls_frame.setLayout(self.controls_layout)

        self.setMinimumSize(300, 200)

        self.main_layout.addWidget(self.controls_frame, alignment=Qt.AlignmentFlag.AlignLeft)

        self.setLayout(self.main_layout)

        self.fit_emit = "fit_both"
        self.pop_emit = "pop_out"

    def change_fit(self):
        fit = next(self.mode_iterator)
        self.fit_button.setIcon(QPixmap(fit))
        self.fit_emit = os.path.basename(fit).split(".")[0]
        self.fit_changed.emit(self.fit_emit)

    def change_pop(self):
        pop = next(self.popout_iterator)
        self.pop_button.setIcon(QPixmap(pop))
        self.pop_emit = os.path.basename(pop).split(".")[0]
        self.pop_changed.emit(self.pop_emit)


class QDocumentViewer(QBaseDocumentViewerControls):
    def __init__(self, parent=None, allow_multiple_popouts: bool = False):
        super().__init__(parent)
        self.theme = global_theme_sensor.theme
        self.scroll_area = QScrollArea()  # Scroll area for the content
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        self.scroll_area.setFrameShape(QFrame.Shape.StyledPanel)
        self.scroll_area.setFrameShadow(QFrame.Shadow.Raised)
        self.scroll_area.setStyleSheet(f"""
                    QScrollArea {{
                        border-radius: 5px;
                        background-color: #{"2d2d2d" if self.theme == SystemTheme.DARK else "fbfbfb"};
                        margin: 1px;
                    }}
                    QScrollArea > QWidget > QWidget {{
                        border: none;
                        border-radius: 15px;
                        background-color: transparent;
                    }}
                    QScrollBar:vertical {{
                        border: none;
                        background: #{'3c3c3c' if self.theme == SystemTheme.DARK else 'f0f0f0'};
                        width: 15px;
                        margin: 15px 0 15px 0;
                        border-radius: 7px;
                    }}
                    QScrollBar::handle:vertical {{
                        background: #{'888888' if self.theme == SystemTheme.DARK else 'cccccc'};
                        min-height: 20px;
                        border-radius: 7px;
                    }}
                    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                        border: none;
                        background: none;
                    }}
                    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                        background: none;
                    }}
                    QScrollBar:horizontal {{
                        border: none;
                        background: #{'3c3c3c' if self.theme == SystemTheme.DARK else 'f0f0f0'};
                        height: 15px;
                        margin: 0 15px 0 15px;
                        border-radius: 7px;
                    }}
                    QScrollBar::handle:horizontal {{
                        background: #{'888888' if self.theme == SystemTheme.DARK else 'cccccc'};
                        min-width: 20px;
                        border-radius: 7px;
                    }}
                    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                        border: none;
                        background: none;
                    }}
                    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                        background: none;
                    }}
                """)

        self.general_preview_widget = QLabel()
        self.general_preview_widget.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.general_preview_widget.setWordWrap(True)

        self.video_widget = QVideoWidget()
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setLoops(QMediaPlayer.Loops.Infinite)

        self.pdf_view = QPdfView()
        self.pdf_document = QPdfDocument(self)
        self.pdf_view.setDocument(self.pdf_document)

        self.scroll_layout.addWidget(self.general_preview_widget)
        self.scroll_layout.addWidget(self.video_widget)
        self.scroll_layout.addWidget(self.pdf_view)
        self.general_preview_widget.hide()
        self.video_widget.hide()
        self.pdf_view.hide()

        self.main_layout.addWidget(self.scroll_area)
        self.is_popped_out = False
        self.current_file_path = ""
        self.pop_changed.connect(self.pop_out_in)
        self.wins = []
        self.allow_multiple_popouts = allow_multiple_popouts
        self.fit_changed.connect(self.fit_content)
        self.FIT_WINDOW.connect(self.fit_window)
        global_theme_sensor.themeChanged.connect(self.reapply_theme)

    def fit_content(self):
        if self.fit_emit == "fit_width":
            if self.pdf_view.isVisible():
                self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
            elif self.video_widget.isVisible():
                self.video_widget.setFixedSize(self.scroll_area.width(), self.video_widget.height())
            elif self.general_preview_widget.isVisible():
                if self.general_preview_widget.pixmap().isNull():
                    self.general_preview_widget.setWordWrap(False)
                else:
                    pixmap = QPixmap(self.current_file_path)
                    self.general_preview_widget.setPixmap(pixmap.scaled(self.scroll_area.width(), pixmap.height(),
                                                                        Qt.AspectRatioMode.KeepAspectRatio))
            self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        elif self.fit_emit == "fit_height":
            if self.pdf_view.isVisible():
                self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitInView)
                self.pdf_view.setZoomFactor(0.0)
                self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
                self.pdf_view.setZoomFactor((self.scroll_area.height() / self.pdf_document.pagePointSize(0).height()) / 1.4)
            elif self.video_widget.isVisible():
                self.video_widget.setFixedSize(self.video_widget.width(), self.scroll_area.height())
            if self.general_preview_widget.isVisible():
                if self.general_preview_widget.pixmap().isNull():
                    self.general_preview_widget.setWordWrap(True)
                else:
                    pixmap = QPixmap(self.current_file_path)
                    self.general_preview_widget.setPixmap(pixmap.scaled(pixmap.width(), self.scroll_area.height(),
                                                                        Qt.AspectRatioMode.KeepAspectRatio))
            self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        elif self.fit_emit == "fit_both":
            if self.pdf_view.isVisible():
                self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitInView)
            elif self.video_widget.isVisible():
                self.video_widget.setFixedSize(self.scroll_area.size())
            elif self.general_preview_widget.isVisible():
                if self.general_preview_widget.pixmap().isNull():
                    self.general_preview_widget.setWordWrap(True)
                else:
                    pixmap = QPixmap(self.current_file_path)
                    self.general_preview_widget.setPixmap(pixmap.scaled(self.scroll_area.size()))
            self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        elif self.fit_emit == "no_limit":  # fit_none
            if self.pdf_view.isVisible():
                self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
                self.pdf_view.setZoomFactor(1.0)
            elif self.video_widget.isVisible():
                self.video_widget.setFixedSize(600, 400)
            if self.general_preview_widget.isVisible():
                if self.general_preview_widget.pixmap().isNull():
                    self.general_preview_widget.setWordWrap(True)
                else:
                    pixmap = QPixmap(self.current_file_path)
                    self.general_preview_widget.setPixmap(pixmap)
            self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    def pop_out_in(self):
        if self.is_popped_out:
            self.close()
        else:
            if not self.allow_multiple_popouts and len(self.wins) > 0:
                self.wins[0].close()
                del self.wins[0]
            win = QDocumentViewer()
            win.preview_document(self.current_file_path)
            win.pop_button.setIcon(QPixmap(next(win.popout_iterator)))
            win.is_popped_out = True
            win.show()
            win.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().value())
            win.scroll_area.horizontalScrollBar().setValue(self.scroll_area.horizontalScrollBar().value())
            win.fit_in(self.fit_emit, itertools.tee(self.mode_iterator)[0])
            win.fit_content()
            self.wins.append(win)

    def fit_in(self, current_fit, iterator):
        self.mode_iterator = iterator
        self.fit_button.setIcon(QPixmap(f"./assets/{current_fit}.svg"))
        self.fit_emit = current_fit

    def change_pop(self):
        pop = next(self.popout_iterator)
        self.pop_emit = os.path.basename(pop).split(".")[0]
        self.pop_changed.emit(self.pop_emit)

    def preview_document(self, file_path: str):
        self.current_file_path = file_path

        self.general_preview_widget.hide()
        self.video_widget.hide()
        self.pdf_view.hide()

        if not file_path:
            return

        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.svg')):
            self.general_preview_widget.show()
            self.general_preview_widget.setPixmap(QPixmap(file_path))
        elif file_path.lower().endswith('.pdf'):
            self.pdf_view.show()
            self.pdf_document.load(file_path)
        elif file_path.lower().endswith(('.mp4', '.mov')):
            self.video_widget.show()
            self.media_player.setSource(QUrl.fromLocalFile(file_path))
            self.media_player.play()
        else:
            self.general_preview_widget.show()
            try:
                with open(file_path, 'r') as f:
                    contents = f.read()
                self.general_preview_widget.setText(contents)
            except Exception:
                self.general_preview_widget.setText(f"Unsupported file format: {file_path}")

        self.fit_content()

    def fit_window(self, arg):
        if self.is_popped_out:
            # Adjust the scroll area to its contents
            self.scroll_area.adjustSize()

            # Calculate the new size based on the content
            content_size = self.scroll_content.sizeHint()

            # Set the scroll area size to match the content size
            self.setMinimumSize(content_size)
            self.setMaximumSize(content_size)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit_content()

    def reapply_theme(self):
        self.theme = global_theme_sensor.theme
        self.scroll_area.setStyleSheet(f"""
                    QScrollArea {{
                        border-radius: 5px;
                        background-color: #{"2d2d2d" if self.theme == SystemTheme.DARK else "fbfbfb"};
                        margin: 1px;
                    }}
                    QScrollArea > QWidget > QWidget {{
                        border: none;
                        border-radius: 15px;
                        background-color: transparent;
                    }}
                    QScrollBar:vertical {{
                        border: none;
                        background: #{'3c3c3c' if self.theme == SystemTheme.DARK else 'f0f0f0'};
                        width: 15px;
                        margin: 15px 0 15px 0;
                        border-radius: 7px;
                    }}
                    QScrollBar::handle:vertical {{
                        background: #{'888888' if self.theme == SystemTheme.DARK else 'cccccc'};
                        min-height: 20px;
                        border-radius: 7px;
                    }}
                    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                        border: none;
                        background: none;
                    }}
                    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                        background: none;
                    }}
                    QScrollBar:horizontal {{
                        border: none;
                        background: #{'3c3c3c' if self.theme == SystemTheme.DARK else 'f0f0f0'};
                        height: 15px;
                        margin: 0 15px 0 15px;
                        border-radius: 7px;
                    }}
                    QScrollBar::handle:horizontal {{
                        background: #{'888888' if self.theme == SystemTheme.DARK else 'cccccc'};
                        min-width: 20px;
                        border-radius: 7px;
                    }}
                    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                        border: none;
                        background: none;
                    }}
                    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                        background: none;
                    }}
                """)


class StdTheme:  # Light then dark
    DEFAULT_MODERN_LIGHT = (("#ffffff", "#f0f0f0", "#e0e0e0", "#d6d6d6", "#c0c0c0"),
                     ("#7f7f7f", ""))
    DEFAULT_MODERN_DARK = ("", "")
    CHERRY_BLOSSOM = ("", "")
    MIDNIGHT = ("", "")


std_stylesheet = None


class StdStylesheet:
    _default_modern_base_stylesheet = """
    QWidget {{
        color: {opposite_color};
        background-color: {general_background_color};
    }}
    QWidget:disabled {{
        color: {disabled_color};
        border: none;
        background-color: {disabled_background_color};
    }}
    QComboBox {{
        border-radius: 5px;
        padding: 5px;
        background-color: {background_color};
        selection-background-color: {selection_background_color};
        selection-color: {opposite_color};
    }}
    QComboBox::drop-down {{
        border: none;
        background: transparent;
    }}
    QComboBox::down-arrow {{
        image: url(data/arrow-down.png);
    }}
    QComboBox QAbstractItemView {{
        background-color: {background_color};
        border: 1px solid {general_background_color};
        border-radius: 5px;
        margin-top: -5px;
    }}
    QCheckBox, QRadioButton {{
        background-color: {background_color};
        border-radius: 5px;           
    }}
    QLabel {{
        border-radius: 5px;
        padding: 5px;
        background-color: {background_color};
    }}
    QPushButton, QToolButton {{
        border: 2px solid {color};
        border-radius: 5px;
        padding: 5px;
        background-color: {background_color};
    }}
    QPushButton:hover, QToolButton:hover {{
        border: 1px solid {background_color};
        background-color: {selection_background_color};
    }}
    QListWidget {{
        border-radius: 10px;
        background-color: {general_background_color};
    }}
    QScrollBar:vertical {{
        border: none;
        background: {selection_background_color};
        width: 15px;
        border-radius: 7px;
    }}
    QScrollBar::handle:vertical {{
        background: {disabled_background_color};
        min-height: 20px;
        border-radius: 7px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        border: none;
        background: none;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}
    QScrollBar:horizontal {{
        border: none;
        background: {selection_background_color};
        height: 15px;
        border-radius: 7px;
    }}
    QScrollBar::handle:horizontal {{
        background: {disabled_background_color};
        min-width: 20px;
        border-radius: 7px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        border: none;
        background: none;
    }}
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: none;
    }}
    QScrollBar::corner {{
        background: {background_color};
        border: none;
    }}
    QTextEdit, QListWidget {{
        border-radius: 8px;
        background-color: {background_color};
    }}
    """
    _default_base_stylesheet = """
QPushButton {{
    font-size: 14px;
    color: {color};
    height: 40px;
    background-color: {general_background_color};
    border-radius: 5px;
}}
QPushButton:hover {{
    background-color: {selection_background_color};
}}
QComboBox {{
    font-size: 14px;
    color: {color};
    height: 30px;
}}
QComboBox QAbstractItemView {{
    border: 1px solid {border_color};
    background-color: {general_background_color};
    border-radius: 5px;
    margin-top: -5px;
}}
QLineEdit {{
    font-size: 14px;
    color: {color};
    height: 30px;
}}
QLabel {{
    font-size: 14px;
    color: {color};
}}
QWidget#background {{
    background-color: {background_color};
    border: 2px solid {border_color};
    border-radius: 10px;
}}
"""

    def __init__(self, light_light_color: str,
                 dark_light_color: str,
                 light_dark_color: str,
                 dark_dark_color: str):
        self._light_light_color = light_light_color
        self._dark_light_color = dark_light_color
        self._light_dark_color = light_dark_color
        self._dark_dark_color = dark_dark_color

        self._current_style_sheet = self._default_base_stylesheet.format(
            color="#ffffff",
            background_color="#fbfbfb",
            selection_background_color="#f2f2f2",
            border_color="#808080",
            general_background_color="#f3f3f3",
            disabled_color="#7f7f7f",
            disabled_background_color="#e0e0e0",
            opposite_color="#000000"
        )
        self._current_style_sheet = self._default_base_stylesheet.format(
            color="#000000",
            background_color="#fbfbfb",
            selection_background_color="#f2f2f2",
            border_color="#808080",
            general_background_color="#f3f3f3",
            disabled_color="#7f7f7f",
            disabled_background_color="#e0e0e0",
            opposite_color="#ffffff"
        )

        self.current_os_theme = "light"

    @classmethod
    def get_std(cls) -> "StdStylesheet":
        global std_stylesheet
        if std_stylesheet is None:
            std_stylesheet = cls.from_theme(StdTheme.DEFAULT_LIGHT, StdTheme.DEFAULT_DARK)
        return std_stylesheet

    @classmethod
    def from_theme(cls, light_theme: StdTheme, dark_theme: StdTheme):
        pass

    def change_light_theme(self, new_light_theme: StdTheme):
        pass

    def change_dark_theme(self, new_dark_theme: StdTheme):
        pass

    def __str__(self):
        return self._current_style_sheet


from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QCheckBox, QRadioButton,
    QSlider, QTextEdit, QListWidget, QScrollArea, QSpinBox, QProgressBar
)
from PySide6.QtCore import Qt


class StyleSheetTester(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PySide6 Stylesheet Tester")
        self.setGeometry(100, 100, 800, 600)

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)

        # Create a horizontal layout for enabled widgets
        enabled_layout = QHBoxLayout()
        enabled_layout.addWidget(QLabel("Enabled Widgets:"))
        enabled_layout.addWidget(self.create_widgets(enabled=True))

        # Create a horizontal layout for disabled widgets
        disabled_layout = QHBoxLayout()
        disabled_layout.addWidget(QLabel("Disabled Widgets:"))
        disabled_layout.addWidget(self.create_widgets(enabled=False))

        main_layout.addLayout(enabled_layout)
        main_layout.addLayout(disabled_layout)

        self.setCentralWidget(main_widget)

    def create_widgets(self, enabled=True):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # QPushButton
        button = QPushButton("QPushButton")
        button.setEnabled(enabled)
        layout.addWidget(button)

        # QLabel
        label = QLabel("QLabel")
        label.setEnabled(enabled)
        layout.addWidget(label)

        # QLineEdit
        line_edit = QLineEdit("QLineEdit")
        line_edit.setEnabled(enabled)
        layout.addWidget(line_edit)

        # QComboBox
        combo_box = QComboBox()
        combo_box.addItems(["Item 1", "Item 2", "Item 3", "Item 4", "Item 5", "Item 6"])
        combo_box.setEnabled(enabled)
        layout.addWidget(combo_box)

        # QCheckBox
        check_box = QCheckBox("QCheckBox")
        check_box.setEnabled(enabled)
        layout.addWidget(check_box)

        # QRadioButton
        radio_button = QRadioButton("QRadioButton")
        radio_button.setEnabled(enabled)
        layout.addWidget(radio_button)

        # QSlider
        slider = QSlider(Qt.Horizontal)
        slider.setEnabled(enabled)
        layout.addWidget(slider)

        # QTextEdit
        text_edit = QTextEdit("QTextEdit")
        text_edit.setEnabled(enabled)
        layout.addWidget(text_edit)

        # QListWidget
        list_widget = QListWidget()
        list_widget.addItems(["Item 1", "Item 2", "Item 3", "Item 4", "Item 5", "Item 6"])
        list_widget.setEnabled(enabled)
        layout.addWidget(list_widget)

        # QScrollArea
        scroll_area = QScrollArea()
        scroll_content = QLabel("QScrollArea Content")
        scroll_content.setFixedSize(300, 300)
        scroll_area.setWidget(scroll_content)
        scroll_area.setEnabled(enabled)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        layout.addWidget(scroll_area)

        # QSpinBox
        spin_box = QSpinBox()
        spin_box.setEnabled(enabled)
        layout.addWidget(spin_box)

        # QProgressBar
        progress_bar = QProgressBar()
        progress_bar.setValue(50)
        progress_bar.setEnabled(enabled)
        layout.addWidget(progress_bar)

        return widget


if __name__ == "__main__":
    app = QApplication([])

    # Set the stylesheet here for testing
    ss = StdStylesheet("2", "", "", "")
    stylesheet = str(ss)
    app.setStyleSheet(stylesheet)

    window = StyleSheetTester()
    window.show()

    app.exec()