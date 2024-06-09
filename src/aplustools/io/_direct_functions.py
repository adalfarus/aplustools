import multiprocessing as _multiprocessing
import subprocess as _subprocess
import threading as _threading
import platform as _platform
import ctypes as _ctypes
import psutil as _psutil
import struct as _struct
import sys as _sys
import os as _os

try:
    import msvcrt as _msvcrt
except Exception:
    _msvcrt = None


def diagnose_shutdown_blockers(suggestions: bool = True):
    blockers = []

    # Check for active threads
    active_threads = _threading.enumerate()
    if len(active_threads) > 1:  # More than just the main thread
        blockers.append(f"Active threads: {[thread.name for thread in active_threads]}")
        blockers.append("Suggestion: Ensure all threads complete or are set as daemon threads.")

    # Check for active processes
    current_process = _multiprocessing.current_process()
    child_processes = _psutil.Process(_os.getpid()).children(recursive=True)
    if child_processes:
        blockers.append(f"Active child processes: {[proc.pid for proc in child_processes]}")
        blockers.append("Suggestion: Ensure all child processes are "
                        "properly terminated using process.terminate() or process.join().")

    # Check for open files
    open_files = _psutil.Process(_os.getpid()).open_files()
    if open_files:
        blockers.append(f"Open files: {[file.path for file in open_files]}")
        blockers.append("Suggestion: Ensure all files are properly closed using file.close().")

    # Check for open network connections
    open_connections = _psutil.Process(_os.getpid()).connections()
    if open_connections:
        blockers.append(f"Open network connections: {open_connections}")
        blockers.append("Suggestion: Ensure all network connections are properly closed.")

    if not blockers:
        return "No obvious blockers preventing Python from shutting down."
    else:
        return "\n".join(blockers if suggestions else blockers[::2])


def clear_screen():
    if _platform.system() == "Windows":
        # Use ctypes to clear the screen for Windows
        kernel32 = _ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # -11 is the handle for STD_OUTPUT_HANDLE
        csbi = _ctypes.create_string_buffer(22)
        res = kernel32.GetConsoleScreenBufferInfo(handle, csbi)
        if res:
            (bufx, bufy, curx, cury, wattr, left, top, right, bottom,
            maxx, maxy) = _struct.unpack("hhhhHhhhhhh", csbi.raw)
            cells_in_screen = (bottom - top + 1) * (right - left + 1)
            written = _ctypes.c_int()
            kernel32.FillConsoleOutputCharacterA(handle, _ctypes.c_char(b' '), cells_in_screen, _ctypes.c_int(0), _ctypes.byref(written))
            kernel32.FillConsoleOutputAttribute(handle, wattr, cells_in_screen, _ctypes.c_int(0), _ctypes.byref(written))
            kernel32.SetConsoleCursorPosition(handle, _ctypes.c_int(0))
    else:
        # ANSI escape sequences for Unix-like systems
        print("\033[H\033[J", end="")


def enable_windows_ansi():
    if _platform.system() != "Windows":
        return
    # Constants from the Windows API
    STD_OUTPUT_HANDLE = -11
    ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004

    # Get the handle to the standard output
    kernel32 = _ctypes.WinDLL('kernel32', use_last_error=True)
    hstdout = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)

    # Get the current console mode
    mode = _ctypes.c_ulong()
    kernel32.GetConsoleMode(hstdout, _ctypes.byref(mode))

    # Set the ENABLE_VIRTUAL_TERMINAL_PROCESSING flag
    mode.value |= ENABLE_VIRTUAL_TERMINAL_PROCESSING

    # Update the console mode
    kernel32.SetConsoleMode(hstdout, mode)


def query_windows_terminal_cursor_position():
    if _platform.system() != "Windows":
        return
    # Send the DSR request
    _sys.stdout.write("\033[6n")
    _sys.stdout.flush()

    # Read the response (expecting format ESC[n;mR)
    response = ""
    while True:
        ch = _msvcrt.getwch()  # Get a character from the console without echo
        response += ch
        if ch == 'R':
            break

    # Parse the response to get the cursor position
    response = response.replace("\033[", "").rstrip('R')
    rows, cols = map(int, response.split(';'))
    return rows, cols


def open_path(path: str):
    if _platform.system() == "Windows":
        _subprocess.Popen(["explorer", path])
    elif _platform.system() == "Darwin":  # macOS
        _subprocess.Popen(["open", path])
    else:  # Linux, including Ubuntu
        _subprocess.Popen(["xdg-open", path])
