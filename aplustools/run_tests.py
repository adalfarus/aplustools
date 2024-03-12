from aplustools.direct_functions import execute_python_command
from aplustools.io.environment import set_working_dir_to_main_script_location
import subprocess
import os
import shutil


def install_pytest():
    print("Ensuring pytest is installed...")
    execute_python_command(["-m", "pip", "install", "pytest"])


def prepare_test_directory(dir_name):
    if os.path.exists(dir_name):
        print(f"Clearing directory {dir_name}...")
        shutil.rmtree(dir_name)
    print(f"Creating directory {dir_name}...")
    os.mkdir(dir_name)


def run_tests():
    print("Running tests...")
    subprocess.run(["pytest", "tests"])


def main():
    set_working_dir_to_main_script_location()
    install_pytest()
    prepare_test_directory("test_data")
    run_tests()
    print("Tests completed.")
    input("Press Enter to continue...")


if __name__ == "__main__":
    main()
