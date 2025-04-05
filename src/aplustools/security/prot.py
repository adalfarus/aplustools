"""TBA, protects data when in transition and ensures types. protect against memory swapping attacks; locked memory chunk"""

from platform import system as _system
from random import randint as _ri
import ctypes as _ctypes
import mmap as _mmap
import numpy as _np

from ..package import enforce_hard_deps as _enforce_hard_deps

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

__deps__: list[str] = []
__hard_deps__: list[str] = []
_enforce_hard_deps(__hard_deps__, __name__)


raise NotImplementedError("This module is not secure and will never be secure, please use something different")


def secure_delete(data: bytearray | list | _np.ndarray) -> None:
    """
    Securely delete the contents of a mutable sequence by overwriting its content with zeros.
    This function is intended for use with data types that allow modification in place,
    such as `bytearray`, `list`, and `numpy.ndarray` (integer types).

    For `bytearray`, the content is overwritten using a `memoryview` for efficient in-place modification.
    For `list`, each element is set to zero.
    For `numpy.ndarray`, it checks for integer types and then overwrites all elements with zero.

    After overwriting, the memory of `bytearray` and `list` objects is left intact but contains zeros.
    This is useful for ensuring that sensitive information (like cryptographic keys) is not lingering
    in memory after use.

    Note:
    - This function does not ensure secure deletion of the underlying memory buffer itself (e.g., if
      the data has been swapped to disk), but it minimizes the risk of sensitive data being left in memory.

    :param data: The mutable sequence to be securely deleted. Must be one of `bytearray`, `list`, or `numpy.ndarray`.
    :raises TypeError: If the provided data type is not supported.
    """
    if isinstance(data, bytearray):
        with memoryview(data) as view:
            view[:] = b'\x00' * len(data)
    elif isinstance(data, list):
        for i in range(len(data)):
            data[i] = 0
    elif isinstance(data, _np.ndarray) and _np.issubdtype(data.dtype, _np.integer):
        data.fill(0)
    else:
        raise TypeError(f"Unsupported data type for secure deletion '{type(data).__name__}'")


