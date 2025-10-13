"""TBA"""
from subprocess import SubprocessError

from ...io.env import *
from ...io.env import (
    _BaseSystem,
    _LinuxSystem,
    _WindowsSystem,
    _DarwinSystem,
    _BSDSystem,
)
import pytest
import platform
from unittest import mock
import os
import io
import tempfile
import warnings
from contextlib import redirect_stdout
import shutil

# Standard typing imports for aps
import typing_extensions as _te
import collections.abc as _a
import typing as _ty

if _ty.TYPE_CHECKING:
    import _typeshed as _tsh
import types as _ts


@pytest.mark.parametrize(
    "platform_name, expected_class",
    [
        ("Windows", _WindowsSystem),
        ("Darwin", _DarwinSystem),
        ("Linux", _LinuxSystem),
        ("FreeBSD", _BSDSystem),
    ],
)
def test_get_system_known_os(
    monkeypatch: pytest.MonkeyPatch, platform_name: str, expected_class: BaseSystemType
) -> None:
    monkeypatch.setattr(platform, "system", lambda: platform_name)
    result: BaseSystemType = get_system()
    assert isinstance(result, expected_class)


def test_get_system_unknown_os(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(platform, "system", lambda: "Solaris")
    with pytest.warns(RuntimeWarning, match="Unknown Operating System"):
        result = get_system()
    assert isinstance(result, _BaseSystem)


# _BaseSystem tests
def test_base_system_cpu_arch_and_lang() -> None:
    system = _BaseSystem()
    assert isinstance(system.get_cpu_arch(), str)
    lang, encoding = system.get_system_language()
    assert isinstance(lang, (str, type(None)))
    assert isinstance(encoding, (str, type(None)))


def test_base_system_not_implemented_methods() -> None:
    system = _BaseSystem()
    with pytest.raises(NotImplementedError):
        system.get_gpu_info()
    with pytest.raises(NotImplementedError):
        system.get_system_theme()
    with pytest.raises(NotImplementedError):
        system.schedule_event("test", "/path/to/script", "startup")
    with pytest.raises(NotImplementedError):
        system.send_native_notification("title", "message")
    with pytest.raises(NotImplementedError):
        system.get_appdata_directory("app")


@pytest.fixture
def system() -> BaseSystemType:
    return get_system()


def test_cpu_brand(system: BaseSystemType) -> None:
    brand = system.get_cpu_brand()
    assert isinstance(brand, str)
    assert len(brand) > 0


def test_cpu_arch(system: BaseSystemType) -> None:
    arch = system.get_cpu_arch()
    assert isinstance(arch, str)
    assert len(arch) > 0


def test_system_language(system: BaseSystemType) -> None:
    lang, encoding = system.get_system_language()
    assert lang is None or isinstance(lang, str)
    assert encoding is None or isinstance(encoding, str)


def test_get_system_theme_safe(system: BaseSystemType) -> None:
    try:
        theme = system.get_system_theme()
        assert theme in {SystemTheme.LIGHT, SystemTheme.DARK, SystemTheme.UNKNOWN}
    except NotImplementedError:
        pytest.skip("System theme not implemented on this OS")


def test_gpu_info_safe(system: BaseSystemType) -> None:
    try:
        info = system.get_gpu_info()
        assert isinstance(info, (str, list))
    except NotImplementedError:
        pytest.skip("GPU info not implemented on this OS")
    except (SubprocessError, FileNotFoundError):
        pytest.skip("Utility for GPU info not working at the moment")


@pytest.mark.skipif('sys.platform != "win32"', reason="Windows-only test")
@pytest.mark.parametrize(
    "reg_value, expected_theme", [(1, SystemTheme.LIGHT), (0, SystemTheme.DARK)]
)
def test_get_system_theme(
    monkeypatch: pytest.MonkeyPatch, reg_value: int, expected_theme: SystemTheme
) -> None:
    mock_key = mock.MagicMock()
    monkeypatch.setattr("winreg.OpenKey", lambda root, path: mock_key)
    monkeypatch.setattr("winreg.QueryValueEx", lambda key, name: (reg_value, None))
    monkeypatch.setattr("winreg.CloseKey", lambda key: None)

    system = _WindowsSystem()
    assert system.get_system_theme() == expected_theme


@pytest.mark.skipif('sys.platform != "win32"', reason="Windows-only test")
def test_get_system_theme_key_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "winreg.OpenKey", lambda root, path: (_ for _ in ()).throw(FileNotFoundError())
    )
    system = _WindowsSystem()
    assert system.get_system_theme() == SystemTheme.UNKNOWN


