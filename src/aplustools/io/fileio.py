"""TBA"""
import io  # Make _ import
import time as _time
import mmap as _mmap
import uuid as _uuid
import os as _os
import shutil as _shutil

from .env import get_system as _get_system
from ..data import align_to_next as _align_to_next
from ..package import enforce_hard_deps as _enforce_hard_deps

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

__deps__: list[str] = []
__hard_deps__: list[str] = []
_enforce_hard_deps(__hard_deps__, __name__)


def is_fd_open(fd: int) -> bool:
    """
    Check if a file descriptor is open.

    This function uses `os.fstat()` to determine if the given file descriptor is still open.
    If the file descriptor is valid and open, it returns `True`. If the file descriptor
    is closed or invalid, it returns `False`.

    Parameters:
    ----------
    fd : int
        The file descriptor to check.

    Returns:
    -------
    bool
        `True` if the file descriptor is open, `False` if it is closed.
    """
    try:
        _os.fstat(fd)
        return True  # If fstat succeeds, the fd is open
    except OSError:
        return False  # If OSError occurs, the fd is closed


class BasicFileLock:
    """
    A basic file locking mechanism for cross-process synchronization using lock files.

    This class provides a simple way to lock a file by creating a `.lock` file alongside the target file.
    It can be used as a context manager or manually engaged/disengaged.

    Args:
        filepath (str): The path of the file to lock.
        check_interval (float, optional): Time (in seconds) to wait before re-checking the lock if it's already held. Defaults to 0.1 seconds.
        open_mode (str, optional): The mode to open the locked file. If None, the file is not opened. Defaults to None.

    Attributes:
        filepath (str): The path of the file being locked.
        lock_filepath (str): The path of the `.lock` file created for locking.
        check_interval (float): Time interval to wait before checking the lock file again.
        open_mode (str | None): The mode in which to open the file (if specified).
        file (_ty.IO | _ty.BinaryIO | None): The opened file object (if opened).
    """

    def __init__(self, filepath: str, check_interval: float = 0.1, open_mode: str | None = None) -> None:
        """
        Initializes the file lock for the given file path.

        Args:
            filepath (str): The path of the file to lock.
            check_interval (float): Time (in seconds) to wait before checking the lock again if it's already held.
            open_mode (str | None): The mode in which to open the file (if applicable).
        """
        self.filepath: str = filepath
        self.lock_filepath: str = f"{filepath}.lock"
        self.check_interval: float = check_interval
        self.open_mode: str | None = open_mode
        self.file: _ty.IO | _ty.BinaryIO | None = None

    def engage(self) -> _ty.IO | _ty.BinaryIO | None:
        """
        Manually acquire the lock by creating the lock file.
        If the lock file already exists, it waits until the lock is released.
        """
        return self.__enter__()

    def disengage(self) -> None:
        """
        Manually release the lock by deleting the lock file if it exists.
        """
        self.__exit__(None, None, None)

    def is_locked(self) -> bool:
        """
        Check if the file is currently locked by verifying the existence of the lock file.

        Returns:
            bool: True if the file is locked, False otherwise.
        """
        return _os.path.exists(self.lock_filepath)

    def __enter__(self) -> _ty.IO | _ty.BinaryIO | None:
        """
        Acquire the lock by creating a lock file.
        If the lock file already exists, wait until it is released.

        Returns:
            _ty.IO | _ty.BinaryIO | None: An opened file object in the specified mode (if open_mode is provided), or None.
        """
        while _os.path.exists(self.lock_filepath):
            _time.sleep(self.check_interval)

        open(self.lock_filepath, "w").close()
        if self.open_mode is not None:
            self.file = open(self.filepath, mode=self.open_mode)
            return self.file

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Release the lock by deleting the lock file.
        """
        if self.file is not None:
            self.file.close()
            self.file = None
        if _os.path.exists(self.lock_filepath):
            _os.remove(self.lock_filepath)


class BasicFDWrapper:
    """
    A wrapper for a file descriptor providing an interface similar to Python's open().

    This class wraps an existing file descriptor and provides higher-level
    file operations like read, write, seek, and close.
    """
    SEEK_SET = _os.SEEK_SET
    SEEK_CUR = _os.SEEK_CUR
    SEEK_END = _os.SEEK_END

    def __init__(self, fd: int, close_fd: bool = True) -> None:
        """
        Initializes the wrapper with the given file descriptor.

        Args:
            fd (int): The file descriptor to wrap.
        """
        self.fd: int = fd
        self.closed: bool = False
        self.close_fd: bool = close_fd

    def read(self, size: int = -1) -> bytes:
        """
        Reads up to 'size' bytes from the file descriptor.

        Args:
            size (int): The number of bytes to read. If -1, reads until EOF.

        Returns:
            bytes: The bytes read from the file descriptor.
        """
        if size == -1:
            # If size is -1, read all content until EOF
            chunks = []
            while True:
                chunk = _os.read(self.fd, 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            return b''.join(chunks)
        else:
            return _os.read(self.fd, size)

    def write(self, data: bytes) -> int:
        """
        Writes data to the file descriptor.

        Args:
            data (bytes): The data to write.

        Returns:
            int: The number of bytes written.
        """
        return _os.write(self.fd, data)

    def seek(self, offset: int, whence: int = _os.SEEK_SET) -> int:
        """
        Moves the file descriptor's read/write position.

        Args:
            offset (int): The position to move to.
            whence (int): Optional argument. The reference point (SEEK_SET, SEEK_CUR, SEEK_END).

        Returns:
            int: The new absolute position.
        """
        return _os.lseek(self.fd, offset, whence)

    def tell(self) -> int:
        """
        Returns the current file position.

        Returns:
            int: The current file offset.
        """
        return _os.lseek(self.fd, 0, _os.SEEK_CUR)

    def truncate(self, size: int | None = None) -> None:
        """
        Truncate the file to the specified size.
        If size is None, truncate the file at the current file position.

        Args:
            size (int | None): The size to truncate the file to.
        """
        if size is None:
            # If size is not specified, truncate at the current position of the file pointer
            size = _os.lseek(self.fd, 0, _os.SEEK_CUR)  # Get the current file position

        # Truncate the file to the specified size
        _os.ftruncate(self.fd, size)

    def close(self) -> None:
        """
        Closes the file descriptor.
        """
        if not self.closed and self.close_fd and is_fd_open(self.fd):
            _os.close(self.fd)
            self.closed = True

    def __enter__(self) -> _ty.Self:
        """
        Allows the FDWrapper to be used as a context manager.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Ensures the file descriptor is closed when exiting the context.
        """
        self.close()

    def fileno(self) -> int:
        """
        Returns the file descriptor.

        Returns:
            int: The file descriptor.
        """
        return self.fd

    def isatty(self) -> bool:
        """
        Checks if the file descriptor refers to a terminal.

        Returns:
            bool: True if the file descriptor refers to a terminal, False otherwise.
        """
        return _os.isatty(self.fd)


class OSFileLock:
    """
    A cross-platform file lock using OS-level locking mechanisms.

    This class locks a file for exclusive access, using platform-specific
    mechanisms like `fcntl` (Unix-like systems) or `msvcrt` (Windows).
    It can be used as a context manager or manually engaged/disengaged.

    Args:
        filepath (str): The path of the file to lock.
        open_flags (int): The flags with which to open the file after locking.

    Attributes:
        filepath (str): The path of the file to lock.
        fd (int | None): The file descriptor when the lock is acquired, or None if not locked.
        open_flags (int): The flags with which to open the file after locking (if any).
        _system: System-specific lock manager (determined based on OS).
    """

    def __init__(self, filepath: str, open_flags: int = _os.O_RDWR | _os.O_CREAT) -> None:
        """
        Initialize the file lock for the given filepath and set up system-specific locking.

        Args:
            filepath (str): The path of the file to lock.
            open_flags (int | None): The flags with which to open the file after locking.
        """
        self.filepath: str = filepath
        self.fd: int | None = None
        self.open_flags: int = open_flags
        self._system = _get_system()  # System-specific lock mechanism

    @staticmethod
    def convert_mode_to_flags(mode: _ty.Literal["r", "rb", "r+", "r+b", "w", "wb", "w+", "w+b", "a", "ab", "a+", "a+b"]) -> int:
        """
        Converts a Python file mode string to os.open flags.

        Args:
            mode (str): A file mode string like 'r', 'w+', 'a', etc.

        Returns:
            int: The corresponding os.open flags.
        """
        flags = 0

        if "r" in mode:
            if "+" in mode:
                flags |= _os.O_RDWR
            else:
                flags |= _os.O_RDONLY
        elif "w" in mode:
            if "+" in mode:
                flags |= _os.O_RDWR | _os.O_CREAT | _os.O_TRUNC
            else:
                flags |= _os.O_WRONLY | _os.O_CREAT | _os.O_TRUNC
        elif "a" in mode:
            if "+" in mode:
                flags |= _os.O_RDWR | _os.O_CREAT | _os.O_APPEND
            else:
                flags |= _os.O_WRONLY | _os.O_CREAT | _os.O_APPEND

        # Handle binary mode
        if "b" in mode:
            if _os.name == "nt":  # Windows needs O_BINARY for binary mode
                flags |= _os.O_BINARY

        return flags

    def engage(self) -> int:
        """
        Manually acquire the lock and optionally open the file.

        Returns:
            _ty.IO | _ty.BinaryIO | None: The opened file object (if `open_mode` is provided), or None.
        """
        return self.__enter__()

    def disengage(self) -> None:
        """
        Manually release the lock and close the file if it was opened.
        """
        self.__exit__(None, None, None)

    def is_locked(self) -> bool:
        """
        Check if the file is currently locked using the system-specific lock manager.

        Returns:
            bool: True if the file is locked, False otherwise.
        """
        return self._system.is_file_locked(self.filepath)

    def __enter__(self) -> int:
        """
        Acquire the lock by using the system's file locking mechanism.
        Waits if the file is already locked.

        Returns:
            _ty.IO | _ty.BinaryIO | None: An opened file object if `open_mode` is provided, or None.
        """
        self.fd = self._system.lock_file(self.filepath, blocking=True, open_flags=self.open_flags)
        return self.fd

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Release the lock and close the file (if it was opened).

        Args:
            exc_type (Exception | None): Exception type (if any).
            exc_val (Exception | None): Exception value (if any).
            exc_tb (traceback | None): Traceback information (if any).
        """
        if self.fd and is_fd_open(self.fd):
            self._system.unlock_file(self.fd)
            self.fd = None


