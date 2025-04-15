"""TBA"""
from ...io.fileio import *
import pytest
import os
import tempfile

# Standard typing imports for aps
import typing_extensions as _te
import collections.abc as _a
import typing as _ty
if _ty.TYPE_CHECKING:
    import _typeshed as _tsh
import types as _ts


@pytest.fixture
def temp_file_path() -> str:
    fd, path = tempfile.mkstemp()
    os.close(fd)
    return path


def test_is_fd_open_true_false() -> None:
    fd, path = tempfile.mkstemp()
    assert is_fd_open(fd) is True
    os.close(fd)
    assert is_fd_open(fd) is False


def test_basic_fd_wrapper_read_write_seek_tell(tmp_path) -> None:
    file_path = tmp_path / "test.txt"
    with open(file_path, "wb") as f:
        f.write(b"abc123")

    fd = os.open(file_path, os.O_RDWR)
    wrapper = BasicFDWrapper(fd, close_fd=False)

    assert wrapper.read(3) == b"abc"
    wrapper.seek(0)
    assert wrapper.tell() == 0
    assert isinstance(wrapper.isatty(), bool)

    wrapper.write(b"XYZ")
    wrapper.seek(0)
    result = wrapper.read()
    assert b"XYZ" in result

    wrapper.truncate()
    wrapper.close()
    os.close(fd)


def test_basic_file_lock(tmp_path) -> None:
    file_path = tmp_path / "lockme.txt"
    file_path.write_text("test")
    lock: BasicFileLock = BasicFileLock(filepath=str(file_path), open_mode="r")
    with lock.engage() as f:
        f: _ty.IO[str]
        assert lock.is_locked()
        assert f.read() == "test"
    lock.disengage()
    assert not lock.is_locked()


def test_os_file_lock(tmp_path) -> None:
    file_path = tmp_path / "oslock.txt"
    file_path.write_text("data")
    lock = OSFileLock(filepath=str(file_path))
    fd = lock.engage()
    assert isinstance(fd, int)
    assert lock.is_locked()
    lock.disengage()


def test_safe_file_writer(tmp_path) -> None:
    file_path = tmp_path / "safe.txt"
    file_path.write_text("Hello")
    writer = SafeFileWriter(path=str(file_path), open_func=open, mode="virtual")
    writer.write("hello")
    writer.flush()
    writer.close()
    assert file_path.read_text() == "hello"


def test_os_hyper_read_write(tmp_path) -> None:
    file_path = tmp_path / "hyper.txt"
    file_path.write_bytes(b"x" * 128)

    with pytest.raises(NotImplementedError):
        reader = os_hyper_read(filepath=str(file_path))
    # assert reader.read(10) == b"x" * 10
    # reader.close()
    #
    # writer = os_hyper_write(filepath=str(file_path))
    # writer.write(b"new data")
    # writer.close()
    #
    # assert b"new data" in file_path.read_bytes()


def test_os_open(tmp_path) -> None:
    file_path = tmp_path / "opened.txt"
    file_path.write_bytes(b"abc123")

    f = os_open(filepath=str(file_path), mode="r+b")
    assert isinstance(f.read(3), bytes)
    f.seek(0)
    f.write(b"xyz")
    f.truncate()
    f.close()
    assert file_path.read_bytes().startswith(b"xyz")
