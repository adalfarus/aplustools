"""TBA"""
from cachetools import LRUCache as _LRUCache
from threading import RLock as _RLock
import sqlite3 as _sqlite3
import struct as _struct
import json as _json
import os as _os

from ..io.fileio import os_open as _os_open
from ..package import enforce_hard_deps as _enforce_hard_deps
from ..data import beautify_json

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

__deps__: list[str] = []
__hard_deps__: list[str] = ["cachetools>=5.5.0"]
_enforce_hard_deps(__hard_deps__, __name__)


class StorageMedium:
    """
    A base class to define the interface for different storage mediums.
    Subclasses should implement methods to store and retrieve data efficiently.
    Implements multiuser compatibility by using a versioning counter with LRU caching.

    Attributes:
        _read_cache (LRUCache): An instance of an LRU cache to store recently accessed data.
        _lock (_Lock): A lock to handle concurrency for versioning in a multiuser setup.

    Methods:
        _increment_version(file: str) -> int:
            Increments the version counter stored in the specified file, cycling from 255 back to 0.

        _get_version(file: str) -> int:
            Retrieves the current version counter from the specified file.
    """

    def __init__(self, filepath: str, max_cache_size: int = 128) -> None:
        """
        Initializes the StorageMedium with an LRU cache and a lock for thread safety.

        Args:
            max_cache_size (int, optional): The maximum size of the LRU cache. Defaults to 100.
        """
        self._read_cache: _LRUCache = _LRUCache(maxsize=max_cache_size)
        self._filepath: str = filepath
        self._current_version: int | None = None
        self._lock: _RLock = _RLock()

        self._current_version = self.create_storage(self._filepath)

    @classmethod
    def from_webresource(cls, new_file_path: str, webresource: str, max_cache_size: int = 128) -> _ty.Self:
        """
        Create an instance of the class by downloading a web resource.

        Args:
            new_file_path (str): The path where the downloaded web resource will be saved.
            webresource (str): The URL of the web resource to download.
            max_cache_size (int, optional): The maximum cache size for the instance. Defaults to 128.

        Returns:
            MyClass: An instance of the class initialized with the downloaded resource.

        Raises:
            requests.exceptions.RequestException: If the download fails.
            IOError: If the file cannot be written to the specified path.
        """
        raise NotImplementedError()  # Download webresource and make new self
        return cls(new_file_path, max_cache_size)

    def create_storage(self, at: str) -> int:
        """
        Creates a storage at the specified file location. If the file already exists it returns the storages version.
        :param at: The storage filepath.
        :return: The version of the storage.
        """
        with self._lock:
            with _os_open(at, flags_overwrite=_os_open.RDWR | _os_open.CREAT) as f:
                first_byte = f.read(1)

                if first_byte == b"":  # File is empty, initialize with version 0
                    version = 0
                    f.write(version.to_bytes(1, "big"))  # Write version byte
                else:
                    version = first_byte[0]  # Read existing version
        return version

    def _store_data(self, f: _os_open, items: dict[str, str]) -> None:
        raise NotImplementedError

    def store(self, items: dict[str, str]) -> None:
        """
        Store the data under a specified key.

        :param items: A dictionary with items to be stored.
        """
        with self._lock:
            with _os_open(self._filepath, "r+b") as f:
                version = f.read(1)[0]

                if version != self._current_version:
                    self._read_cache.clear()
                    self._current_version = version
                self._current_version = (self._current_version + 1) & 255
                self._store_data(f, items)
                f.seek(0, f.SEEK_SET)
                f.write(self._current_version.to_bytes(1, "big"))

    def _retrieve_data(self, f: _os_open, keys: list[str]) -> list[str | None]:
        raise NotImplementedError

    def retrieve(self, keys: list[str]) -> list[str | None]:
        """
        Retrieve the data stored under the specified key from the file.

        :param keys: The keys associated with the data.
        :return: The retrieved data or None if the key doesn't exist.
        """
        with self._lock:
            with _os_open(self._filepath, "rb") as f:
                version = f.read(1)[0]

                if version != self._current_version:
                    self._read_cache.clear()
                    self._current_version = version
                    return self._retrieve_data(f, keys)
                return self._retrieve_data(f, keys)

    def filepath(self) -> str:
        """Returns the filepath of the StorageMedium object."""
        return self._filepath

    def acquire(self, timeout: float = -1) -> None:
        """
        Sets the lock for multiple operations.

        :param timeout: Timeout before returning if lock cannot get acquired.
        """
        self._lock.acquire(timeout=timeout)

    def release(self) -> None:
        """
        Releases the lock acquired with acquire(timeout=...)
        :return:
        """
        self._lock.release()

    def __enter__(self) -> _ty.Self:
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.release()
        return False


