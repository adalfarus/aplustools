import requests
import subprocess
import socket
import tempfile

def get_temp():
    return tempfile.gettempdir()

class gitupdater:
    def __init__(self, version="exe"):
        self.version = version
        
    def get_latest_version(self, author, repo_name):
        response = requests.get(f"https://api.github.com/repos/{author}/{repo_name}/releases/latest")
        response2 = requests.get(f"https://api.github.com/repos/{author}/{repo_name}/tags")
        repo_version = ''.join([x if sum(c.isnumeric() for c in x) >= 3 else "" for x in response.json()["name"].split("v")])
        repo_version_2 = response2.json()[0]["name"].replace("v", "")
        return repo_version, repo_version_2
        
    def reveive_update_status(self, host='localhost', port=5000):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            while True:
                data s.recv(1024)
                if data:
                    yield data.decode()
                else:
                    print("Connection closed by updater.")
                    break
        
    def update(self, path, zip_path, version, author, repo_name, gui_toggle=0, cmd_toggle=0):
        try:
            if bool(cmd_toggle) and not bool(ui_toggle):
                subprocess.run([f"gitupdater-cmd.{self.version}", str(path), str(zip_path), str(version), str(author), str(repo_name)])
            elif bool(gui_toggle) and not bool(cmd_toggle):
                subprocess.run([f"gitupdater-gui.{self.version}", str(path), str(zip_path), str(version), str(author), str(repo_name)])
            elif not bool(cmd_toggle) and not bool(ui_toggle):
                subprocess.run([f"gitupdater.{self.version}", str(path), str(zip_path), str(version), str(author), str(repo_name)])
            else:
                raise RuntimeError()
        except Exception as e:
            return False, e
        finally:
            return True
