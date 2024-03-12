from aplustools.data import updaters
import threading
from aplustools.io import environment as env
import sys

def main(path, zip_path, version, author, repo_name):
    # Set the working directory to the main script location
    env.set_working_dir_to_main_script_location()

    # Initialize the updater
    updater = updaters.gitupdater("exe")
    tmpdir, path = env.Path(zip_path), env.Path(path)

    # Setup arguments for the update
    host, port = "localhost", 1264
    #path.join("update") # path = 
    path.create_directory()
    #tmpdir = tmpdir.mkdir("update")
    tmpdir.create_directory()
    update_args = (str(tmpdir), str(path), 
                   version, author, repo_name, False, False, host, port)

    # Start the update in a new thread
    update_thread = threading.Thread(target=updater.update, args=update_args)
    update_thread.start()

    # Receive the update status generator and print them
    progress_bar = 1
    print("Starting update ...")
    for i in updater.receive_update_status(host, port):
        print(f"{i}%", end=f" PB{progress_bar}\n")
        if i == 100:
            progress_bar += 1 # Switch to second progress bar, when the downloading is finished

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
