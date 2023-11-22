import requests
import subprocess
import socket
import tempfile
from typing import Optional, Tuple, Generator, Union, List, Any
from packaging.version import Version, InvalidVersion
import sys
import os
import warnings

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
        
    def get_latest_version(self, author: str, repo_name: str) -> Union[Tuple[None, None], Tuple[str, str]]:
        try:
            response = requests.get(f"https://api.github.com/repos/{author}/{repo_name}/releases/latest")
            response2 = requests.get(f"https://api.github.com/repos/{author}/{repo_name}/tags")
            repo_version = ''.join([x if sum(c.isnumeric() for c in x) >= 3 else "" for x in response.json()["name"].split("v")])
            repo_version_2 = response2.json()[0]["name"].replace("v", "")
            return repo_version, repo_version_2
        except KeyError:
            print("Github repo not correctly set-up, please check the documentation and try again.")
        except Exception as e:
            print(f"Unexpected exception occured: {e}")
        return None, None
        
    def compare_release_numbers(self, release_version: str, release_version_2: str) -> Optional[str]:
        warnings.warn("This function is for an older version of this library, please stop using it as it will be removed in version 0.1.4. Use updaters.vNum instead.", 
                      DeprecationWarning, 
                      stacklevel=2)
        rv_1_lst = release_version.split(".")
        rv_2_lst = release_version_2.split(".")
        
        # Equalize the length of the lists by appending zeros
        rv_1_lst += [0] * (len(rv_2_lst) - len(rv_1_lst))
        rv_2_lst += [0] * (len(rv_1_lst) - len(rv_2_lst))

        for i, p in zip(rv_1_lst, rv_2_lst):
            i, p = int(i), int(p)
            if i != p:
                if i < p:
                    return release_version_2
                return release_version
        return None
    
    def compare_release_numbers_diff(self, release_version: str, release_version_2: str, join: Optional[bool]=True) -> Union[str, List[int]]:
        warnings.warn("This function is for an older version of this library, please stop using it as it will be removed in version 0.1.4. Use updaters.vNum instead.", 
                      DeprecationWarning, 
                      stacklevel=2)
        rv_1_lst = [int(i) for i in release_version.split(".")]
        rv_2_lst = [int(i) for i in release_version_2.split(".")]

        # Equalize the length of the lists by appending zeros
        rv_1_lst += [0] * (len(rv_2_lst) - len(rv_1_lst))
        rv_2_lst += [0] * (len(rv_1_lst) - len(rv_2_lst))

        diff = [str(p - i) for i, p in zip(rv_1_lst, rv_2_lst)]
        return ".".join(diff) if join else diff

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
                process = run_subprocess("gitupdater-cmd.exe") if self.version=="exe" else run_python_subprocess("gitupdater-cmd.py")
            elif bool(gui_toggle) and not bool(cmd_toggle):
                process = run_subprocess("gitupdater-gui.exe") if self.version=="exe" else run_python_subprocess("gitupdater-gui.py")
            elif not bool(cmd_toggle) and not bool(gui_toggle):
                process = run_subprocess("gitupdater.exe") if self.version=="exe" else run_python_subprocess("gitupdater.py")
            else:
                raise RuntimeError()
        except Exception as e:
            return False, e, process.returncode
        finally:
            return True, None, process.returncode
