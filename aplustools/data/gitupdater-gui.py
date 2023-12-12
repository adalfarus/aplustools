import sys
import threading
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QTextEdit
from PySide6.QtCore import Signal, QObject
from aplustools.data import updaters
from aplustools.io import environment as env

class UpdateThread(QObject):
    update_signal = Signal(str)

    def __init__(self, path, zip_path, version, author, repo_name):
        super().__init__()
        self.path = path
        self.zip_path = zip_path
        self.version = version
        self.author = author
        self.repo_name = repo_name

    def start_update(self):
        threading.Thread(target=self.run_update, args=()).start()

    def run_update(self):
        try:
            env.set_working_dir_to_main_script_location()
            updater = updaters.gitupdater("exe")
            tmpdir, path = env.Path(self.zip_path), env.Path(self.path)
            path.create_directory()
            tmpdir.create_directory()
            update_args = (str(tmpdir), str(path), self.version, self.author, self.repo_name, False, False, "localhost", 1264)
            updater.update(*update_args)

            for progress_status in updater.receive_update_status("localhost", 1264):
                self.update_signal.emit(progress_status)

            self.update_signal.emit("Update done!")
        except Exception as e:
            self.update_signal.emit(f"Error: {e}")

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title = 'Updater'
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.path_input = QLineEdit(self)
        self.path_input.setPlaceholderText("Path")
        layout.addWidget(self.path_input)

        self.zip_path_input = QLineEdit(self)
        self.zip_path_input.setPlaceholderText("Zip Path")
        layout.addWidget(self.zip_path_input)

        self.version_input = QLineEdit(self)
        self.version_input.setPlaceholderText("Version")
        layout.addWidget(self.version_input)

        self.author_input = QLineEdit(self)
        self.author_input.setPlaceholderText("Author")
        layout.addWidget(self.author_input)

        self.repo_name_input = QLineEdit(self)
        self.repo_name_input.setPlaceholderText("Repo Name")
        layout.addWidget(self.repo_name_input)

        self.download_button = QPushButton("Update", self)
        self.download_button.clicked.connect(self.start_update_thread)
        layout.addWidget(self.download_button)

        self.info_box = QTextEdit(self)
        self.info_box.setReadOnly(True)
        layout.addWidget(self.info_box)

    def start_update_thread(self):
        self.update_thread = UpdateThread(self.path_input.text(), 
                                          self.zip_path_input.text(),
                                          self.version_input.text(), 
                                          self.author_input.text(), 
                                          self.repo_name_input.text())
        self.update_thread.update_signal.connect(self.update_info_box)
        self.update_thread.start_update()

    def update_info_box(self, text):
        self.info_box.append(text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec())
