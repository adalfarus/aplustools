"""
This module is used a lot internally to protect against memory swapping attacks, by putting any sensitive data in a
locked memory chunk.

Made by me :)
"""
import numpy as np
import platform
import random
import ctypes
import mmap
import os


def secure_delete(data: bytearray | list | np.ndarray) -> None:
    """
    Securely delete the contents of a bytearray or bytes object by overwriting
    it with zeros.
    """
    if isinstance(data, bytearray):
        length = len(data)
        # Get the address of the bytearray
        address = (ctypes.c_char * length).from_buffer(data)
        # Overwrite with zeros
        ctypes.memset(address, 0, length)
    elif isinstance(data, list):
        for i in range(len(data)):
            data[i] = 0
    elif isinstance(data, np.ndarray) and np.issubdtype(data.dtype, np.integer):
        data.fill(0)
    else:
        raise TypeError(f"Unsupported data type for secure deletion '{type(data).__name__}'")


def secure_delete_file(file_path: str, passes: int = 7) -> None:
    """
    Securely delete a file by overwriting its content with random data and zeros.

    :param file_path: Path to the file to be securely deleted.
    :param passes: Number of overwrite passes to perform.
    """
    if not os.path.isfile(file_path):
        raise ValueError(f"File not found: {file_path}")

    length = os.path.getsize(file_path)
    with open(file_path, 'r+b') as f:
        for _ in range(passes):
            f.seek(0)
            f.write(os.urandom(length))
        f.seek(0)
        f.write(b'\x00' * length)

    os.remove(file_path)


class SecureMemoryChunk:
    """Secures a chunk of memory and lets you read and write it. This is self-secure, meaning it won't spill anything,
    but it also won't clean up any insecure variables you have passed."""

    def __init__(self, byte_size: int):
        """
        Initializes the SecureMemoryChunk.

        :param byte_size: The size of the memory chunk in bytes.
        """
        self._size = byte_size
        self._mmap_obj = mmap.mmap(-1, self._size, access=mmap.ACCESS_WRITE)
        self._lock_memory()

    def _lock_memory(self) -> None:
        """Locks the memory to prevent it from being swapped to disk."""
        system = platform.system()
        addr = ctypes.c_void_p(ctypes.addressof(ctypes.c_char.from_buffer(self._mmap_obj)))
        length = ctypes.c_size_t(self._size)
        if system == "Linux" or system == "Darwin":  # Unix-like
            libc = ctypes.CDLL("libc.so.6" if system == "Linux" else "libc.dylib")
            if libc.mlock(addr, length) != 0:
                raise OSError(f"Failed to lock memory at {addr} with mlock")
        elif system == "Windows":
            kernel32 = ctypes.windll.kernel32
            if not kernel32.VirtualLock(addr, length):
                raise OSError(f"Failed to lock memory at {addr} with VirtualLock")

    def _unlock_memory(self) -> None:
        """Unlocks the memory."""
        system = platform.system()
        addr = ctypes.c_void_p(ctypes.addressof(ctypes.c_char.from_buffer(self._mmap_obj)))
        length = ctypes.c_size_t(self._size)
        if system == "Linux" or system == "Darwin":  # Unix-like
            libc = ctypes.CDLL("libc.so.6" if system == "Linux" else "libc.dylib")
            if libc.munlock(addr, length) != 0:
                raise OSError(f"Failed to unlock memory at {addr} with mlock")
        elif system == "Windows":
            kernel32 = ctypes.windll.kernel32
            if not kernel32.VirtualUnlock(addr, length):
                raise OSError(f"Failed to unlock memory at {addr} with VirtualUnlock")

    def write(self, data: bytes | bytearray, offset: int = 0) -> None:
        """
        Write data to the memory chunk.

        :param data: The data to write.
        :param offset: The offset at which to start writing.
        """
        if len(data) > self._size:
            raise ValueError("Data size exceeds allocated secure memory size")
        self._mmap_obj.seek(offset)
        self._mmap_obj.write(bytes(data))

    def write_from_disposable(self, data: bytes | bytearray, offset: int = 0) -> None:
        """
        Write data to the memory chunk and delete is right after.

        :param data: The data to write.
        :param offset: The offset at which to start writing.
        """
        if len(data) > self._size:
            raise ValueError("Data size exceeds allocated secure memory size")
        self._mmap_obj.seek(offset)
        self._mmap_obj.write(bytes(data))
        if isinstance(data, bytearray):
            secure_delete(data)
        del data

    def read(self, length=None, offset=0, return_byte_array: bool = False) -> bytes | bytearray:
        """
        Read data from the memory chunk.

        :param length: The number of bytes to read.
        :param offset: The offset from which to start reading.
        :param return_byte_array:
        :return: The read data.
        """
        self._mmap_obj.seek(offset)
        if length:
            if length + offset <= self._size:
                return self._mmap_obj.read(length)
            raise ValueError(f"The reserved memory is only {self._size} byte(s) long, the offset {offset} plus length "
                             f"{length} are bigger than that")
        return self._mmap_obj.read(self._size) if not return_byte_array else bytearray(self._mmap_obj.read(self._size))

    def resize(self, to: int, no_data_warn: bool = False) -> None:
        """
        Resize the memory-mapped file.

        :param to: The new size to resize the memory-mapped file to.
        :param no_data_warn: If False, will check for non-null data in the truncated section and raise a warning if found.
        """
        if not no_data_warn:
            if to < self._size:
                if not all(b == 0 for b in self.read(self._size - to, to)):
                    raise UserWarning("There is non-null data in the section being truncated, "
                                      "please reconsider resizing.")
        else:
            self.wipe(start=0, end=to)
        self._mmap_obj.resize(to)
        self._size = to

    def resize_with_data(self, from_offset: int, final_size: int) -> None:
        """
        Resize the memory-mapped file while preserving data starting from a specific offset.

        :param from_offset: The offset from which data should be preserved.
        :param final_size: The final size of the memory-mapped file.
        """
        if from_offset < 0 or from_offset >= self._size:
            raise ValueError("Invalid from_offset value.")
        if final_size <= 0:
            raise ValueError("Invalid final_size value.")

        self._mmap_obj.seek(from_offset)
        data_length = min(final_size, self._size - from_offset)
        inst = self.__class__(data_length)
        inst.write_from_disposable(bytearray(self._mmap_obj.read(data_length)))
        self.wipe(start=data_length, end=self._size)  # Clear any remaining memory
        self._mmap_obj.resize(final_size)
        self._mmap_obj.seek(0)
        self._mmap_obj.write(inst.read(data_length))
        inst.close()
        self._size = final_size

    def wipe(self, start: int = 0, end: int | None = None) -> None:
        """
        Wipes the memory chunk by overwriting it with zeros.

        :param start: The start offset from which to begin wiping.
        :param end: The end offset up to which to wipe. If None, wipes to the end of the memory chunk.
        """
        if end is None:
            end = self._size
        if start < 0 or end > self._size or start >= end:
            raise ValueError("Invalid start or end values.")
        self._mmap_obj.seek(start)
        self._mmap_obj.write(b'\x00' * (end - start))

    def close(self) -> None:
        """
        Closes the memory chunk, wiping it and unlocking the memory.
        """
        self.wipe()
        self._unlock_memory()
        self._mmap_obj.close()


