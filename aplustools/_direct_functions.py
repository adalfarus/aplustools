import subprocess
import sys
import os
import warnings


def execute_python_command(arguments: list = None, *args, **kwargs) -> subprocess.CompletedProcess[str]:
    if arguments is None:
        arguments = []
    print(' '.join([sys.executable] + arguments))
    # Added to remain consistent with executing in the same python environment
    return subprocess.run([sys.executable] + arguments, *args, **kwargs)


def interruptCTRL():
    """
    Simulates a user CTRL+C exit.
    """
    exit(-1073741510)  # 130


def install_all_dependencies():
    for dep in ["requests==2.31.0",
                "Pillow==10.2.0",
                "BeautifulSoup4==4.12.3",
                "duckduckgo_search==3.9.3",
                "rich==13.7.0",
                "pycryptodome==3.20.0",
                "PySide6==6.6.1",
                "aiohttp==3.9.3",
                "asyncio==3.4.3",
                "opencv-python==4.9.0.80"]:
        try:
            proc = execute_python_command(arguments=
                                          ["-m", "pip", "install", dep])
            if proc.returncode != 0:
                raise
        except Exception as e:
            print("An error occurred:" + str(e))

    print("Done, all possible dependencies installed ...")


def set_dir_to_ex():
    import __main__
    # Get the directory where the main script (or frozen exe) is located
    if getattr(sys, 'frozen', False):
        # If the script is running as a bundled executable created by e.g. PyInstaller
        main_dir = os.path.dirname(sys.executable)
    else:
        # If the script is running as a normal Python script
        if hasattr(__main__, '__file__'):
            main_dir = os.path.dirname(os.path.abspath(__main__.__file__))
        else:
            main_dir = os.path.dirname(os.getcwd())
            warnings.warn(
                "Could not set the current working directory to the location of the main script or executable",
                RuntimeWarning,
                stacklevel=2
            )
    # Change the current working directory to the main script directory
    os.chdir(main_dir)
