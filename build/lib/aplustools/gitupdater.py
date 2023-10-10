import requests
import zipfile
import sys
import os
import socket

def get_release_asset_download_url(owner, repo, tag, asset_name):
    releases_url = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag}"
    response = requests.get(releases_url)
    response.raise_for_status()
    data = response.json()

    for asset in data.get('assets', []):
        if asset['name'] == asset_name:
            return asset['browser_download_url']

    raise Exception(f"Asset with name '{asset_name}' not found.")

def download_file(url, zip_path, version, connection):
    file_path = os.path.join(zip_path, f"win-{version}.zip")
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))

    with open(file_path, 'wb') as fd:
        for data in response.iter_content(chunk_size=4096):
            fd.write(data)
            progress = int(100 * fd.tell() / total_size)
            connection.sendall(f"Download progress: {progress}%".encode())
    
    return file_path

def main(path, zip_path, version, author, repo_name, connection):
    url = get_release_asset_download_url(author, repo_name, f"v{version}", f"win-{version}.zip")
    file_path = download_file(url, zip_path, version, connection)
    
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        total_files = len(zip_ref.namelist())
        extracted_files = 0
        for file in zip_ref.namelist():
            extracted_files += 1
            zip_ref.extract(file, path)
            progress = int(100 * extracted_files / total_files)
            connection.sendall(f"Extraction progress: {progress}%".encode())

    connection.sendall(b'Update complete.')

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Not enough arguments provided.")
        sys.exit()

    host = 'localhost'
    port = 5000

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen(1)
        print('Updater started. Waiting for the main application to connect...')
        conn, addr = s.accept()
        with conn:
            print('Connection established.')
            try:
                main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], conn)
            except Exception as e:
                print(f"Error: {e}")
                conn.sendall(f"Error: {e}".encode())
                