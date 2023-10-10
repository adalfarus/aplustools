import requests
import zipfile
import sys
import os

def get_release_asset_download_url(owner, repo, tag, asset_name):
    releases_url = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag}"
    response = requests.get(releases_url)
    response.raise_for_status()
    data = response.json()

    for asset in data.get('assets', []):
        if asset['name'] == asset_name:
            return asset['browser_download_url']

    raise Exception(f"Asset with name '{asset_name}' not found.")

def main(path, zip_path, version, author, repo_name):
    # Define URL and download file
    url = get_release_asset_download_url(author, repo_name, f"v{version}", f"win-{version}.zip")
    response = requests.get(url, stream=True)

    # Get the parent directory of the specified path
    file_path = zip_path + f"/win-{version}.zip"
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
                print(f"Download in progress... {progress}%") # Print progress
    
    # Unpack zipfile into path var
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        total_files = len(zip_ref.namelist())
        extracted_files = 0
        for file in zip_ref.namelist():
            extracted_files += 1
            zip_ref.extract(file, path)
            progress = int(100 * extracted_files / total_files)
            print(f"Extraction in progress... {progress}%")
    
try:
    if len(sys.argv) >= 5: # If enough arguments were passed
        path = str(sys.argv[1]) # path e.g. ./save
        zip_path = str(sys.argv[2]) # Path of zip temp by default
        version = str(sys.argv[3]) # Version e.g. 1.0.0
        author = str(sys.argv[4]) # Author of repo
        repo_name = str(sys.argv[5]) # Repo name
    else:
        print("Not enough arguments provided. Please input them manually.")
        path = str(input("Path: "))
        zip_path = str(input("Zip_path: "))
        version = str(input("Version: "))
        author = str(input("Author: "))
        repo_name = str(input("Repo_name: "))
    main(path, zip_path, version, author, repo_name)
except Exception as e:
    print(f"Error: {e}")
finally:
    print("Update done!")

    if len(sys.argv) < 4:
        input("Press Enter to exit...")  # Wait for user input to exit