class SecureMemoryChunk:
    """
    Secures a chunk of memory and allows reading and writing operations.
    This class is designed to provide secure memory handling by locking memory
    to prevent it from being swapped to disk and ensuring that sensitive data is
    overwritten and deleted properly.

    Note: The memory security is limited to keeping the data in RAM and preventing
    unintentional exposure but cannot protect against all forms of memory attacks.
    """

    def __init__(self, byte_size: int) -> None:
        """
        Initializes the SecureMemoryChunk.

        :param byte_size: The size of the memory chunk in bytes.
        """
        self._size: int = byte_size
        self._mmap_obj: _mmap.mmap = _mmap.mmap(-1, self._size, access=_mmap.ACCESS_WRITE)
        self._is_locked: bool = False
        self._lock_memory()

    def _lock_memory(self) -> None:
        """
        Locks the memory to prevent it from being swapped to disk.

        Raises a ValueError if the memory is already locked.
        """
        if self._is_locked:
            raise ValueError("Memory is already locked.")
        system = _system()
        addr = _ctypes.c_void_p(_ctypes.addressof(_ctypes.c_char.from_buffer(self._mmap_obj)))
        length = _ctypes.c_size_t(self._size)
        if system == "Linux" or system == "Darwin":  # Unix-like
            libc = _ctypes.CDLL("libc.so.6" if system == "Linux" else "libc.dylib")
            if libc.mlock(addr, length) != 0:
                raise OSError(f"Failed to lock memory at {addr} with mlock")
        elif system == "Windows":
            kernel32 = _ctypes.windll.kernel32
            if not kernel32.VirtualLock(addr, length):
                raise OSError(f"Failed to lock memory at {addr} with VirtualLock")
        self._is_locked = True

    def _unlock_memory(self) -> None:
        """
        Unlocks the memory, allowing it to be swapped if necessary.
        This method first wipes the memory to ensure that no sensitive data remains
        before unlocking.

        Raises a ValueError if the memory is not locked.
        """
        if not self._is_locked:
            raise ValueError("Memory is not currently locked.")
        self.wipe()  # Wipe memory before unlocking to ensure no sensitive data remains
        system = _system()
        addr = _ctypes.c_void_p(_ctypes.addressof(_ctypes.c_char.from_buffer(self._mmap_obj)))
        length = _ctypes.c_size_t(self._size)
        if system == "Linux" or system == "Darwin":  # Unix-like
            libc = _ctypes.CDLL("libc.so.6" if system == "Linux" else "libc.dylib")
            if libc.munlock(addr, length) != 0:
                raise OSError(f"Failed to unlock memory at {addr} with mlock")
        elif system == "Windows":
            kernel32 = _ctypes.windll.kernel32
            if not kernel32.VirtualUnlock(addr, length):
                raise OSError(f"Failed to unlock memory at {addr} with VirtualUnlock")
        self._is_locked = False

    def write(self, data: bytes | bytearray, offset: int = 0) -> None:
        """
        Write data to the memory chunk at a specified offset.

        :param data: The data to write, either as bytes or a bytearray.
        :param offset: The offset in bytes at which to start writing the data.

        Raises a ValueError if the memory is not locked or if the data size
        exceeds the allocated memory size.
        """
        if not self._is_locked:
            raise ValueError("Cannot write while memory is unlocked.")
        if len(data) > self._size:
            raise ValueError("Data size exceeds allocated secure memory size")
        self._mmap_obj.seek(offset)
        self._mmap_obj.write(bytes(data))

    def write_from_disposable(self, data: bytearray, offset: int = 0) -> None:
        """
        Write data to the memory chunk and securely delete the source data.

        :param data: The data to write, as a bytearray. This data will be securely deleted after writing.
        :param offset: The offset at which to start writing.

        Raises a ValueError if the memory is not locked.
        """
        self.write(data, offset)
        secure_delete(data)
        del data

    def read(self, length=None, offset=0, return_byte_array: bool = False) -> bytes | bytearray:
        """
        Read data from the memory chunk starting from a specific offset.

        :param length: The number of bytes to read. Reads the full size if None.
        :param offset: The offset from which to start reading.
        :param return_byte_array: If True, returns the data as a bytearray instead of bytes.
        :return: The read data as bytes or bytearray.

        Raises a ValueError if the memory is not locked or if the requested length
        exceeds the memory size.
        """
        if not self._is_locked:
            raise ValueError("Cannot read while memory is unlocked.")
        self._mmap_obj.seek(offset)
        if length:
            if length + offset > self._size:
                raise ValueError(f"The reserved memory is only {self._size} byte(s) long, "
                                 f"the offset {offset} plus length {length} are too large")
            data = self._mmap_obj.read(length)
        else:
            data = self._mmap_obj.read(self._size)
        return bytearray(data) if return_byte_array else data

    def resize(self, to: int) -> None:
        """
        Resize the memory chunk to a new size.

        :param to: The new size of the memory chunk in bytes.

        Raises a ValueError if the memory is locked or if the new size is invalid.
        """
        if self._is_locked:
            raise ValueError("Cannot resize while memory is locked.")
        if to <= 0:
            raise ValueError("New size must be greater than zero.")
        else:
            self.wipe(start=0, end=to)
        self._mmap_obj.resize(to)
        self._size = to

    def resize_with_data(self, from_offset: int, final_size: int) -> None:
        """
        Resize the memory chunk while preserving data starting from a given offset.

        :param from_offset: The starting offset of the data to preserve.
        :param final_size: The final size of the memory chunk.

        Raises a ValueError if the memory is not locked, the offset is invalid, or the size is not positive.
        """
        if not self._is_locked:
            raise ValueError("Memory must be locked before resizing with data.")
        if from_offset < 0 or from_offset >= self._size:
            raise ValueError("Invalid from_offset value.")
        if final_size <= 0:
            raise ValueError("Invalid final_size value.")

        self._mmap_obj.seek(from_offset)
        data_length = min(final_size, self._size - from_offset)
        inst = self.__class__(data_length)
        inst.write_from_disposable(bytearray(self._mmap_obj.read(data_length)))

        self._unlock_memory()
        self.resize(final_size)
        self._lock_memory()
        self._mmap_obj.seek(0)
        self._mmap_obj.write(inst.read(data_length))
        inst.close()
        self._size = final_size

    def wipe(self, start: int = 0, end: int | None = None) -> None:
        """
        Wipe a section of the memory chunk by overwriting it with zeros.

        :param start: The start offset in bytes.
        :param end: The end offset in bytes. If None, wipes to the end of the memory chunk.

        Raises a ValueError if the start or end values are invalid.
        """
        if end is None:
            end = self._size
        if start < 0 or end > self._size or start >= end:
            raise ValueError("Invalid start or end values.")
        self._mmap_obj.seek(start)
        self._mmap_obj.write(b'\x00' * (end - start))

    def close(self) -> None:
        """
        Closes the memory chunk, ensuring that all data is wiped and the memory is unlocked.
        """
        self.wipe()
        if self._is_locked:
            self._unlock_memory()
        self._mmap_obj.close()