class JSONStorage(StorageMedium):
    """
    A storage medium using JSON files to store and retrieve key-data pairs.
    """
    def __init__(self, filepath: str, max_cache_size: int = 128, beautify: bool = False) -> None:
        self.beautify: bool = beautify
        super().__init__(filepath, max_cache_size)

    def _store_data(self, f: _os_open, items: dict[str, str]) -> None:
        """
        Store the data under a specified key in a JSON file.

        :param f: The open file object (os_open) to store data.
        :param items: A dictionary with items to be stored.
        """
        # We can assume that f is positioned after the version byte
        try:
            # Load the existing JSON data (or start with an empty dictionary if the file is empty)
            storage = _json.loads(f.read().decode())
        except (ValueError, _json.JSONDecodeError) as e:
            storage = {}

        # Update the JSON structure with the new key-value pair
        storage |= items

        # Move back to the start of the file (after the version byte)
        f.seek(1, f.SEEK_SET)

        # Write the updated JSON data (without overwriting the version byte)
        f.truncate()
        if self.beautify:
            f.write(beautify_json(storage).encode())
        else:
            f.write(_json.dumps(storage).encode())

        for k, v in items.items():
            self._read_cache[k] = v

    def _retrieve_data(self, f: _os_open, keys: list[str]) -> list[str | None]:
        """
        Retrieve the data stored under the specified key from a JSON file.

        :param f: The open file object (os_open) to read data from.
        :param keys: The keys associated with the data.
        :return: The retrieved data or None if the key doesn't exist.
        """
        dates = []
        json_storage = None
        for key in keys:
            cached = self._read_cache.get(key)

            if cached is None:
                if json_storage is None:
                    # We can assume that f is positioned after the version byte
                    try:
                        # Load the entire JSON data from the file
                        data = f.read().decode()
                        json_storage = _json.loads(data)
                    except (ValueError, _json.JSONDecodeError) as e:
                        dates.append(None)  # If the file is empty or corrupted

                    # Cache every key-value pair in the file
                    if len(self._read_cache) == 0:
                        for k, v in json_storage.items():
                            self._read_cache[k] = v
                dates.append(json_storage.get(key))
            else:
                dates.append(cached)
        return dates