class os_open(BasicFDWrapper):
    """
    A simplified wrapper that combines the functionality of OSFileLock and BasicFDWrapper, allowing you to
    work with file locking in a manner similar to Python's built-in open() function.

    The os_open class ensures that the file is exclusively locked using OS-specific file locks, preventing
    other processes from accessing the file while it is in use. It provides an easy interface for file operations
    with automatic locking, useful in scenarios where concurrent access to files needs to be controlled.

    This class extends BasicFDWrapper, which handles low-level file descriptor management, and uses OSFileLock
    to manage the exclusive locking mechanism.

    Args:
        filepath (str): The path to the file that should be locked and opened.
        mode (str): The file access mode (e.g., "r" for reading, "w" for writing). Defaults to "r".
        buffer_size (int): The size of the write buffer.

    Example:
        with os_open("/path/to/file", "r") as file:
            content = file.read()

    """
    RDWR = _os.O_RDWR
    CREAT = _os.O_CREAT
    TRUNC = _os.O_TRUNC
    APPEND = _os.O_APPEND
    WRONLY = _os.O_WRONLY
    BINARY = _os.O_BINARY

    def __init__(self, filepath: str,
                 mode: _ty.Literal["r", "rb", "r+", "r+b", "w", "wb", "w+", "w+b", "a", "ab", "a+", "a+b"] = "r",
                 *_, buffer_size: int = 500, flags_overwrite: int | None = None) -> None:
        super().__init__(OSFileLock(filepath, flags_overwrite or OSFileLock.convert_mode_to_flags(mode)).engage())
    #     self._buffer: bytearray = bytearray(buffer_size)  # Allocate buffer with max size
    #     self._buffer_size: int = buffer_size
    #     self._p: int = 0  # Buffer pointer
    #     self.mode: str = mode
    #     self._rmapped: bool = False  # If the the area from self._p to self._buffer_size is mapped with read data.
    #     self._flags_overwritten: bool = flags_overwrite is not None
    #
    # def write(self, data: bytes) -> int:
    #     data_len = len(data)
    #     if self._rmapped:
    #         self.flush()
    #     if data_len >= self._buffer_size:
    #         if self._p > 0:
    #             self.flush()
    #         super().write(data)
    #         return data_len  # bytes written
    #
    #     bytes_written = 0  # Add to buffer, if _p == len(self._buffer) flush buffer
    #     while bytes_written < data_len:
    #         amount_to_write = min(self._buffer_size - self._p, data_len)
    #         self._buffer[self._p:self._p + amount_to_write] = data[bytes_written:bytes_written + amount_to_write]
    #         self._p += amount_to_write
    #         bytes_written += amount_to_write
    #
    #         if self._p == len(self._buffer):
    #             self.flush()
    #     return bytes_written
    #
    # def read(self, size: int = -1) -> bytes:
    #     # Read from the buffer and file
    #     if size == -1 or size > self._buffer_size:  # Read until EOF or more than buffer
    #         size =
    #         size -= self._buffer_size - self._p
    #         print(size, self._p)
    #         read_data = self._buffer[self._p:self._buffer_size]  # Read all data from the file descriptor
    #         if size > 0:
    #             read_data += super().read(size)
    #         self._p = 0
    #         self._rmapped = False
    #         return read_data
    #     if not self._rmapped:
    #         self.flush()  # Flush and read in the first chunk
    #         self._rmapped = True
    #         self._buffer[:self._buffer_size] = super().read(self._buffer_size)
    #
    #     read_data = bytearray()
    #     while size > 0:
    #         to_read = min(size, self._buffer_size - self._p)
    #         print("[fileio] to read", to_read, size, self._p)
    #         read_data += self._buffer[self._p:self._p + to_read]
    #         print("[fileio] read", read_data)
    #         self._p += to_read
    #         size -= to_read
    #
    #         if self._p == self._buffer_size:
    #             self._p = 0
    #             self._buffer[:self._buffer_size] = super().read(self._buffer_size)
    #
    #     print("[fileio] final read", read_data)
    #     return bytes(read_data)
    #
    # def seek(self, offset: int, whence: int = _os.SEEK_SET) -> int:
    #     self.flush()
    #     return super().seek(offset, whence)
    #
    # def tell(self) -> int:
    #     if self._p > 0:
    #         return super().tell() - self._buffer_size + self._p
    #     return super().tell()
    #
    # def truncate(self, size: int | None = None) -> None:
    #     self.flush()
    #     super().truncate(size)
    #
    # def flush(self) -> None:
    #     """
    #     Public method to flush the buffer by writing the content to the file.
    #     This is typically used in write mode to ensure all buffered data is written to disk.
    #     """
    #     if "w" in self.mode or "a" in self.mode or "+" in self.mode or self._flags_overwritten:
    #         print("[fileio] Flushing", bytes(self._buffer[:self._p]))
    #         if not self._rmapped:
    #             print("[fileio] Writing Buffer")
    #             super().write(self._buffer[:self._p])
    #         self._p = 0  # Reset pointer after flushing the buffer
    #         self._rmapped = False
    #
    # def close(self) -> None:
    #     self.flush()
    #     super().close()


