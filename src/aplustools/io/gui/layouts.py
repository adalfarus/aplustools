from PySide6.QtWidgets import QLayout, QSizePolicy, QWidget
from PySide6.QtCore import QRect, QSize, Qt


class QFlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        self.item_list = []
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)

    def addItem(self, item):
        self.item_list.append(item)

    def count(self):
        return len(self.item_list)

    def itemAt(self, index):
        if index >= 0 and index < len(self.item_list):
            return self.item_list[index]
        return None

    def takeAt(self, index):
        if index >= 0 and index < len(self.item_list):
            return self.item_list.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation.Horizontal | Qt.Orientation.Vertical

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self.doLayout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.item_list:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def doLayout(self, rect, testOnly):
        raise NotImplementedError("doLayout must be implemented by subclasses")


class QFixedFlowLayout(QFlowLayout):
    def __init__(self, parent=None, margin=0, spacing=-1, items_per_row=3):
        super().__init__(parent, margin, spacing)
        self.items_per_row = items_per_row

    def doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        lineHeight = 0

        for index, item in enumerate(self.item_list):
            item_size = item.sizeHint()
            item_size.setWidth(rect.width() // self.items_per_row)
            next_x = x + item_size.width() + self.spacing()

            if (index + 1) % self.items_per_row == 0:
                if not testOnly:
                    item.setGeometry(QRect(x, y, item_size.width(), item_size.height()))
                y += lineHeight + self.spacing()
                x = rect.x()
                lineHeight = 0
            else:
                if not testOnly:
                    item.setGeometry(QRect(x, y, item_size.width(), item_size.height()))
                x = next_x
                lineHeight = max(lineHeight, item_size.height())

        return y + lineHeight - rect.y()


class QStrictFlowLayout(QFlowLayout):
    def __init__(self, parent=None, margin=0, spacing=-1, ideal_item_width=100):
        super().__init__(parent, margin, spacing)
        self.ideal_item_width = ideal_item_width

    def doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        lineHeight = 0

        for item in self.item_list:
            item_size = item.sizeHint()
            item_size.setWidth(self.ideal_item_width)
            next_x = x + item_size.width() + self.spacing()

            if next_x - self.spacing() > rect.right():
                if not testOnly:
                    item.setGeometry(QRect(x, y, item_size.width(), lineHeight))
                y += lineHeight + self.spacing()
                x = rect.x()
                next_x = x + item_size.width() + self.spacing()
                lineHeight = 0

            if not testOnly:
                item.setGeometry(QRect(x, y, item_size.width(), item_size.height()))

            x = next_x
            lineHeight = max(lineHeight, item_size.height())

        return y + lineHeight - rect.y()


class QDynamicFlowLayout(QFlowLayout):
    def __init__(self, parent=None, margin=0, spacing=-1, ideal_item_width=100, fill_half_full_rows=False):
        super().__init__(parent, margin, spacing)
        self.ideal_item_width = ideal_item_width
        self.fill_half_full_rows = fill_half_full_rows

    def doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        lineHeight = 0

        items_in_row = []
        current_row_width = 0

        for item in self.item_list:
            item_size = item.sizeHint()
            item_size.setWidth(self.ideal_item_width)
            next_x = x + item_size.width() + self.spacing()

            if next_x - self.spacing() > rect.right() and items_in_row:
                # Calculate the remaining space and distribute it evenly among the items
                available_width = rect.width() - current_row_width + self.spacing()
                extra_width_per_item = available_width // len(items_in_row)

                for i, it in enumerate(items_in_row):
                    if not testOnly:
                        it.setGeometry(QRect(
                            rect.x() + i * (self.ideal_item_width + extra_width_per_item + self.spacing()),
                            y,
                            self.ideal_item_width + extra_width_per_item,
                            it.sizeHint().height()
                        ))

                y += lineHeight + self.spacing()
                x = rect.x()
                lineHeight = 0
                items_in_row = []
                current_row_width = 0
                next_x = x + item_size.width() + self.spacing()

            if not testOnly:
                item.setGeometry(QRect(x, y, item_size.width(), item_size.height()))

            items_in_row.append(item)
            x = next_x
            current_row_width += item_size.width() + self.spacing()
            lineHeight = max(lineHeight, item_size.height())

        # Final row adjustment
        if items_in_row:
            available_width = rect.width() - current_row_width + self.spacing()
            if self.fill_half_full_rows:
                extra_width_per_item = available_width // len(items_in_row)
                for i, it in enumerate(items_in_row):
                    if not testOnly:
                        it.setGeometry(QRect(
                            rect.x() + i * (self.ideal_item_width + extra_width_per_item + self.spacing()),
                            y,
                            self.ideal_item_width + extra_width_per_item,
                            it.sizeHint().height()
                        ))
            else:
                # Calculate the width each item would have if the row was full
                full_row_count = (rect.width() + self.spacing()) // (self.ideal_item_width + self.spacing())

                if full_row_count > 0:
                    # Calculate the width each item would need to fill the entire row if it were full
                    full_row_item_width = (rect.width() - (full_row_count - 1) * self.spacing()) // full_row_count

                    for i, it in enumerate(items_in_row):
                        if not testOnly:
                            it.setGeometry(QRect(
                                rect.x() + i * (full_row_item_width + self.spacing()),
                                y,
                                full_row_item_width,
                                it.sizeHint().height()
                            ))

        return y + lineHeight - rect.y()


class QFluidFlowLayout(QFlowLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent, margin, spacing)

    def doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        lineHeight = 0

        item_count = len(self.item_list)
        if item_count == 0:
            return 0

        # Calculate the available width and height
        available_width = rect.width()
        available_height = rect.height()

        # Determine ideal item width and height, ensuring no division by zero
        ideal_item_width = max(1, available_width // item_count)
        ideal_item_height = max(1, available_height // item_count)

        # Calculate the number of rows needed
        num_rows = max(1, available_height // ideal_item_height)
        items_per_row = max(1, item_count // num_rows)

        current_row_width = 0
        current_row_count = 0

        for i, item in enumerate(self.item_list):
            item_size = item.sizeHint()

            # Calculate item width and height to fit within the grid
            item_width = available_width // items_per_row
            item_height = item_size.height()

            # Place the item
            if not testOnly:
                item.setGeometry(QRect(x, y, item_width, item_height))

            # Update x position for the next item
            x += item_width + self.spacing()
            current_row_width += item_width + self.spacing()
            lineHeight = max(lineHeight, item_height)
            current_row_count += 1

            # Move to the next row if current row is full
            if current_row_count >= items_per_row:
                y += lineHeight + self.spacing()
                x = rect.x()
                current_row_count = 0
                lineHeight = 0

        return y + lineHeight - rect.y()

    def minimumSize(self):
        size = QSize()
        for item in self.item_list:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size


import sys
from PySide6.QtWidgets import QApplication, QWidget, QPushButton

class Window(QWidget):
    def __init__(self):
        super().__init__()
        # Choose one of the layouts:
        layout = QDynamicFlowLayout(self, ideal_item_width=40)  # Fixed number of items per row
        # layout = FixedItemWidthFlowLayout(self, item_width=120)  # Fixed item width

        for i in range(10):
            layout.addWidget(QPushButton(f"Button {i+1}"))
        self.setLayout(layout)

app = QApplication(sys.argv)
window = Window()
window.show()
sys.exit(app.exec_())
