import sys
import requests
import zipfile
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QTextEdit
from PyQt5.QtCore import QThread, pyqtSignal
import warnings


warnings.warn("This package doesn't include PyQt5 anymore, so this is deprecated. Please use the executable instead.", DeprecationWarning, stacklevel=2)

class DownloadThread(QThread):
    signal = pyqtSignal('PyQt_PyObject')

    def __init__(self, path, zip_path, version, author, repo_name):
        QThread.__init__(self)
        self.path = path
        self.zip_path = zip_path
        self.version = version
        self.author = author
        self.repo_name = repo_name

    # Define your methods
    def run(self):
        try:
            self.download_and_extract()
        except Exception as e:
            self.signal.emit(f"Error: {str(e)}")
        finally:
            self.signal.emit("Update done!")

    # Rest of your code
    def get_release_asset_download_url(self, owner, repo, tag, asset_name):
        releases_url = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag}"
        response = requests.get(releases_url)
        response.raise_for_status()
        data = response.json()

        for asset in data.get('assets', []):
            if asset['name'] == asset_name:
                return asset['browser_download_url']

        raise Exception(f"Asset with name '{asset_name}' not found.")

    def download_and_extract(self):
        # Define URL and download file
        url = self.get_release_asset_download_url(self.author, self.repo_name, f"v{self.version}", f"win-{self.version}.zip")
        response = requests.get(url, stream=True)

        # Get the parent directory of the specified path
        file_path = self.zip_path + f"/win-{self.version}.zip"
        with open(file_path, 'wb') as fd:
            total_size = response.headers.get('content-length')
            if total_size is None:  # no content length header
                fd.write(response.content)
            else:
                dl = 0
                total_size = int(total_size)
                for data in response.iter_content(chunk_size=4096):
                    dl += len(data)
                    fd.write(data)
                    progress = int(100 * dl / total_size)
                    self.signal.emit(f"Download in progress... {progress}%") # signal emit progress
        
        # Unpack zipfile into path var
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            total_files = len(zip_ref.namelist())
            extracted_files = 0
            for file in zip_ref.namelist():
                extracted_files += 1
                zip_ref.extract(file, self.path)
                progress = int(100 * extracted_files / total_files)
                self.signal.emit(f"Extraction in progress... {progress}%")


class App(QWidget):
    def __init__(self, switch):
        super().__init__()
        self.title = 'Download and Extract'
        self.switch = switch
        if not bool(self.switch):
            self.initUI()
        else:
            self.initUI2()

    def initUI(self):
        self.setWindowTitle(self.title)

        # Create widgets
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.path_input = QLineEdit(self)
        self.path_input.setPlaceholderText("Path")
        layout.addWidget(self.path_input)

        self.zip_path_input = QLineEdit(self)
        self.zip_path_input.setPlaceholderText("Zip_path")
        layout.addWidget(self.zip_path_input)

        self.version_input = QLineEdit(self)
        self.version_input.setPlaceholderText("Version")
        layout.addWidget(self.version_input)

        self.author_input = QLineEdit(self)
        self.author_input.setPlaceholderText("Author")
        layout.addWidget(self.author_input)

        self.repo_name_input = QLineEdit(self)
        self.repo_name_input.setPlaceholderText("Repo_name")
        layout.addWidget(self.repo_name_input)

        self.download_button = QPushButton("Download", self)
        self.download_button.clicked.connect(self.start_download_thread)
        layout.addWidget(self.download_button)

        self.info_box = QTextEdit(self)
        self.info_box.setReadOnly(True)
        layout.addWidget(self.info_box)
        
    def initUI2(self):
        self.setWindowTitle(self.title)

        # Create widgets
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.download_button = QPushButton("Download", self)
        self.download_button.clicked.connect(self.start_download_thread)
        layout.addWidget(self.download_button)

        self.info_box = QTextEdit(self)
        self.info_box.setReadOnly(True)
        layout.addWidget(self.info_box)

    def start_download_thread(self):
        if not bool(self.switch):
            self.download_thread = DownloadThread(self.path_input.text(), self.zip_path_input.text(), 
                                                  self.version_input.text(), self.author_input.text(), 
                                                  self.repo_name_input.text())
        else:
            self.path = str(sys.argv[1]) # path e.g. ./save
            self.zip_path = str(sys.argv[2]) # Path of zip temp by default
            self.version = str(sys.argv[3]) # Version e.g. 1.0.0
            self.author = str(sys.argv[4]) # Author of repo
            self.repo_name = str(sys.argv[5]) # Repo name
            self.download_thread = DownloadThread(self.path, self.zip_path, 
                                                  self.version, self.author, 
                                                  self.repo_name)
        self.download_thread.signal.connect(self.update_info_box)
        self.download_thread.start()

    def update_info_box(self, text):
        self.info_box.append(text)

try:
    if len(sys.argv) >= 5: # If enough arguments were passed
        switch = 1
    else:
        switch = 0
    app = QApplication(sys.argv)
    ex = App(switch)
    ex.show()
    sys.exit(app.exec_())
except Exception as e:
    print(f"Error: {e}")
finally:
    print("Update done!")

    if len(sys.argv) < 4:
        print("Press Enter to exit...")  # Wait for user input to exit
