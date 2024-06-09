import subprocess as _subprocess
import sys as _sys
import os as _os
import warnings as _warnings
import typing as _typing


def execute_python_command(arguments: _typing.Optional[list] = None, *args, **kwargs) -> _subprocess.CompletedProcess[str]:
    if arguments is None:
        arguments = []
    print(' '.join([_sys.executable] + arguments))
    # Added to remain consistent with executing in the same python environment
    return _subprocess.run([_sys.executable] + arguments, *args, **kwargs)


# def interruptCTRL():
#     """Simulates a hard user CTRL+C exit. This means it skips any try ... except KeyboardInterrupts"""
#     exit(-1073741510)  # 130 / 0xC000013A


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
