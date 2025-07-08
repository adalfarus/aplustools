"""TBA"""
import tempfile
import os

from ...data.storage import *
import pytest

# Standard typing imports for aps
import typing_extensions as _te
import collections.abc as _a
import typing as _ty
if _ty.TYPE_CHECKING:
    import _typeshed as _tsh
import types as _ts


@pytest.mark.parametrize("storage_cls", [
    JSONStorage, BinaryStorage, SQLite3Storage,
    SimpleJSONStorage, SimpleBinaryStorage, SimpleSQLite3Storage
])
def test_storages(storage_cls: _ty.Type[StorageMedium | SimpleStorageMedium], *args: _ty.Any, **kwargs: _ty.Any) -> None:
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        filepath = tmp.name

    try:
        # Create the storage instance
        store = storage_cls(filepath, *args, **kwargs)

        # Test storing a single key-value pair
        store.store({'key1': 'value1'})
        result = store.retrieve(['key1'])
        assert result == ['value1'], f"Expected ['value1'], got {result}"

        # Test storing multiple keys
        store.store({'key2': 'value2', 'key3': 'value3'})
        result = store.retrieve(['key2', 'key3'])
        assert result == ['value2', 'value3'], f"Expected ['value2', 'value3'], got {result}"

        # Test retrieving non-existent key
        result = store.retrieve(['missing'])
        assert result == [None], f"Expected [None], got {result}"

        # Overwrite key and check
        store.store({'key1': 'new_value'})
        result = store.retrieve(['key1'])
        assert result == ['new_value'], f"Expected ['new_value'], got {result}"

    finally:
        try:
            os.remove(filepath)
        except PermissionError:
            import gc, time
            gc.collect()
            time.sleep(0.1)
            os.remove(filepath)