class StaticSecureAttrs:
    """Statically stores attributes given at initialization"""
    def __init__(self, **kwargs):
        total_size = sum(len(str(value).encode('utf-8')) for value in kwargs.values())
        self._secure_memory = SecureMemoryChunk(total_size)
        self._offsets = {}
        current_offset = 0
        for key, value in kwargs.items():
            data = bytearray(str(value).encode('utf-8'))
            self._secure_memory.write(data, current_offset)
            self._offsets[key] = (current_offset, len(data))
            current_offset += len(data)
            secure_delete(data)

    def __getattr__(self, item):
        if item in self._offsets:
            offset, length = self._offsets[item]
            data = self._secure_memory.read(length, offset)
            return data.decode('utf-8')
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{item}'")

    def __setattr__(self, key, value):
        raise ValueError("Can't set attributes in a static type")

    def close(self) -> None:
        """
        Closes the memory chunk, wiping it and unlocking the memory.
        """
        self._secure_memory.close()


class DynamicSecureAttrs:
    """Statically stores attributes given at initialization"""
    def __init__(self, **kwargs):
        total_size = sum(len(str(value).encode('utf-8')) for value in kwargs.values())
        self._secure_memory = SecureMemoryChunk(total_size)
        self._offsets = {}
        current_offset = 0
        for key, value in kwargs.items():
            data = bytearray(str(value).encode('utf-8'))
            data_len = len(data)
            self._secure_memory.write_from_disposable(data, current_offset)
            self._offsets[key] = (current_offset, data_len)
            current_offset += data_len

    def _get_new_offset(self, to_what):
        if self._offsets:
            last_item: tuple[str, tuple[int, int]] = sorted(self._offsets.items(), key=lambda x: x[1][0])[-1]
            last_offset, last_length = last_item[1]
            final_offset = last_offset + last_length
            self._secure_memory.resize(final_offset + len(to_what))
            return final_offset
        else:
            return 0

    def __getattr__(self, item):
        if item in self._offsets:
            offset, length = self._offsets[item]
            return self._secure_memory.read(length, offset).decode('utf-8')
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{item}'")

    def __setattr__(self, key, value):
        if key in ['_secure_memory', '_offsets']:
            super().__setattr__(key, value)
            return

        value = bytearray(str(value).encode('utf-8'))
        if key in self._offsets:
            original_location = self._offsets[key]
            self._secure_memory.wipe(original_location[0], sum(original_location))

            if len(value) <= original_location[1]:
                offset = original_location[0]
            elif key == sorted(self._offsets.items(), key=lambda x: x[1][0])[-1]:
                offset = original_location[0]
                self._secure_memory.resize(offset + len(value))
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


if __name__ == "__main__":
    # Bytearray example
    byte_array_data = bytearray(b"Sensitive Data")
    print("Before:", byte_array_data)
    secure_delete(byte_array_data)
    print("After: ", byte_array_data)

    # List example
    list_data = [1, 2, 3, 4, 5]
    print("Before:", list_data)
    secure_delete(list_data)
    print("After: ", list_data)

    # Numpy array example
    numpy_data = np.array([1, 2, 3, 4, 5], dtype=np.int32)
    print("Before:", numpy_data)
    secure_delete(numpy_data)
    print("After: ", numpy_data)

    obj = SecureMemoryChunk(128)
    obj.write(b"\x00\x01", 126)
    obj.resize_with_data(126, 2)
    data = obj.read(1, 0)
    obj.wipe()
    print(data)
    print(obj.read(1, 0))

    attrs = DynamicSecureAttrs(key="MySuperSecretKey", cd=1, never_gonna_give_you_up=18123712737812781227838.182381823)

    for _ in range(1, 100):
        print("i" * _)
        print(attrs.key)
        attrs.key = "MySuperSecretKey2" * _
        print(attrs.key)
        print(attrs.cd)
        attrs.never_gonna_give_you_uP = 14 * _
        print(attrs.never_gonna_give_you_up)
    attrs.key = "1"
    print(attrs.key, attrs.cd, attrs.never_gonna_give_you_uP, attrs.never_gonna_give_you_up)
    print(attrs._secure_memory.read().replace(b"\x00", b""))
