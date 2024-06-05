import sys
import os
import ctypes
from PIL import Image
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QIcon, QPixmap





def main():
    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle('Get App Icon Example')

    layout = QVBoxLayout()

    try:
        icon_path = get_app_icon_path()
        app_icon = QIcon(icon_path)
    except Exception as e:
        print(f"Error retrieving app icon path: {e}")
        app_icon = QIcon()

    label = QLabel()
    label.setPixmap(app_icon.pixmap(64, 64))

    layout.addWidget(label)
    window.setLayout(layout)

    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
