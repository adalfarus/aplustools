from PySide6.QtWidgets import QPlainTextEdit, QStyleOptionFrame, QStyle
from PySide6.QtGui import QTextOption, QFocusEvent,QTextCursor, QFontMetricsF
from PySide6.QtCore import Qt, QSize


class QLineSpellCheckEdit(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.textChanged.connect(self.cb_textChanged)

        self.setTabChangesFocus(True)

    def focusInEvent(self, e: QFocusEvent):
        """Override focusInEvent to mimic QLineEdit behaviour"""
        super(QLineSpellCheckEdit, self).focusInEvent(e)

        # TODO: Are there any other things I'm supposed to be checking for?
        if e.reason() in (Qt.BacktabFocusReason, Qt.ShortcutFocusReason,
                          Qt.TabFocusReason):
            self.selectAll()

    def focusOutEvent(self, e: QFocusEvent):
        """Override focusOutEvent to mimic QLineEdit behaviour"""
        super(QLineSpellCheckEdit, self).focusOutEvent(e)

        # TODO: Are there any other things I'm supposed to be checking for?
        if e.reason() in (Qt.BacktabFocusReason, Qt.MouseFocusReason,
                          Qt.ShortcutFocusReason, Qt.TabFocusReason):
            # De-select everything and move the cursor to the end
            cur = self.textCursor()
            cur.movePosition(QTextCursor.End)
            self.setTextCursor(cur)

    def cb_textChanged(self):
        if self.document().blockCount() > 1:
            self.document().setPlainText(self.document().firstBlock().text())

    def minimumSizeHint(self):
        """Redefine minimum size hint to match QLineEdit"""
        block_fmt = self.document().firstBlock().blockFormat()
        width = super(QLineSpellCheckEdit, self).minimumSizeHint().width()
        height = int(
            QFontMetricsF(self.font()).lineSpacing() +  # noqa
            block_fmt.topMargin() + block_fmt.bottomMargin() +  # noqa
            self.document().documentMargin() +  # noqa
            2 * self.frameWidth()
        )

        style_opts = QStyleOptionFrame()
        style_opts.initFrom(self)
        style_opts.lineWidth = self.frameWidth()
        # TODO: Is it correct that I'm achieving the correct content height
        #       under test conditions by feeding self.frameWidth() to both
        #       QStyleOptionFrame.lineWidth and the sizeFromContents height
        #       calculation?

        return self.style().sizeFromContents(
            QStyle.CT_LineEdit,
            style_opts,
            QSize(width, height),
            self
        )

    def sizeHint(self):
        """Reuse minimumSizeHint for sizeHint"""
        return self.minimumSizeHint()


if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    window = QLineSpellCheckEdit()
    window.show()
    sys.exit(app.exec_())