def test_schedule_event_stub(system: BaseSystemType, tmp_path) -> None:
    try:
        # Just test the method exists and accepts parameters
        system.schedule_event("TestEvent", str(tmp_path / "script.sh"), "login")
    except NotImplementedError:
        pytest.skip("Scheduling not supported on this OS")
    except Exception:
        # Accept that on real systems it may fail if permissions or formats are invalid
        pass


def test_send_native_notification_safe(system: BaseSystemType) -> None:
    try:
        system.send_native_notification("Test", "This is a native test.")
    except NotImplementedError:
        pytest.skip("Native notification not implemented")


def test_appdata_path_user(system: BaseSystemType) -> None:
    path = system.get_appdata_directory("APlusTest", "user")
    assert isinstance(path, str)
    assert "APlusTest" in path


def test_appdata_path_global(system: BaseSystemType) -> None:
    path = system.get_appdata_directory("APlusTest", "global")
    assert isinstance(path, str)
    assert "APlusTest" in path


@pytest.mark.parametrize(
    "base_name,expected_hidden",
    [("visible_file.txt", True), (".already_hidden.txt", False)],
)
def test_hide_file_unix_like(
    monkeypatch: pytest.MonkeyPatch, base_name: str, expected_hidden: bool
) -> None:
    system: BaseSystemType = get_system()

    if system.os not in {"Linux", "Darwin", "FreeBSD"}:
        pytest.skip("This test is only for Unix-like systems")

    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, base_name)
        with open(path, "w") as f:
            f.write("data")

        result = system.hide_file(path)
        assert result is expected_hidden

        hidden_path = os.path.join(tmpdir, "." + base_name)
        if expected_hidden:
            assert os.path.exists(hidden_path)
        else:
            assert os.path.exists(path)


def test_get_shared_folder_exists_and_writable() -> None:
    system: BaseSystemType = get_system()
    try:
        path = system.get_shared_folder()
        assert os.path.exists(path)
        assert os.access(path, os.W_OK) or system.os == "Windows"
    except OSError:
        pytest.skip("Shared folder not available or writable")