class _FileLockMixin:
    SEEK_SET = _os.SEEK_SET
    SEEK_CUR = _os.SEEK_CUR
    SEEK_END = _os.SEEK_END

    def __init__(self, filepath: str, fd: int) -> None:
        self._filepath: str = filepath
        self._fd: int | None = fd
        self._locked: bool = False
        self._system = _get_system()
        self._page_size: int = self._system.page_size()

    def _acquire_read_lock(self, byte_range: range | None = None) -> None:
        """Acquire a shared read lock, retrying if necessary."""
        if not self._locked:
            self._system.lock_file(self._fd, byte_range, True, shared_lock=True)
            self._locked = True
        else:
            raise ValueError("Lock already gotten")

    def _acquire_write_lock(self, byte_range: range | None = None) -> None:
        """Acquire an exclusive write lock, retrying if necessary."""
        if not self._locked:
            self._system.lock_file(self._fd, byte_range, True, shared_lock=False)
            self._locked = True
        else:
            raise ValueError("Lock already gotten")

    def _release_lock(self, byte_range: range | None = None, *_, release_fd: bool = False) -> None:
        """Release the lock, keeping the file descriptor open."""
        if self._locked:
            self._system.unlock_file(self._fd, keep_fd_open=not release_fd, byte_range=byte_range)
            self._locked = False
        else:
            raise ValueError("No lock gotten")


