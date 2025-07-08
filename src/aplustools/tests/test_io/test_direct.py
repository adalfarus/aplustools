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
        raise ValueError()  # Kind of janky with monkeypatch for installed and uninstalled
