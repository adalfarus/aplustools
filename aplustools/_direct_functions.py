import subprocess as _subprocess
import sys as _sys
import os as _os
import warnings as _warnings
from aplustools.package import install_dependencies_lst as _install_dependencies_lst
from typing import Optional as _Optional
from aplustools.package.argumint import EndPoint as _EndPoint


def what_func(func, type_names: bool = False):
    endpoint = _EndPoint(func)
    arguments_str = ''.join([f"{argument.name}: "
                             f"{(argument.type or type(argument.default)).__name__ if type_names else argument.type or type(argument.default)}"
                             f" = {argument.default}, " for argument in endpoint.arguments])[:-2]
    print(f"{func.__module__}.{endpoint.name}({arguments_str}){(' -> ' + str(endpoint.return_type)) if endpoint.return_type is not None else ''}")


def execute_python_command(arguments: _Optional[list] = None, *args, **kwargs) -> _subprocess.CompletedProcess[str]:
    if arguments is None:
        arguments = []
    print(' '.join([_sys.executable] + arguments))
    # Added to remain consistent with executing in the same python environment
    return _subprocess.run([_sys.executable] + arguments, *args, **kwargs)


def interruptCTRL():
    """Simulates a hard user CTRL+C exit. This means it skips any try ... except KeyboardInterrupts"""
    exit(-1073741510)  # 130 / 0xC000013A


def install_all_dependencies():
    success = _install_dependencies_lst(["requests==2.31.0", "Pillow==10.3.0", "BeautifulSoup4==4.12.3",
                                         "duckduckgo_search==3.9.3", "cryptography==42.0.5", "PySide6==6.6.1",
                                         "aiohttp==3.9.4", "opencv-python==4.9.0.80", "brotli==1.1.0",
                                         "zstandard==0.22.0", "py7zr==0.21.0", "pillow_heif==0.15.0", "numpy==1.26.4"])
    if not success:
        return
    print("Done, all possible dependencies installed ...")


def set_dir_to_ex():
    import __main__
    # Get the directory where the main script (or frozen exe) is located
    if getattr(_sys, 'frozen', False):
        # If the script is running as a bundled executable created by e.g. PyInstaller
        main_dir = _os.path.dirname(_sys.executable)
    else:
        # If the script is running as a normal Python script
        if hasattr(__main__, '__file__'):
            main_dir = _os.path.dirname(_os.path.abspath(__main__.__file__))
        else:
            main_dir = _os.path.dirname(_os.getcwd())
            _warnings.warn(
                "Could not set the current working directory to the location of the main script or executable",
                RuntimeWarning,
                stacklevel=2
            )
    # Change the current working directory to the main script directory
    _os.chdir(main_dir)


if __name__ == "__main__":
    what_func(lambda x=1, y=2: 1, True)
