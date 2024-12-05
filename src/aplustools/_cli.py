"""TBA"""
try:
    from .package.argumint import Argumint, ArgStructBuilder, EndPoint
except ImportError:
    from package.argumint import Argumint, ArgStructBuilder, EndPoint

import subprocess
import inspect
import shutil
import sys
import os


def _change_working_dir_to_script_location():  # Duplicate code
    try:
        if getattr(sys, 'frozen', False):
            # If the script is running as a bundled executable created by PyInstaller
            script_dir = os.path.dirname(sys.executable)
        else:
            # Get the path of the caller of this function
            frame = inspect.currentframe()
            caller_frame = frame.f_back
            caller_file = caller_frame.f_globals["__file__"]
            script_dir = os.path.dirname(os.path.abspath(caller_file))

        # Change the current working directory to the script directory
        os.chdir(script_dir)
        print(f"Working directory changed to {script_dir}")
    except Exception as e:
        print(f"An error occurred while changing the working directory: {e}")
        raise


def _execute_silent_python_command(command):  # Duplicate code
    with open(os.devnull, 'w') as devnull:
        result = subprocess.run([sys.executable] + command, stdout=devnull, stderr=devnull)
    return result


def _cli():
    def _run_tests(tests: list = None, debug: bool = False, minimal: bool = False):
        def _debug(*args, **kwargs):
            if debug:
                print(*args, **kwargs)
        if tests is None:
            tests = ["all"]
        _change_working_dir_to_script_location()
        os.chdir("../")  # To make the imports work properly
        _debug("Ensuring pytest is installed...")
        _execute_silent_python_command(["-m", "pip", "install", "pytest"])

        dir_name = "test_data"
        if os.path.exists(dir_name):
            _debug(f"Clearing directory {dir_name}...")
            shutil.rmtree(dir_name)
        _debug(f"Creating directory {dir_name}...")
        os.mkdir(dir_name)

        for test in tests:
            _debug("Running tests...")
            test = os.path.join("aplustools", test)
            if not minimal:
                result = subprocess.run(["pytest", "-s", "-q", "--tb=short", "--maxfail=1", "-p", "no:warnings"] + [test])  # "-vv",
            else:
                result = subprocess.run(["pytest", "--tb=short", "--maxfail=1", "-p", "no:warnings"] + [test])
            if result.returncode != 0:
                _debug(f"Tests failed for {test}.")
            else:
                _debug(f"Tests passed for {test}.")
        _debug("Tests completed.")

    builder = ArgStructBuilder()
    builder.add_command("aps")
    builder.add_nested_command("aps", "tests", "run")
    builder.add_subcommand("aps", "help")

    arg_struct = builder.get_structure()

    argu_mint = Argumint(EndPoint(lambda: print("Not implemented yet, sorry.")), arg_struct=arg_struct)
    argu_mint.add_endpoint("aps.tests.run", EndPoint(_run_tests))
    argu_mint.add_endpoint("aps.help", EndPoint(lambda: print("aps --> tests -> run {tests} {-debug} {-minimal}\n    |\n     -> help")))
    argu_mint.add_endpoint("aps", EndPoint(lambda: print("This command doesn't work like that, please use it like this:\n"
                                                "aps --> tests -> run {tests} {-debug} {-minimal}\n    |\n     -> help")))

    sys.argv[0] = "aps"

    argu_mint.parse_cli(sys, "native_light")


if __name__ == "__main__":
    _cli()