class StaticSecureAttrs:
    """
    Stores attributes in a secure, static manner using a SecureMemoryChunk.
    The attributes and their values are set during initialization and cannot
    be modified afterward, ensuring data consistency.

    This class is suitable for storing fixed-size sensitive data securely.
    """

    def __init__(self, **kwargs) -> None:
        total_size = sum(len(value) for value in kwargs.values())
        self._secure_memory = SecureMemoryChunk(total_size)
        self._offsets = {}
        current_offset = 0
        for key, value in kwargs.items():
            self._secure_memory.write_from_disposable(value, current_offset)
            self._offsets[key] = (current_offset, len(value))
            current_offset += len(value)

    def __getattr__(self, item: str) -> bytearray:
        """
        Retrieve the value of an attribute by reading from the secure memory.

        :param item: The name of the attribute.
        :return: The value of the attribute as a string.

        Raises AttributeError if the attribute does not exist.
        """
        if item in self._offsets:
            offset, length = self._offsets[item]
            return self._secure_memory.read(length, offset, return_byte_array=True)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{item}'")

    def __setattr__(self, key: str, value: bytearray) -> None:
        """
        Prevents setting attributes after initialization, ensuring immutability.

        Raises ValueError when an attempt is made to set an attribute.
        """
        if key in ['_secure_memory', '_offsets']:
            super().__setattr__(key, value)
            return
        raise ValueError("Can't set attributes in a static type")

    def close(self) -> None:
        """
        Closes the secure memory, wiping and unlocking it.
        """
        self._secure_memory.close()


class DynamicSecureAttrs:
    """
    Dynamically stores attributes in a secure manner using a SecureMemoryChunk.
    Unlike StaticSecureAttrs, this class allows adding and modifying attributes
    after initialization, with the data being securely stored and managed.

    This class is suitable for scenarios where the stored data may need to change over time.
    """
    def __init__(self, **kwargs) -> None:
        total_size = sum(len(value) for value in kwargs.values())
        self._secure_memory = SecureMemoryChunk(total_size or 1)
        self._offsets = {}
        current_offset = 0
        for key, value in kwargs.items():
            self._secure_memory.write_from_disposable(value, current_offset)
            self._offsets[key] = (current_offset, len(value))
            current_offset += len(value)

    def _get_new_offset(self, to_what: bytearray) -> int:
        if self._offsets:
            last_item: tuple[str, tuple[int, int]] = sorted(self._offsets.items(), key=lambda x: x[1][0])[-1]
            last_offset, last_length = last_item[1]
            final_offset = last_offset + last_length
            self._secure_memory.resize_with_data(0, final_offset + len(to_what))
            return final_offset
        else:
            return 0

    def __getattr__(self, item: str) -> bytearray:
        if item in self._offsets:
            offset, length = self._offsets[item]
            return self._secure_memory.read(length, offset, return_byte_array=True)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{item}'")

    def __setattr__(self, key: str, value: bytearray) -> None:
        if key in ['_secure_memory', '_offsets']:
            super().__setattr__(key, value)
            return
        if key in self._offsets:
            original_location = self._offsets[key]
            self._secure_memory.wipe(original_location[0], sum(original_location))

            if len(value) <= original_location[1]:
                offset = original_location[0]
            elif key == sorted(self._offsets.items(), key=lambda x: x[1][0])[-1]:
                offset = original_location[0]
                self._secure_memory.resize_with_data(0, offset + len(value))
            else:
                offset = self._get_new_offset(value)
        else:
            offset = self._get_new_offset(value)
        self._offsets[key] = (offset, len(value))
        self._secure_memory.write_from_disposable(value, offset)

    def close(self) -> None:
        """
        Closes the memory chunk, wiping it and unlocking the memory.
        """
        self._secure_memory.close()


class BlackBox:
    """Is a black box that 100% securely stores data."""
    link_pub_key = None  # Linked public key of secure instance

    def __init__(self) -> None:
        self._attrs = DynamicSecureAttrs()

    def link(self, inst) -> None:
        self.link_pub_key = _ri(100_000_000_000, 999_999_999_999)
        self._attrs.bb_public_key = inst.link()

    def set(self, item: str, value: bytearray) -> None:
        if self.link_pub_key is None:
            raise ValueError("The BlackBox must be linked to add values!")
        ...  # Encrypt value with public key before storing it

    def set_from_disposable(self, item: str, value: bytearray) -> None:
        if self.link_pub_key is None:
            raise ValueError("The BlackBox must be linked to add values!")
        ...  # Encrypt value with public key before storing it
        secure_delete(value)

    def get(self, item) -> bytes:
        ...  # Return the encrypted value if is present.

    def __del__(self):
        self._attrs.close()