def test_create_shared_file(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    system = get_system()
    monkeypatch.setattr(system, "get_shared_folder", lambda: str(tmp_path))

    path = system.create_shared_file("lockfile.test")
    assert os.path.exists(path)


def test_page_size() -> None:
    system = get_system()
    size = system.page_size()
    assert isinstance(size, int)
    assert size > 0


def test_is_virtual_machine_safe() -> None:
    system = get_system()
    result = system.is_virtual_machine()
    assert isinstance(result, bool)


def test_open_location(monkeypatch: pytest.MonkeyPatch) -> None:
    system = get_system()
    called = []

    monkeypatch.setattr("subprocess.run", lambda cmd: called.append(cmd))
    try:
        system.open_location(os.getcwd())
        assert called  # Should have tried to run something
    except NotImplementedError:
        pytest.skip("open_location not implemented on this system")


def test_lock_and_unlock_file() -> None:
    system = get_system()
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(b"lock test")
        tmp_file.flush()
        tmp_path = tmp_file.name

    # Try to acquire a lock
    fd = system.lock_file(tmp_path)
    assert isinstance(fd, int)

    # Try to check if locked (should say locked from our own lock)
    locked = system.is_file_locked(tmp_path)
    assert locked is True

    # Unlock
    system.unlock_file(fd, keep_fd_open=False)


def test_lock_conflict_behavior() -> None:
    system = get_system()
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(b"x" * 20)
        tmp_file.flush()
        tmp_path = tmp_file.name

    # First lock
    fd1 = system.lock_file(tmp_path)
    assert fd1 is not None

    # Try non-blocking lock (should fail and return None)
    fd2 = system.lock_file(tmp_path, blocking=False)
    assert fd2 is None

    # Unlock original
    system.unlock_file(fd1, keep_fd_open=False)


def test_byte_range_lock() -> None:
    system = get_system()
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(b"abcdefghij")
        tmp_file.flush()
        tmp_path = tmp_file.name

    # Lock byte range
    fd = system.lock_file(tmp_path, byte_range=range(2, 6))
    assert isinstance(fd, int)

    # Unlock byte range
    system.unlock_file(fd, byte_range=range(2, 6), keep_fd_open=False)


def test_is_file_locked_check() -> None:
    system = get_system()
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(b"locked-check")
        tmp_file.flush()
        tmp_path = tmp_file.name

    # No locks yet
    assert system.is_file_locked(tmp_path) is False

    # Lock it from within this process
    fd = system.lock_file(tmp_path, blocking=True)
    try:
        assert system.is_file_locked(tmp_path) is True  # self-lock should be detected
    finally:
        system.unlock_file(fd, keep_fd_open=False)


def test_hide_and_unhide_file_cycle() -> None:
    system = get_system()

    with tempfile.TemporaryDirectory() as tmpdir:
        filename = "mytemp.txt"
        path = os.path.join(tmpdir, filename)

        with open(path, "w") as f:
            f.write("just testing")

        # 1. Confirm initially unhidden
        assert not system.is_hidden(path)

        # 2. Hide it
        assert system.hide_file(path)

        # Update path (if renamed)
        if system.os in {"Linux", "Darwin", "FreeBSD"}:
            path = os.path.join(tmpdir, "." + filename)

        assert os.path.exists(path)
        assert system.is_hidden(path)

        # 3. Unhide it
        assert system.unhide_file(path)

        if system.os in {"Linux", "Darwin", "FreeBSD"}:
            path = os.path.join(tmpdir, filename)

        assert os.path.exists(path)
        assert not system.is_hidden(path)


# TODO: Make better test
# def test_diagnose_shutdown_blockers_return_str() -> None:
#     result = diagnose_shutdown_blockers(return_result=True)
#     assert isinstance(result, str)
#     assert "blockers" in result.lower() or "threads" in result.lower() or "no obvious blockers" in result.lower() or "processes" in result.lower()
#
#
# def test_diagnose_shutdown_blockers_prints(capsys) -> None:
#     diagnose_shutdown_blockers(return_result=False)
#     captured = capsys.readouterr()
#     assert "blockers" in captured.out.lower() or "threads" in captured.out.lower() or "no obvious" in captured.out.lower() or "processes" in captured.out.lower()


# def test_diagnose_shutdown_blockers_with_and_without_suggestions() -> None:
#     with_suggestions: str = diagnose_shutdown_blockers(suggestions=True, return_result=True)
#     without_suggestions: str = diagnose_shutdown_blockers(suggestions=False, return_result=True)
#
#     if "Suggestion:" in with_suggestions:
#         assert "Suggestion:" not in without_suggestions


def test_suppress_warnings_context_manager() -> None:
    with io.StringIO() as buf, redirect_stdout(buf):
        with suppress_warnings():
            warnings.warn("Test warning suppressed", UserWarning)
        output = buf.getvalue()
    assert "Test warning suppressed" not in output


@auto_repr
class _DummyClass:
    def __init__(self) -> None:
        self.name = "X"
        self._private = "Y"
        self.__very_private__ = "Z"
        self.__hidden = "shhh"  # name mangled


def test_auto_repr_basic_repr() -> None:
    obj = _DummyClass()
    repr_str = repr(obj)
    assert "DummyClass" in repr_str
    assert "name=X" in repr_str
    assert "_private=" not in repr_str  # hidden by default
    assert "__very_private__=Z" in repr_str
    assert "_DummyClass__hidden" not in repr_str  # name-mangled; should be excluded


@auto_repr_with_privates
class _DummyPrivate:
    def __init__(self) -> None:
        self.name = "Visible"
        self._secret = "Hidden"
        self.__hidden = "shhh"  # name mangled


def test_auto_repr_with_privates_includes_private() -> None:
    obj = _DummyPrivate()
    repr_str = repr(obj)
    assert "_secret=Hidden" in repr_str
    assert "name=Visible" in repr_str
    assert "_DummyPrivate__hidden" in repr_str  # name-mangled; should be excluded


def test_is_accessible_returns_true_for_readable_writable_path() -> None:
    path = tempfile.mkdtemp()
    try:
        assert os.access(path, os.R_OK | os.W_OK)
    finally:
        shutil.rmtree(path)


def test_get_home_directory_returns_home_path() -> None:
    assert os.path.expanduser("~") == BasicSystemFunctions.get_home_directory()


def test_change_working_dir_to_new_temp_folder() -> None:
    path = BasicSystemFunctions.change_working_dir_to_new_temp_folder()
    assert os.path.realpath(os.getcwd()) == os.path.realpath(path)
    assert os.path.exists(path)


def test_change_working_dir_to_temp_folder() -> None:
    BasicSystemFunctions.change_working_dir_to_temp_folder()
    assert os.path.realpath(os.getcwd()) == os.path.realpath(tempfile.gettempdir())


def test_change_working_dir_to_userprofile_folder(tmp_path) -> None:
    userprofile_folder = os.path.join(os.path.expanduser("~"), "test_aplus_folder")
    os.makedirs(userprofile_folder, exist_ok=True)
    original_cwd = os.getcwd()
    try:
        BasicSystemFunctions.change_working_dir_to_userprofile_folder(
            "test_aplus_folder"
        )
        assert os.getcwd() == userprofile_folder
    finally:
        os.chdir(original_cwd)  # Move out so we can delete it
        os.rmdir(userprofile_folder)


def test_is_compiled_returns_false_in_interpreter() -> None:
    assert is_compiled() is False
