import requests
import subprocess

class gitupdater:
    def get_latest_version(author, repo_name):
        response = requests.get(f"https://api.github.com/repos/{author}/{repo_name}/releases/latest")
        response2 = requests.get(f"https://api.github.com/repos/{author}/{repo_name}/tags")
        repo_version = ''.join([x if sum(c.isnumeric() for c in x) >= 3 else "" for x in response.json()["name"].split("v")])
        repo_version_2 = response2.json()[0]["name"].replace("v", "")
        return repo_version, repo_version_2

    def update(path, zip_path, version, author, repo_name, ui_toggle, cmd_toggle):
        try:
            if bool(cmd_toggle):
                subprocess.run(["gitupdater-cmd.exe", str(path), str(zip_path), str(version), str(author), str(repo_name)])
            else:
                subprocess.run(["gitupdater.exe", str(path), str(zip_path), str(version), str(author), str(repo_name), str(ui_toggle)])
        except Exception as e:
            return False, e
        finally:
            return True
