from aplustools._direct_functions import execute_python_command
from aplustools.io.environment import change_working_dir_to_script_location
import subprocess
import os
import shutil
import sys


def pype_command():
    """Pype"""
    if len(sys.argv) > 1:
        expression = ' '.join(sys.argv[1:])
        try:
            result = eval(expression)
            print(result)
        except Exception as e:
            print(f"Error: {e}")
    else:
        expression = input("Enter Python expression: ")
        try:
            result = eval(expression)
            print(result)
        except Exception as e:
            print(f"Error: {e}")


def upype_command():
    """Unified pype"""
    if len(sys.argv) > 1:
        # Join the arguments and split by ';'
        code = ' '.join(sys.argv[1:]).split(';')
        try:
            for line in code:
                # Strip leading and trailing whitespace and execute each line
                exec(line.strip())
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Enter Python code (type 'end' on a new line to finish):")
        lines = []
        while True:
            line = input("... ")
            if line == 'end':
                break
            lines.append(line)

        try:
            exec('\n'.join(lines))
        except Exception as e:
            print(f"Error: {e}")


class APTTestRunner:
    def install_pytest(self):
        print("Ensuring pytest is installed...")
        execute_python_command(["-m", "pip", "install", "pytest"])

    def prepare_test_directory(self, dir_name):
        if os.path.exists(dir_name):
            print(f"Clearing directory {dir_name}...")
            shutil.rmtree(dir_name)
        print(f"Creating directory {dir_name}...")
        os.mkdir(dir_name)

    def run_tests(self):
        print("Running tests...")
        subprocess.run(["pytest", "-vv", "tests"])


def run_tests():
    apt_test_runner = APTTestRunner()
    change_working_dir_to_script_location()
    apt_test_runner.install_pytest()
    apt_test_runner.prepare_test_directory("test_data")
    apt_test_runner.run_tests()
    print("Tests completed.")


if __name__ == "__main__":
    run_tests()
