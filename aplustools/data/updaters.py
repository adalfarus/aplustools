import requests
import subprocess
import socket
import tempfile
from typing import Optional, Tuple, Generator, Union, List, Any
from packaging.version import Version, InvalidVersion
import sys
import os
import warnings
from collections import namedtuple # Can be removed if executables are added and the code to execute them here is re-instated

YieldType = Union[int, None]
ReturnType = Union[None, bool]
UpdateStatusGenerator = Generator[YieldType, None, ReturnType]


def get_temp():
    return tempfile.gettempdir()


class vNum:
    def __init__(self, number: str):
        try:
            self.version = Version(number)
        except InvalidVersion:
            raise ValueError(f"Invalid version number: {number}")

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, vNum):
            return self.version < other.version
        elif isinstance(other, str):
            try:
                other = Version(other)
                return self.version < other
            except InvalidVersion:
                raise ValueError(f"Invalid version number: {other}")
        return NotImplemented

    def __le__(self, other: Any) -> bool:
        if isinstance(other, vNum):
            return self.version <= other.version
        elif isinstance(other, str):
            try:
                other = Version(other)
                return self.version <= other
            except InvalidVersion:
                raise ValueError(f"Invalid version number: {other}")
        return NotImplemented

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, vNum):
            return self.version == other.version
        elif isinstance(other, str):
            try:
                other = Version(other)
                return self.version == other
            except InvalidVersion:
                raise ValueError(f"Invalid version number: {other}")
        return NotImplemented

    def __ne__(self, other: Any) -> bool:
        if isinstance(other, vNum):
            return self.version != other.version
        elif isinstance(other, str):
            try:
                other = Version(other)
                return self.version != other
            except InvalidVersion:
                raise ValueError(f"Invalid version number: {other}")
        return NotImplemented

    def __gt__(self, other: Any) -> bool:
        if isinstance(other, vNum):
            return self.version > other.version
        elif isinstance(other, str):
            try:
                other = Version(other)
                return self.version > other
            except InvalidVersion:
                raise ValueError(f"Invalid version number: {other}")
        return NotImplemented

    def __ge__(self, other: Any) -> bool:
        if isinstance(other, vNum):
            return self.version >= other.version
        elif isinstance(other, str):
            try:
                other = Version(other)
                return self.version >= other
            except InvalidVersion:
                raise ValueError(f"Invalid version number: {other}")
        return NotImplemented

    def __str__(self) -> str:
        return str(self.version)


class gitupdater:
    def __init__(self, version: str="exe"):
        self.version = version

    @staticmethod
    def get_latest_version(author: str, repo_name: str) -> Union[Tuple[None, None], Tuple[str, str]]:
        try:
            response = requests.get(f"https://api.github.com/repos/{author}/{repo_name}/releases/latest")
            response2 = requests.get(f"https://api.github.com/repos/{author}/{repo_name}/tags")
            repo_version = ''.join([x if sum(c.isnumeric() for c in x) >= 3 else "" for x in response.json()["name"].split("v")])
            repo_version_2 = response2.json()[0]["name"].replace("v", "")
            return repo_version, repo_version_2
        except KeyError:
            print("Github repo not correctly set-up, please check the documentation and try again.")
        except Exception as e:
            print(f"Unexpected exception occurred: {e}")
        return None, None
        
    def receive_update_status(self, host: str='localhost', port: int=5000) -> UpdateStatusGenerator:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, port))
                bool_map = {'True': True, 'False': False}
                try:
                    while True:
                        data = s.recv(1024)
                        if data:
                            decoded_data = data.decode()
                            if "Error" in decoded_data: print(f"Error occurred: {decoded_data}")
                            elif "Connection" in decoded_data: print(decoded_data)
                            elif decoded_data in bool_map:
                                success = bool_map[decoded_data]
                            else:
                                str_progress_values = decoded_data.split("\n")
                                progress_values = [int(p) for p in str_progress_values if p]
                                for progress_value in progress_values: yield progress_value
                        else:
                            print("Connection closed by updater.")
                            return success
                except ConnectionError as e:
                    print(f"Connection Error: {e}")
        except ConnectionRefusedError:
            print("Connection Refused, maybe your updater isn't running?")
        except Exception as e:
            print(f"Unexpected exception occurred: {e}")
        return None
        
    def update(self, path: str, zip_path: str, version: str, author: str, 
               repo_name: str, gui_toggle: bool=False, cmd_toggle: bool=False, 
               host: str="localhost", port: int=5000, non_blocking: Optional[bool]=False
    ) -> Union[Tuple[bool, None, int], Tuple[bool, Exception, int]]:
        lib_path = os.path.dirname(os.path.abspath(__file__))
        def run_subprocess(file):
            return subprocess.run([os.path.join(lib_path, file), str(path), str(zip_path), str(version), str(author), str(repo_name), str(host), str(port)], shell=True, text=True, capture_output=True)
        def run_python_subprocess(file):
            return subprocess.run([sys.executable, os.path.join(lib_path, file), str(path), str(zip_path), str(version), str(author), str(repo_name), str(host), str(port)], shell=True, text=True, capture_output=True)
        try:
            if bool(cmd_toggle) and not bool(gui_toggle):
                if self.version=="exe":
                    print("Executable Updaters have to be compiled by you now.")
                    ProcessResult = namedtuple('ProcessResult', 'returncode')
                    process = ProcessResult(returncode=0)
                    #process = run_subprocess("gitupdater-cmd.exe")
                else: process = run_python_subprocess("gitupdater-cmd.py")
            elif bool(gui_toggle) and not bool(cmd_toggle):
                if self.version=="exe":
                    print("Executable Updaters have to be compiled by you now.")
                    ProcessResult = namedtuple('ProcessResult', 'returncode')
                    process = ProcessResult(returncode=0)
                    #process = run_subprocess("gitupdater-gui.exe")
                else: process = run_python_subprocess("gitupdater-gui.py")
            elif not bool(cmd_toggle) and not bool(gui_toggle):
                if self.version=="exe":
                    print("Executable Updaters have to be compiled by you now.")
                    ProcessResult = namedtuple('ProcessResult', 'returncode')
                    process = ProcessResult(returncode=0)
                    #process = run_subprocess("gitupdater.exe")
                else: process = run_python_subprocess("gitupdater.py")
            else:
                raise RuntimeError()
        except Exception as e:
            return False, e, process.returncode
        finally:
            return True, None, process.returncode


def local_test():
    try:
        import threading
        from aplustools.io.environment import Path
    
        # Initialize the updater
        updater = gitupdater("exe")

        # Setup arguments for the update
        host, port = "localhost", 1264
        path, zip_path = Path("./test_data/update"), Path("./test_data/zip")
        path.mkdir("."); zip_path.mkdir(".")
        version, author, repo_name = "0.0.1", "Adalfarus", "unicode-writer"
    
        update_args = (str(zip_path), str(path), 
                       version, author, repo_name, False, False, host, port)

        # Start the update in a new thread
        update_thread = threading.Thread(target=updater.update, args=update_args)
        update_thread.start()

        # Receive the update status generator and print them
        progress_bar = 1
        print("Starting test update ...")
        for i in updater.receive_update_status(host, port):
            print(f"{i}%", end=f" PB{progress_bar}\n")
            if i == 100:
                progress_bar += 1 # Switch to second progress bar, when the downloading is finished
    except Exception as e:
        print(f"Exception occurred {e}.")
        return False
    else:
        print("Test completed successfully.")
        return True


if __name__ == "__main__":
    local_test()