class SQLite3Storage(StorageMedium):
    """
    A storage medium using an SQLite3 database to store and retrieve key-data pairs.
    """

    def __init__(self, filepath: str, tables: tuple[str, ...] = ("storage",), drop_unused_tables: bool = False) -> None:
        """
        Initializes the SQLite3Storage with a database file.

        :param filepath: The path to the SQLite3 database file.
        """
        self._tables = tables
        self._table = tables[0]  # You have to set _table before the init call
        super().__init__(filepath)
        with _sqlite3.connect(filepath) as conn:
            cursor = conn.cursor()
            if drop_unused_tables:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                existing_tables = {row[0] for row in cursor.fetchall()}

                unused_tables = existing_tables - set(self._tables)
                for table in unused_tables:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")

            conn.commit()

    def switch_table(self, table: str) -> None:
        """
        Switch to a different table within the same database.

        :param table: The name of the new table to use.
        """
        self._table = table
        if table not in self._tables:
            self.make_sure_exists(table, self._filepath)

    @staticmethod
    def make_sure_exists(table: str, at: str) -> None:
        """
        Ensures a specified table exists in an SQLite database.

        Connects to the SQLite database at the given path and checks if the specified
        table exists. If not, it creates the table with `key` and `value` columns
        for storing key-value pairs.

        Args:
            table (str): The name of the table to check or create.
            at (str): The path to the SQLite database file.

        Returns:
            None
        """
        with _sqlite3.connect(at) as conn:
            cursor = conn.cursor()
            # Create a table for storing key-value pairs if it doesn't already exist
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {table} (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            conn.commit()

    def create_storage(self, at: str) -> int:
        """
        Initializes the database with a table for key-value storage.
        """
        for table in self._tables:
            self.make_sure_exists(table, at)
        return -1

    def _store_data(self, f: _sqlite3.Connection, items: dict[str, str]) -> None:
        """
        Store the data under a specified key in the SQLite database.

        :param f: The SQLite connection object to store data.
        :param items: A dictionary with items to be stored.
        """
        cursor = f.cursor()

        # Insert or update the key-value pair
        cursor.executemany(f'''
            INSERT INTO {self._table} (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
        ''', items.items())

        # Commit the transaction
        f.commit()

    def _retrieve_data(self, f: _sqlite3.Connection, keys: list[str]) -> list[str | None]:
        """
        Retrieve the data stored under the specified key from the SQLite database.

        :param f: The SQLite connection object to read data from.
        :param keys: The keys associated with the data.
        :return: The retrieved data or None if the key doesn't exist.
        """
        cursor = f.cursor()

        # Use the IN clause to retrieve multiple keys in one query with parameterized queries
        query = f'SELECT key, value FROM {self._table} WHERE key IN ({",".join(["?"] * len(keys))})'
        cursor.execute(query, keys)
        db_results = cursor.fetchall()

        # Create a dictionary of results from the database query
        db_result_map = {key: value for key, value in db_results}

        results = []
        for key in keys:
            results.append(db_result_map.get(key))
        return results

    def store(self, items: dict[str, str]) -> None:
        """
        Store the data under a specified key.

        :param items: A dictionary with items to be stored.
        """
        with self._lock:  # Ensure thread-safety
            with _sqlite3.connect(self._filepath) as conn:
                self._store_data(conn, items)

    def retrieve(self, keys: list[str]) -> list[str | None]:
        """
        Retrieve the data stored under the specified key.

        :param keys: The keys associated with the data.
        :return: The retrieved data or None if the key doesn't exist.
        """
        with self._lock:  # Ensure thread-safety
            # If not in cache, query the database
            with _sqlite3.connect(self._filepath) as conn:
                return self._retrieve_data(conn, keys)


class BinaryStorage(StorageMedium):
    """
    A storage medium using binary format to store and retrieve key-data pairs.
    """

    def _pack_data(self, key: str, data: str) -> bytes:
        """
        Pack key and data into a binary format with length prefixes for variable-sized data.
        """
        key_bytes = key.encode('utf-8')
        data_bytes = data.encode('utf-8')

        # Pack the lengths of the key and value along with the data
        packed_data = _struct.pack(f'!I{len(key_bytes)}sI{len(data_bytes)}s',
                                   len(key_bytes), key_bytes, len(data_bytes), data_bytes)

        return packed_data

    def _unpack_data(self, data: bytes, pos: int) -> tuple[str, str, int]:
        """
        Unpack binary data into key and value with length prefixes starting from a specific position.

        :param data: The binary data to unpack.
        :param pos: The current position in the data buffer.
        :return: A tuple containing the key, value, and the new position.
        """
        # Unpack key length
        key_len = _struct.unpack('!I', data[pos:pos + 4])[0]
        pos += 4
        # Unpack key
        key = _struct.unpack(f'!{key_len}s', data[pos:pos + key_len])[0].decode('utf-8')
        pos += key_len
        # Unpack value length
        value_len = _struct.unpack('!I', data[pos:pos + 4])[0]
        pos += 4
        # Unpack value
        value = _struct.unpack(f'!{value_len}s', data[pos:pos + value_len])[0].decode('utf-8')
        pos += value_len

        return key, value, pos

    def _store_data(self, f: _os_open, items: dict[str, str]) -> None:
        """
        Store the data under a specified key in a binary file,
        reading all key-value pairs into memory, modifying them,
        and writing everything back in one go.
        """
        # Read the entire file into memory
        buffer = f.read()

        # Unpack the entire binary data into a dictionary
        pos = 0
        all_data = {}  # Dictionary to store all key-value pairs
        while pos + 4 <= len(buffer):  # Ensure we have enough bytes to unpack the key length
            # Use _unpack_data to extract key, value, and the updated position
            key, value, pos = self._unpack_data(buffer, pos)
            all_data[key] = value

        # Update or add new items to the dictionary
        for key, value in items.items():
            all_data[key] = value
            self._read_cache[key] = value  # Update the cache

        # Now write everything back to the file
        f.seek(1)  # Move to the start of the file after the version byte
        f.truncate()  # Truncate the file to clear old data

        # Pack the entire dictionary into a binary format using _pack_data
        for key, value in all_data.items():
            packed_entry = self._pack_data(key, value)
            f.write(packed_entry)

    def _retrieve_data(self, f: _os_open, keys: list[str]) -> list[str | None]:
        """
        Retrieve the data stored under the specified key from a binary file.

        :param f: The open file object (os_open) to read data from.
        :param keys: The keys associated with the data.
        :return: The retrieved data or None if the key doesn't exist.
        """
        results = []
        bin_storage = None

        for key in keys:
            cached = self._read_cache.get(key)

            if cached is None:
                if bin_storage is None:
                    bin_storage = {}
                    buffer = f.read()  # Assume f is positioned after the version byte
                    pos = 0
                    fill_cache = len(self._read_cache) == 0

                    while pos + 4 <= len(buffer):  # Ensure there are enough bytes to unpack
                        # Use _unpack_data to extract key, value, and the updated position
                        existing_key, existing_value, pos = self._unpack_data(buffer, pos)

                        # Optionally fill the cache
                        if fill_cache:
                            self._read_cache[existing_key] = existing_value

                        bin_storage[existing_key] = existing_value

                results.append(bin_storage.get(key))
            else:
                results.append(cached)

        return results


class SimpleStorageMedium:
    """
    A base class to define the interface for different storage mediums.
    Subclasses should implement methods to store and retrieve data efficiently.
    SimpleStorageMedium doesn't define any standard for multi user access.

    Methods:
        _store_data(f, items: dict[str, str]) -> None:
            Store the data into the storage medium.
        _retrieve_data(f, keys: list[str]) -> list[str | None]:
            Retrieve data from the storage medium.
    """

    def __init__(self, filepath: str) -> None:
        """
        Initializes the StorageMedium with the specified file path.

        Args:
            filepath (str): The path to the storage file.
        """
        self._filepath = filepath
        self.create_storage(self._filepath)

    def create_storage(self, at: str) -> None:
        """
        Creates storage at the specified file location if it doesn't exist.
        """
        raise NotImplementedError

    def _store_data(self, f, items: dict[str, str]) -> None:
        raise NotImplementedError

    def store(self, items: dict[str, str]) -> None:
        """
        Store the data under a specified key.

        Args:
            items (dict[str, str]): A dictionary with items to be stored.
        """
        with open(self._filepath, "r+b") as f:
            self._store_data(f, items)

    def _retrieve_data(self, f, keys: list[str]) -> list[str | None]:
        raise NotImplementedError

    def retrieve(self, keys: list[str]) -> list[str | None]:
        """
        Retrieve the data stored under the specified keys.

        Args:
            keys (list[str]): The keys associated with the data.
        Returns:
            list[str | None]: The retrieved data or None if the key doesn't exist.
        """
        with open(self._filepath, "rb") as f:
            return self._retrieve_data(f, keys)

    def filepath(self) -> str:
        """Returns the filepath of the StorageMedium object."""
        return self._filepath


class SimpleJSONStorage(SimpleStorageMedium):
    """
    A simple storage medium using JSON files to store and retrieve key-data pairs.
    """
    def __init__(self, filepath: str, beautify: bool = False) -> None:
        self.beautify: bool = beautify
        super().__init__(filepath)

    def create_storage(self, at: str) -> None:
        """Create an empty JSON file if it doesn't exist."""
        if not _os.path.exists(at):
            with open(at, 'w') as f:
                _json.dump({}, f)

    def _store_data(self, f, items: dict[str, str]) -> None:
        """Store data in JSON format."""
        f.seek(0)
        try:
            storage = _json.load(f)
        except _json.JSONDecodeError:
            storage = {}

        storage.update(items)
        f.seek(0)
        f.truncate()
        if self.beautify:
            f.write(beautify_json(storage).encode())
        else:
            f.write(_json.dumps(storage).encode())

    def _retrieve_data(self, f, keys: list[str]) -> list[str | None]:
        """Retrieve data from JSON format."""
        f.seek(0)
        try:
            storage = _json.load(f)
        except _json.JSONDecodeError:
            storage = {}

        return [storage.get(key) for key in keys]


class SimpleSQLite3Storage(SimpleStorageMedium):
    """
    A storage medium using an SQLite3 database to store and retrieve key-data pairs.
    """

    def __init__(self, filepath: str, tables: tuple[str, ...] = ("storage",), drop_unused_tables: bool = False) -> None:
        """
        Initializes the SQLite3Storage with a database file.

        :param filepath: The path to the SQLite3 database file.
        """
        self._tables = tables
        self._table = tables[0]  # You have to set _table before the init call
        super().__init__(filepath)
        with _sqlite3.connect(filepath) as conn:
            cursor = conn.cursor()
            if drop_unused_tables:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                existing_tables = {row[0] for row in cursor.fetchall()}

                unused_tables = existing_tables - set(self._tables)
                for table in unused_tables:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")

            conn.commit()

    def switch_table(self, table: str) -> None:
        """
        Switch to a different table within the same database.

        :param table: The name of the new table to use.
        """
        self._table = table
        if table not in self._tables:
            self.make_sure_exists(table, self._filepath)

    @staticmethod
    def make_sure_exists(table: str, at: str) -> None:
        """
        Ensures a specified table exists in an SQLite database.

        Connects to the SQLite database at the given path and checks if the specified
        table exists. If not, it creates the table with `key` and `value` columns
        for storing key-value pairs.

        Args:
            table (str): The name of the table to check or create.
            at (str): The path to the SQLite database file.

        Returns:
            None
        """
        with _sqlite3.connect(at) as conn:
            cursor = conn.cursor()
            # Create a table for storing key-value pairs if it doesn't already exist
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {table} (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            conn.commit()

    def create_storage(self, at: str) -> None:
        """Initialize the SQLite database with a table for key-value storage."""
        for table in self._tables:
            self.make_sure_exists(table, at)

    def _store_data(self, f: _sqlite3.Connection, items: dict[str, str]) -> None:
        """Store data in the SQLite database."""
        cursor = f.cursor()
        cursor.executemany(f'''
            INSERT INTO {self._table} (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
        ''', items.items())
        f.commit()

    def _retrieve_data(self, f: _sqlite3.Connection, keys: list[str]) -> list[str | None]:
        """Retrieve data from the SQLite database."""
        cursor = f.cursor()
        cursor.execute(f'''
            SELECT key, value FROM {self._table} WHERE key IN ({",".join(["?"] * len(keys))})
        ''', keys)
        db_results = cursor.fetchall()

        db_result_map = {key: value for key, value in db_results}
        return [db_result_map.get(key) for key in keys]

    def store(self, items: dict[str, str]) -> None:
        """
        Store the data under a specified key.

        :param items: A dictionary with items to be stored.
        """
        with _sqlite3.connect(self._filepath) as conn:
            self._store_data(conn, items)

    def retrieve(self, keys: list[str]) -> list[str | None]:
        """
        Retrieve the data stored under the specified key.

        :param keys: The keys associated with the data.
        :return: The retrieved data or None if the key doesn't exist.
        """
        with _sqlite3.connect(self._filepath) as conn:
            return self._retrieve_data(conn, keys)


class SimpleBinaryStorage(SimpleStorageMedium):
    """
    A storage medium using binary format to store and retrieve key-data pairs.
    """

    def create_storage(self, at: str) -> None:
        """Create an empty binary file if it doesn't exist."""
        if not _os.path.exists(at):
            with open(at, 'wb') as f:
                f.write(b"")

    def _pack_data(self, key: str, data: str) -> bytes:
        """Pack key and data into a binary format."""
        key_bytes = key.encode('utf-8')
        data_bytes = data.encode('utf-8')
        return _struct.pack(f'!I{len(key_bytes)}sI{len(data_bytes)}s', len(key_bytes), key_bytes, len(data_bytes), data_bytes)

    def _unpack_data(self, data: bytes, pos: int) -> tuple[str, str, int]:
        """Unpack binary data into key and value."""
        key_len = _struct.unpack('!I', data[pos:pos + 4])[0]
        pos += 4
        key = _struct.unpack(f'!{key_len}s', data[pos:pos + key_len])[0].decode('utf-8')
        pos += key_len
        value_len = _struct.unpack('!I', data[pos:pos + 4])[0]
        pos += 4
        value = _struct.unpack(f'!{value_len}s', data[pos:pos + value_len])[0].decode('utf-8')
        pos += value_len
        return key, value, pos

    def _store_data(self, f, items: dict[str, str]) -> None:
        """Store data in a binary format."""
        buffer = f.read()
        pos = 0
        all_data = {}

        while pos < len(buffer):
            key, value, pos = self._unpack_data(buffer, pos)
            all_data[key] = value

        all_data.update(items)
        f.seek(0)
        f.truncate()

        for key, value in all_data.items():
            f.write(self._pack_data(key, value))

    def _retrieve_data(self, f, keys: list[str]) -> list[str | None]:
        """Retrieve data from a binary file."""
        buffer = f.read()
        pos = 0
        all_data = {}

        while pos < len(buffer):
            key, value, pos = self._unpack_data(buffer, pos)
            all_data[key] = value

        return [all_data.get(key) for key in keys]