class os_hyper_read(_FileLockMixin):
    """
    A file descriptor-based reader class that reads data in chunks, uses a buffer,
    and manages file locking during read operations.

    This class handles reading from a file by acquiring a read lock when loading chunks of data
    into a buffer. The buffer is filled with chunks of data, and the file is read incrementally
    as needed. The read lock is released as soon as the chunk has been read to minimize the time
    the file is locked. The buffer will grow up to `max_buffer_size`, after which older data may
    be discarded if more data is read.
    """

    def __init__(self, filepath: str, chunk_size: int = (1024 * 1024) * 4,
                 max_buffer_size: int = (1024 * 1024) * 16) -> None:
        raise NotImplementedError(f"This class is not yet ready to be used.")
        super().__init__(filepath, _os.open(filepath, _os.O_RDONLY))  # Open file in read-only mode
        self._chunk_size: int = chunk_size
        self._max_buffer_size: int = max_buffer_size
        self._buffer: bytearray = bytearray()  # Internal buffer to store chunks
        self._offset: int = 0  # Current read position in the file
        self._buffer_start: int = 0  # Where the buffer starts in the file
        self._buffer_end: int = 0  # End of the buffer
        self._file_size: int = self._get_file_size()

    def _get_file_size(self) -> int:
        """
        Get the total size of the file.

        This function retrieves the file size using `os.fstat()`.

        Returns:
        -------
        int
            The total size of the file in bytes.
        """
        return _os.fstat(self._fd).st_size

    def _read_chunk(self, offset: int) -> bytes:
        """
        Read a chunk from the file starting at the given offset.

        This function seeks to the specified offset and reads a chunk of data from the file.

        Parameters:
        ----------
        offset : int
            The byte offset in the file where the reading starts.

        Returns:
        -------
        bytes
            The chunk of data read from the file.
        """
        _os.lseek(self._fd, offset, _os.SEEK_SET)  # Seek to the specified offset
        return _os.read(self._fd, self._chunk_size)  # Read a chunk from the file

    def _fill_buffer(self) -> None:
        """
        Read the next chunk into the buffer and update the buffer's state.

        This method reads a chunk from the file into the buffer while ensuring the buffer
        doesn't exceed the `max_buffer_size`. The method acquires a read lock before reading
        the chunk and releases the lock immediately after the chunk is read.
        """
        # Ensure we're not at the end of the file
        if self._offset >= self._file_size:
            return

        chunk = b''  # Initialize chunk to avoid UnboundLocalError

        # Acquire a read lock while reading the chunk
        self._acquire_read_lock(range(self._offset, self._offset + self._chunk_size))

        try:
            # Read the chunk
            chunk = self._read_chunk(self._offset)

            # Update the buffer and offset
            if len(self._buffer) + len(chunk) > self._max_buffer_size:
                # If buffer exceeds max size, trim it (discard old data if necessary)
                excess_size = len(self._buffer) + len(chunk) - self._max_buffer_size
                self._buffer = self._buffer[excess_size:]  # Trim the oldest data

            self._buffer.extend(chunk)
            self._buffer_start = self._offset  # Update buffer start
            self._buffer_end = self._buffer_start + len(chunk)  # Update buffer end

            # Move the offset to reflect the newly read chunk
            self._offset += len(chunk)
        finally:
            # Quickly release the read lock once the chunk is read
            self._release_lock(range(self._offset - len(chunk), self._offset))

    def read(self, length: int) -> bytes:
        """
        Read a specific length of data from the buffer.

        This method reads the requested number of bytes from the buffer. If the buffer
        does not have enough data, it will load more chunks from the file until the
        requested length is fulfilled.

        Parameters:
        ----------
        length : int
            The number of bytes to read.

        Returns:
        -------
        bytes
            The bytes read from the buffer.
        """
        read_buffer = bytearray()

        while length > 0:
            # Check if we need to fill the buffer
            if self._buffer_start + len(self._buffer) - self._offset < length:
                self._fill_buffer()

            # How much we can read from the current buffer
            available = self._buffer_end - self._offset
            to_read = min(available, length)

            # Read from the buffer
            read_buffer += self._buffer[self._offset - self._buffer_start:self._offset - self._buffer_start + to_read]
            self._offset += to_read
            length -= to_read

            if not available:  # If there's no more data to read, stop
                break

        return bytes(read_buffer)

    def seek(self, offset: int) -> None:
        """
        Set the read position in the file to the given offset.

        Parameters:
        ----------
        offset : int
            The new read position, must be within the file size.

        Raises:
        -------
        ValueError
            If the offset is outside the file bounds.
        """
        if 0 <= offset <= self._file_size:
            self._offset = offset
        else:
            raise ValueError(f"Offset {offset} out of bounds.")

    def tell(self) -> int:
        """
        Get the current read position in the file.

        Returns:
        -------
        int
            The current position of the file pointer.
        """
        return self._offset

    def get_chunk_size(self) -> int:
        """
        Get the current chunk size.

        Returns:
        -------
        int
            The size of each memory-mapped chunk.
        """
        return self._chunk_size

    def set_chunk_size(self, new_chunk_size: int) -> None:
        """
        Set a new chunk size for memory mapping.

        Parameters:
        ----------
        new_chunk_size : int
            The new chunk size to be used for memory mapping.

        Raises:
        -------
        ValueError
            If the new chunk size is less than or equal to zero.
        """
        if new_chunk_size <= 0:
            raise ValueError("The chunk size has to be greater than 0.")
        self._chunk_size = _align_to_next(new_chunk_size, self._page_size) or self._page_size
        self.set_max_buffer_size(self._max_buffer_size)

    def get_max_buffer_size(self) -> int:
        """
        Get the current maximum buffer size.

        Returns:
        -------
        int
            The maximum size of the buffer.
        """
        return self._max_buffer_size

    def set_max_buffer_size(self, new_max_buffer_size: int) -> None:
        """
        Set a new maximum buffer size for memory mapping.

        Parameters:
        ----------
        new_max_buffer_size : int
            The new maximum buffer size to be used.

        Raises:
        -------
        ValueError
            If the new buffer size is less than or equal to zero.
        """
        if new_max_buffer_size <= 0:
            raise ValueError("The max buffer size has to be greater than 0.")
        self._max_buffer_size = _align_to_next(new_max_buffer_size, self._chunk_size) or self._chunk_size

    def close(self) -> None:
        """
        Clean up the file descriptor and release any held locks.

        This method ensures that the file descriptor is properly closed and any locks
        are released when the object is deleted.
        """
        if is_fd_open(self._fd):
            _os.close(self._fd)

    def __enter__(self) -> _ty.Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()


