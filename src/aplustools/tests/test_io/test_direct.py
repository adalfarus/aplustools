"""TBA"""
import logging
import os
import tempfile
from io import StringIO
import threading

from ...io import _direct  # Needed
from ...io._direct import *
import pytest

# Standard typing imports for aps
import typing_extensions as _te
import collections.abc as _a
import typing as _ty
if _ty.TYPE_CHECKING:
    import _typeshed as _tsh
import types as _ts


def test_actlogger_console_logging() -> None:
    logger = ActLogger("TestLogger")
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    logger._logger.handlers.clear()  # Remove default console/file handlers
    logger._logger.addHandler(handler)

    logger.info("test info")
    logger.debug("test debug")
    logger.error("test error")
    handler.flush()
    output = stream.getvalue()

    assert "test info" in output
    assert "test debug" in output
    assert "test error" in output


def test_actlogger_file_logging() -> None:
    ActLogger._instances.clear()  # ← reset singleton instance

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        path = tmp.name

    try:
        logger = ActLogger("FileLogger", log_to_file=True, filename=path)
        logger.info("file test")
        logger.error("file error")

        # Flush and close all handlers manually
        for handler in logger.handlers:
            handler.flush()
            handler.close()
        logger._logger.handlers.clear()

        with open(path, "r", encoding="utf8") as f:
            content = f.read()
            assert "file test" in content
            assert "file error" in content
    finally:
        os.remove(path)


@pytest.fixture
def redirector() -> ThreadOutputRedirector:
    return ThreadOutputRedirector()


def test_single_thread_redirection(redirector: ThreadOutputRedirector) -> None:
    buffer = StringIO()
    redirector.enable_proxy()
    redirector.redirect(buffer)
    print("Hello from main thread")
    redirector.stop_redirect()
    redirector.disable_proxy()
    assert "Hello from main thread" in buffer.getvalue()


def test_output_not_redirected_without_call(redirector: ThreadOutputRedirector) -> None:
    buffer = StringIO()
    redirector.enable_proxy()
    print("This should go to default stdout")
    redirector.disable_proxy()
    assert buffer.getvalue() == ""


def test_multi_thread_isolation(redirector: ThreadOutputRedirector) -> None:
    results = {}

    def worker(name):
        buf = StringIO()
        redirector.redirect(buf)
        print(f"Hello from {name}")
        redirector.stop_redirect()
        results[name] = buf.getvalue()

    redirector.enable_proxy()

    threads = []
    for name in ["thread1", "thread2"]:
        t = threading.Thread(target=worker, args=(name,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    redirector.disable_proxy()

    assert "Hello from thread1" in results["thread1"]
    assert "Hello from thread2" in results["thread2"]
    assert results["thread1"] != results["thread2"]


def test_stop_redirect_without_redirect(redirector: ThreadOutputRedirector) -> None:
    assert redirector.stop_redirect() is None


def test_enable_proxy_without_local(monkeypatch: pytest.MonkeyPatch, redirector: ThreadOutputRedirector) -> None:
    monkeypatch.setattr("aplustools.io._direct._local", None)
    with pytest.raises(ValueError, match="Optional dependency werkzeug not installed."):
        redirector.enable_proxy()
