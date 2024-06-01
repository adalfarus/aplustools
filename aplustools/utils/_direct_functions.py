from aplustools.package import install_dependencies_lst as _install_dependencies_lst
from typing import Iterable, Iterator, Callable, Any
import socket
import errno
import time


def reverse_map(functions: Iterable[Callable], *args, **kwargs):
    return [func(*args, **kwargs) for func in functions]


def gen_map(functions: Iterable[Callable], args_iter: Iterator[Any], kwargs_iter: Iterator[dict]):
    for func, args, kwargs in zip(functions, args_iter, kwargs_iter):
        yield func(*args, **kwargs)


def install_dependencies():
    success = _install_dependencies_lst(["Pillow==10.2.0", "cryptography==42.0.5", "brotli==1.1.0", "zstandard==0.22.0",
                                         "py7zr==0.21.0"])
    if not success:
        return
    print("Done, all possible dependencies for the utils module installed ...")


class PortUtils:
    @staticmethod
    def find_available_port():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))  # Bind to an available port provided by the OS
            return s.getsockname()[1]  # Return the allocated port

    @staticmethod
    def find_available_port_range(start_port, end_port):
        for port in range(start_port, end_port + 1):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
                    return port  # Port is available
            except OSError as e:
                if e.errno == errno.EADDRINUSE:  # Port is already in use
                    continue
                raise  # Reraise unexpected errors
        raise RuntimeError("No available ports in the specified range")

    @staticmethod
    def test_port(port, retries=5, delay=1):
        while retries > 0:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
                    return port
            except OSError as e:
                if e.errno == errno.EADDRINUSE:
                    retries -= 1
                    time.sleep(delay)
                else:
                    raise
        raise RuntimeError("Port is still in use after several retries")