class os_hyper_write(_FileLockMixin):
    """
    A file descriptor-based writer class that uses memory-mapped I/O (mmap) for efficient
    partial reads and writes with batching, supporting buffered writes in chunks.

    This class manages file writes by memory-mapping regions of the file, writing data
    in chunks, and efficiently managing file locking. The class handles both reading and
    writing via mmap, ensuring only the necessary portions of the file are locked and
    mapped into memory at any given time.
    """

    def __init__(self, filepath: str, chunk_size: int = (1024 * 1024) * 4,
                 max_buffer_size: int = (1024 * 1024) * 16) -> None:
        raise NotImplementedError(f"This class is not yet ready to be used.")
        super().__init__(filepath, _os.open(filepath, _os.O_RDWR | _os.O_CREAT))
        self._chunk_size: int = _align_to_next(chunk_size, self._page_size) or self._page_size
        self._max_buffer_size: int = _align_to_next(max_buffer_size, self._chunk_size) or self._chunk_size

        self._offset = self._buffer_start = self._buffer_end = 0
        self.dirty: bool = False
        self._mmap_obj: _mmap.mmap | None = None
        self._map_region(self._offset)

    def _get_file_size(self) -> int:
        """
        Get the total size of the file.

        Returns:
        -------
        int
            The total size of the file in bytes.
        """
        return _os.fstat(self._fd).st_size

    def _flush_mmap(self) -> None:
        """
        Flush the current memory-mapped region if it's dirty.

        If the memory-mapped region has been modified, this method writes the changes to disk.
        It manages file locking by switching between read and write locks while performing the flush.
        """
        if self.dirty:
            # Release the shared read lock and acquire an exclusive write lock for the current chunk
            byte_range = range(self._buffer_start, self._buffer_start + self._chunk_size)
            self._release_lock(byte_range)  # Release read lock
            self._acquire_write_lock(byte_range)

            # Flush the dirty memory-mapped region to disk
            self._mmap_obj.flush()
            self.dirty = False

            # Release the write lock and re-acquire the read lock for the current chunk
            self._release_lock(byte_range)  # Release write lock
            self._acquire_read_lock(byte_range)

    def _map_region(self, offset: int) -> None:
        """
        Map a specific region of the file into memory.

        This method maps a portion of the file into memory, managing file locks and ensuring that
        the mapped region does not exceed the chunk size or buffer limits.

        Parameters:
        ----------
        offset : int
            The byte offset in the file to start mapping.
        """
        if offset + self._chunk_size > self._get_file_size():
            new_file_size = offset + self._chunk_size
            was_locked = self._locked
            if was_locked:
                self._release_lock(range(self._buffer_start, self._buffer_end))
            self._acquire_write_lock(range(offset, new_file_size))
            _os.truncate(self._fd, new_file_size)
            self._release_lock(range(offset, new_file_size))
            if was_locked:
                self._acquire_read_lock(range(self._buffer_start, self._buffer_end))

        if self._mmap_obj is not None:
            if self._buffer_start <= offset < self._buffer_end:
                return
            # Making the buffer bigger instead of a new buffer made it slower
            # elif self._buffer_end < (offset - self._buffer_start) < self._max_buffer_size:
            #     self._release_lock(range(self._buffer_start, self._buffer_end))
            #     self._buffer_end = offset + self._chunk_size
            #     self._offset = offset - self._buffer_start
            #     self._acquire_read_lock(range(self._buffer_start, self._buffer_end))
            #     self._mmap_obj.resize(self._buffer_end)
            #     return

            self._flush_mmap()
            self._mmap_obj.close()
            self._mmap_obj = None
            self._release_lock(range(self._buffer_start, self._buffer_end))

        self._buffer_start = offset
        self._buffer_end = offset + self._chunk_size

        # Acquire the lock for the current region (byte range)
        byte_range = range(self._buffer_start, self._buffer_end)
        self._acquire_read_lock(byte_range)  # Lock only the current chunk

        # Create the mmap object for the specified region
        self._mmap_obj = _mmap.mmap(self._fd, self._chunk_size,
                                    # prot=mmap.PROT_WRITE | mmap.PROT_READ,
                                    access=_mmap.ACCESS_DEFAULT,
                                    offset=self._buffer_start)
        self.dirty = False
        self._offset = 0

    def read(self, length: int) -> bytes:
        """
        Read data from the file using the memory-mapped region.

        Parameters:
        ----------
        length : int
            The number of bytes to read from the file.

        Returns:
        -------
        bytes
            The data read from the file.
        """
        read_buffer = bytearray()
        while True:  # mmap new regions until the length is fulfilled
            if length + self._offset <= self._chunk_size:
                read_buffer += self._mmap_obj.read(length)
                self._offset += length
                return bytes(read_buffer)

            len_to_read = (self._buffer_end - self._buffer_start) - self._offset
            length -= len_to_read
            self._offset += len_to_read
            read_buffer += self._mmap_obj.read(len_to_read)
            self._map_region(self._buffer_start + self._offset)

    def write(self, data: bytes) -> None:
        """
        Write data to the file using the memory-mapped region.

        This method writes data to the memory-mapped region, remapping the region as needed
        if the buffer is full or the write extends beyond the current region.

        Parameters:
        ----------
        data : bytes
            The data to write to the file.
        """
        bytes_written = 0  # Track how much of `data` has been written
        data_length = len(data)

        while bytes_written < data_length:
            remaining_space_in_buffer = self._buffer_end - self._buffer_start - self._offset
            len_to_write = min(remaining_space_in_buffer, data_length - bytes_written)

            self._mmap_obj[self._offset:self._offset + len_to_write] = data[bytes_written:bytes_written + len_to_write]

            self._offset += len_to_write
            bytes_written += len_to_write

            if self._offset == (self._buffer_end - self._buffer_start):
                new_offset = self._buffer_start + self._offset
                self._map_region(new_offset)

    @staticmethod
    def _seeker(offset: int, current_offset: int, file_size: int, whence: int = 0) -> int:
        """
        Calculate the new file position based on the seek parameters.

        Parameters:
        ----------
        offset : int
            The offset to move the file pointer.
        current_offset : int
            The current position in the file.
        file_size : int
            The size of the file.
        whence : int, optional
            Defines the reference point for seeking, by default 0 (start of file).

        Returns:
        -------
        int
            The new file position.
        """
        if whence == 0:
            return offset
        elif whence == 1:
            return current_offset + offset
        elif whence == 2:
            return file_size - offset

    def seek(self, offset: int, whence: int = 0) -> None:
        """
        Set the file pointer to a specific position.

        Parameters:
        ----------
        offset : int
            The new position to set the file pointer.
        whence : int, optional
            The reference point for the offset, by default 0 (start of file).
        """
        fz = self._get_file_size()
        new_pos = self._seeker(offset, self._offset, fz, whence)
        if 0 <= new_pos <= fz:
            whole, rest = divmod(new_pos, self._page_size)
            self._map_region(whole * self._page_size)
            self._mmap_obj.seek(rest)
            self._offset += rest

    def tell(self) -> int:
        """
        Get the current position in the memory-mapped file.

        Returns:
        -------
        int
            The current file pointer position.
        """
        return self._buffer_start + self._offset  # or self._mmap_obj.tell()

    def get_chunk_size(self) -> int:
        """
        Get the current chunk size.

        Returns:
        -------
        int
            The size of each memory-mapped chunk.
        """
        return self._chunk_size

    def set_chunk_size(self, new_chunk_size: int) -> None:
        """
        Set a new chunk size for memory mapping.

        Parameters:
        ----------
        new_chunk_size : int
            The new chunk size to be used for memory mapping.

        Raises:
        -------
        ValueError
            If the new chunk size is less than or equal to zero.
        """
        if new_chunk_size <= 0:
            raise ValueError("The chunk size has to be greater than 0.")
        self._chunk_size = _align_to_next(new_chunk_size, self._page_size) or self._page_size
        self.set_max_buffer_size(self._max_buffer_size)

    def get_max_buffer_size(self) -> int:
        """
        Get the current maximum buffer size.

        Returns:
        -------
        int
            The maximum size of the buffer.
        """
        return self._max_buffer_size

    def set_max_buffer_size(self, new_max_buffer_size: int) -> None:
        """
        Set a new maximum buffer size for memory mapping.

        Parameters:
        ----------
        new_max_buffer_size : int
            The new maximum buffer size to be used.

        Raises:
        -------
        ValueError
            If the new buffer size is less than or equal to zero.
        """
        if new_max_buffer_size <= 0:
            raise ValueError("The max buffer size has to be greater than 0.")
        self._max_buffer_size = _align_to_next(new_max_buffer_size, self._chunk_size) or self._chunk_size

    def close(self) -> None:
        """
        Ensure the file is properly closed and the memory-mapped region is flushed upon deletion.

        This method flushes any dirty memory-mapped regions, closes the mmap object, and releases
        any locks held on the file before closing the file descriptor.
        """
        if self._mmap_obj is not None:
            self._flush_mmap()
            self._mmap_obj.close()
            self._mmap_obj = None
        if self._locked:  # If we aren't locked, we aren't opened.
            self._release_lock(range(self._buffer_start, self._buffer_end), release_fd=True)
        elif is_fd_open(self._fd):
            _os.close(self._fd)

    def __enter__(self) -> _ty.Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()


