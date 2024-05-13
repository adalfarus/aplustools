from aplustools.package import install_dependencies_lst as _install_dependencies_lst
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout


def install_dependencies():
    success = _install_dependencies_lst(["PySide6==6.6.1", "brotli==1.1.0"])
    if not success:
        return
    print("Done, all possible dependencies for the data module installed ...")


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