class FileIOType(_ty.Protocol):
    """
    A protocol defining the interface for file-like objects.
    This includes methods commonly found in Python's file objects.
    """
    def read(self, n: int = -1) -> _ty.Any:
        """
        Read up to n bytes from the file. If n is -1, read all available data.
        """
        ...

    def write(self, t: _ty.Any) -> int:
        """
        Write the given data to the file. Returns the number of bytes written.
        """
        ...

    def seek(self, i: int, whence: int = 0) -> None:
        """
        Move the file pointer to a specified location.

        Parameters:
        - i: The offset to move to.
        - whence: Optional, defaults to 0 (absolute positioning).
                  1 (relative to the current position), or 2 (relative to the end of file).
        """
        ...

    def close(self) -> None:
        """
        Close the file. After closing, operations on the file object will fail.
        """
        ...

    def fileno(self) -> int:
        """
        Return the file descriptor associated with the file object.
        """
        ...

    def flush(self) -> None:
        """
        Flush the file's internal buffer, ensuring data is written to disk.
        """
        ...


class SafeFileWriter:
    """
    SafeFileWriter takes in a standard FileIO object with expected methods.
    It opens the original in write mode but doesn't do anything with it.
    It expects the open() to bring its own locking for greater compatibility.
    The potential temporary file is opened in write mode too.

    There are three modes to choose from:

    - virtual: All changes are written to a memory map.

    - copy on close: All changes are written to a copy of the file which gets written to the original at close.

    - switch on close: Same as copy on close but the files are switched instead. This method is error and
    corruption prone on Windows machines.

    We do not catch or convert any data read or written, you need to know what your open needs.

    Usage example:
    safe_f = SafeFileWriter("./hello_world.txt", os_open, )
    safe_f.seek(0, 2)
    safe_f.write(b"Hello WORLD!")  # As I know os_open only accepts binary data
    """

    def __init__(self, path: str, open_func: _a.Callable[[str, str], FileIOType] | _ty.Type,
                 mode: _ty.Literal["virtual", "copy_on_close", "switch_on_close"] = "copy_on_close") -> None:
        if not _os.path.exists(path):
            open(path, "w").close()
        self._mode: str = mode
        self._curr_open_obj: FileIOType | _mmap.mmap | None = None
        self._path: str = path
        self._temppath: str = f"{path}.{_uuid.uuid4().hex}.tempwrite"
        self._closed: bool = False

        if mode == "virtual":
            self._open_obj: FileIOType = open_func(path, "r+")
            file_size = _os.path.getsize(path)
            if file_size == 0:  # Handle empty files
                raise ValueError("Cannot use 'virtual' mode on an empty file.")
            self._curr_open_obj = _mmap.mmap(self._open_obj.fileno(), file_size)
        elif mode == "copy_on_close" or mode == "switch_on_close":
            _shutil.copy(self._path, self._temppath)  # Prevent locking
            self._open_obj: FileIOType = open_func(path, "r+")
            self._curr_open_obj = open_func(self._temppath, "r+")
        else:
            raise ValueError(f"The mode '{mode}' is invalid")

    def read(self, n: int = -1) -> _ty.Any:
        """
        Read data from the file or memory map.

        Parameters:
        - n: The number of bytes to read. Defaults to -1 (read all).

        Returns:
        - The data read.
        """
        if self._closed:
            raise ValueError("The file is already closed")
        return self._curr_open_obj.read(n)

    def write(self, t: _ty.Any) -> int:
        """
        Write data to the file or memory map.

        Parameters:
        - t: The data to write.

        Returns:
        - The number of bytes written.
        """
        if self._closed:
            raise ValueError("The file is already closed")
        if self._mode == "virtual":
            self._curr_open_obj.write(t.encode() if isinstance(t, str) else t)
            return len(t)
        return self._curr_open_obj.write(t)

    def seek(self, i: int, whence: int = 0) -> None:
        """
        Move the file pointer to a specified position.

        Parameters:
        - i (int): The offset to move to.
        - whence (int): Determines the reference point for the offset.
            - 0: Start of the file (default).
            - 1: Current position.
            - 2: End of the file.

        This method adjusts the current position in the file for subsequent read or write operations.
        """
        self._curr_open_obj.seek(i, whence)

    def flush(self) -> None:
        """
        Flush the internal buffer, ensuring that all changes made to the file
        are written to the underlying storage.

        This is especially useful in buffered operations to avoid data loss
        in case of an unexpected termination.
        """
        self._curr_open_obj.flush()

    def fileno(self) -> int:
        """
        Return the file descriptor associated with the current open file object.

        The file descriptor is an integer that uniquely identifies an open file
        and can be used with low-level system calls.

        Returns:
        - int: The file descriptor for the underlying file object.
        """
        return self._curr_open_obj.fileno()

    def close(self) -> None:
        """
        Close the SafeFileWriter, finalizing changes based on the mode.
        """
        if self._closed:
            return
        self._closed = True
        if self._mode == "virtual":
            self._curr_open_obj.flush()
            self._curr_open_obj.close()
            self._open_obj.close()
        elif self._mode == "copy_on_close":
            self._curr_open_obj.seek(0, 0)
            content = self._curr_open_obj.read()
            self._open_obj.seek(0, 0)
            self._open_obj.write(content)
            self._curr_open_obj.close()
            self._open_obj.close()
            _os.remove(self._temppath)
        elif self._mode == "switch_on_close":
            self._curr_open_obj.close()
            try:
                _os.remove(self._path)
                _os.rename(self._temppath, self._path)
            except OSError:
                # We're on windows
                self._open_obj.close()  # Someone else can lock the file right here leading to corruption
                _os.remove(self._path)
                _os.rename(self._temppath, self._path)
            else:  # We're on posix, we can now safely release the lock
                self._open_obj.close()  # This only works on posix

    def __enter__(self) -> _ty.Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()
