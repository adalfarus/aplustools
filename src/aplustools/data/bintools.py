"""TBA"""
from collections import OrderedDict as _OrderedDict
from threading import Lock as _Lock
import struct as _struct
import math as _math
import sys as _sys

from ..package import enforce_hard_deps as _enforce_hard_deps
from . import cutoff_iterable as _cutoff_iterable

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

from ..package import optional_import as _optional_import

_np = _optional_import("numpy")

__deps__: list[str] = ["numpy==1.26.4"]
__hard_deps__: list[str] = []
_enforce_hard_deps(__hard_deps__, __name__)


def encode_float(fp: float, precision: _ty.Literal["half", "single", "double", "quad"] = "single") -> bytes:
    """
    Encode a floating-point number into its byte representation with variable precision.

    This function converts a floating-point number into bytes using the specified precision.
    Supported precisions are:

    - 'half'   : 16-bit floating-point number (requires NumPy)
    - 'single' : 32-bit floating-point number (standard Python float)
    - 'double' : 64-bit floating-point number
    - 'quad'   : 128-bit floating-point number (if supported by the system)

    Args:
        fp: The floating-point number to encode.
        precision: The precision of the floating-point representation. Options are 'half', 'single', 'double', 'quad'.

    Returns:
        The byte representation of the floating-point number.

    Raises:
        ValueError: If an unsupported precision is specified.
        ImportError: If 'half' precision is specified but NumPy is not installed.
    """
    if precision == "half":  # 16-bit float (requires NumPy)
        if _np is None:
            raise RuntimeError(f"You need to have numpy to encode a 16-bit float")
        return _np.float16(fp).tobytes()
    elif precision == "single":  # 32-bit float
        return _struct.pack(">f", fp)
    elif precision == "double":  # 64-bit float
        return _struct.pack(">d", fp)
    elif precision == "quad":  # 128-bit float (if supported)
        if _sys.maxsize > 2**32:
            try:
                return _struct.pack(">e", fp)
            except _struct.error:
                raise ValueError("128-bit floats are not supported on this system.")
        else:
            raise ValueError("128-bit floats are not supported on this system.")
    else:
        raise ValueError("Unsupported precision. Choose from 'half', 'single', 'double', 'quad'.")


def decode_float(bytes_like: bytes, precision: _ty.Literal["half", "single", "double", "quad"] = "single") -> float:
    """
    Decode bytes into a floating-point number with variable precision.

    This function converts a byte representation back into a floating-point number using the specified precision.
    Supported precisions are:

    - 'half'   : 16-bit floating-point number (requires NumPy)
    - 'single' : 32-bit floating-point number
    - 'double' : 64-bit floating-point number
    - 'quad'   : 128-bit floating-point number (if supported by the system)

    Args:
        bytes_like: The byte data to decode into a floating-point number.
        precision: The precision of the floating-point representation. Options are 'half', 'single', 'double', 'quad'.

    Returns:
        The decoded floating-point number.

    Raises:
        ValueError: If an unsupported precision is specified.
        ImportError: If 'half' precision is specified but NumPy is not installed.
    """
    if precision == "half":  # 16-bit float (requires NumPy)
        if _np is None:
            raise RuntimeError(f"You need to have numpy to decode a 16-bit float")
        return _np.frombuffer(bytes_like, dtype=_np.float16)[0]
    elif precision == "single":  # 32-bit float
        return _struct.unpack(">f", bytes_like)[0]
    elif precision == "double":  # 64-bit float
        return _struct.unpack(">d", bytes_like)[0]
    elif precision == "quad":  # 128-bit float (if supported)
        if _sys.maxsize > 2**32:
            try:
                return _struct.unpack(">e", bytes_like)[0]
            except _struct.error:
                raise ValueError("128-bit floats are not supported on this system.")
        else:
            raise ValueError("128-bit floats are not supported on this system.")
    else:
        raise ValueError("Unsupported precision. Choose from 'half', 'single', 'double', 'quad'.")


def bytes_length(data: int | float | str) -> int:
    """
    Calculate the number of bytes required to represent the given data.

    Args:
        data: The data to calculate byte length for. Can be an int, float, or str.

    Returns:
        The total number of bytes required to represent the input data.
    """
    if isinstance(data, int):
        return ((data.bit_length() + 7) // 8) or 1
    elif isinstance(data, float):
        return len(encode_float(data))
    elif isinstance(data, str):
        return len(data.encode("utf-8"))
    raise ValueError(f"Unsupported data type '{type(data).__name__}'.")


def bit_length(data: int | float | str) -> int:
    """
    Calculate the number of bits required to represent the given data.

    Args:
        data: The data to calculate bit length for. Can be an int, float, or str.

    Returns:
        The total number of bits required to represent the input data.
    """
    if isinstance(data, int):
        return data.bit_length() or 1
    elif isinstance(data, float):
        return int.from_bytes(encode_float(data)).bit_length() or 1
    elif isinstance(data, str):
        return int.from_bytes(data.encode("utf-8")).bit_length()
    raise ValueError(f"Unsupported data type '{type(data).__name__}'.")


def encode_integer(integer: int, negatives: bool = False, byteorder: _ty.Literal["little", "big"] = "big") -> bytes:
    """
    Encode an integer into bytes with optional support for negatives and byte order.

    Args:
        integer: The integer to encode.
        negatives: If True, allows encoding of negative integers using two's complement. Defaults to False.
        byteorder: Byte order to use ('little' or 'big'). Defaults to 'big'.

    Returns:
        The byte representation of the integer.

    Raises:
        ValueError: If a negative integer is passed and `negatives` is False.

    Example:
        encode_integer(12345)  # b'09'
        encode_integer(-12345, negatives=True, byteorder='little')  # b'\xc7\xcf\xff\xff'
    """
    if integer < 0 and not negatives:
        raise ValueError(f"The integer passed is negative but you haven't enabled negatives.")
    byte_size = (integer.bit_length() + 7) // 8  # Determine the required number of bytes
    return integer.to_bytes(byte_size if integer != 0 else 1, byteorder, signed=negatives)


def decode_integer(bytes_like: bytes, negatives: bool = False, byteorder: _ty.Literal["little", "big"] = "big") -> int:
    """
    Decode a bytes object into an integer with optional support for negatives and byte order.

    Args:
        bytes_like: The bytes object to decode.
        negatives: If True, interprets the integer as signed. Defaults to False.
        byteorder: Byte order to use ('little' or 'big'). Defaults to 'big'.

    Returns:
        The decoded integer.

    Example:
        decode_integer(b'09')  # 12345
        decode_integer(b'\xc7\xcf\xff\xff', negatives=True, byteorder='little')  # -12345
    """
    return int.from_bytes(bytes_like, byteorder, signed=negatives)


def get_variable_bytes_like(bytes_like: bytes) -> bytes:
    """
    Encode a byte sequence with a length prefix.

    This function prepends the byte sequence with its length as a single byte, allowing
    for variable-length encoding. The length byte represents the size of the byte sequence
    and is followed by the actual bytes.

    Args:
    -----
    bytes_like : bytes
        The byte sequence to encode with a length prefix.

    Returns:
    --------
    bytes
        A new byte sequence with the length byte prepended, followed by the original byte sequence.

    Example:
    --------
    >>> get_variable_bytes_like(b'hello')
    b'\x05hello'  # \x05 indicates the length of 'hello'
    """
    return to_progressive_length(len(bytes_like)) + bytes_like


def read_variable_bytes_like(f: _ty.BinaryIO) -> bytes | None:
    """
    Read a length-prefixed byte sequence from a binary stream or bytes.

    This function reads the first byte, which indicates the length of the subsequent byte sequence,
    then reads that number of bytes from the input. It can work on a file-like binary stream or
    directly on a bytes object.

    Args:
    -----
    f : _ty.BinaryIO or bytes
        The file-like binary stream or bytes object to read from.

    Returns:
    --------
    bytes or None
        The read byte sequence (without the length prefix), or None if the stream is empty.

    Example:
    --------
    >>> import io
    >>> f = io.BytesIO(b'\x05hello')
    >>> read_variable_bytes_like(f)
    b'hello'
    """
    try:
        length = read_progressive_length(f)
    except EOFError:
        return None
    return f.read(length)


def expected_progressive_length_bytecount(length_of_x: int) -> int:
    """
    Estimate the number of bytes needed for progressive length encoding.

    Given an integer `length_of_x`, this function calculates the expected byte count
    required for a progressive length encoding, based on the magnitude of `length_of_x`.
    This encoding format scales the byte length logarithmically with the input size,
    optimizing space usage. Negative values are treated as their positive counterparts,
    and a length of 0 returns 1, the minimum amount needed by the encoding.

    :param length_of_x: The length value to estimate for encoding.
    :return: The estimated byte count for encoding `length_of_x`.
    """
    total = 0
    x = cx = abs(length_of_x)
    while x > 1:
        x = _math.log(cx, 256) + 0.125  # 1/8 as a float
        # x = (math.log(cx, 2) / 8) + 0.125  # This is noticeably a little slower, by around 00.01->00.02 seconds.
        cx = _math.ceil(x)
        total += cx
    return total or 1  # Handle cases where length_of_x == 0


def to_progressive_length(length_of_x: int) -> bytes:
    """
    Encode an integer length into a compact, progressively larger byte format.

    This encoding supports small numbers with minimal bytes and scales up for larger
    numbers using additional bytes as needed. The format is efficient, aiming to
    use the least space for each length magnitude.

    :param length_of_x: The integer to encode in progressive length format.
    :return: A byte-encoded representation of `length`.
    :raises ValueError: If `length` is negative or an internal bug occurs.
    """
    buffer_size = int(expected_progressive_length_bytecount(length_of_x) * 1.1)  # Margin of error as a buffer
    result_buffer = bytearray(buffer_size)
    result_pointer = buffer_size  # - 1 is not needed as slices exclude the last element of the specified range
    current_length = length_of_x
    last = True  # We move through the buffer back to front

    if length_of_x < 0:
        raise ValueError("Only positives lengths can exist")
    elif length_of_x == 1:
        return b"\x02"
    elif length_of_x == 0:
        return b"\x00"

    while current_length > 1:
        stage = encode_integer((current_length << 1) | (0 if last else 1))
        last = False
        # Move pointer back and insert stage at the pointer
        stage_len = len(stage)
        result_pointer -= stage_len
        if result_pointer < 0:
            raise ValueError("Encountered bug while encoding, please report!")
        result_buffer[result_pointer:result_pointer + stage_len] = stage
        # Update length for the next loop iteration
        current_length = len(stage)  # bytes_length(current_length)

    return bytes(result_buffer[result_pointer:])


def read_progressive_length(f: _ty.BinaryIO) -> int:
    """
    Decode a progressive length-encoded integer from a binary stream.

    This function reads an integer encoded in a progressive-length format from
    a binary input stream. Each segment of the encoding specifies the byte length
    of the next segment, allowing for compact and scalable length encoding.
    The function reads in stages, where the least significant bit in each segment
    indicates if more data follows (1 for continue, 0 for stop). The remaining bits
    determine the byte length for the next read.

    :param f: A binary file-like object implementing `read` for reading the encoded integer.
    :return: The decoded integer length from the progressive encoding.
    :raises EOFError: If the stream ends before the full integer is decoded.
    """
    current_length = 1
    goes_on = True

    while goes_on:
        bytes_read = f.read(current_length)
        if len(bytes_read) < current_length:
            raise EOFError("Unexpected end of file or stream during progressive length decoding.")
        part = decode_integer(bytes_read)
        goes_on = (part & 1) == 1
        current_length = part >> 1

    return current_length


class BitBuffer:
    """
    A class that handles efficient reading and manipulation of a bit-level buffer
    from a stream of bytes. It maintains internal state to track byte and bit positions
    and allows extracting arbitrary numbers of bits or sequences of bit values.
    """
    def __init__(self) -> None:
        self._array: bytes | bytearray = b""
        self._disregard_pointer: int = 0
        self._byte_index: int = 0  # Track the current byte index to avoid repeated calculations
        self._bit_position: int = 0  # Track the current bit position within the byte

    def read(self, f, count: int) -> None:
        """
        Reads `count` bytes from a file-like object `f` and appends them to the internal buffer.
        The buffer grows as new bytes are added.

        Parameters:
        -----------
        f : file-like object
            The file-like object to read data from. Must have a `read()` method.
        count : int
            The number of bytes to read from the object and append to the buffer.

        Notes:
        ------
        This method appends data to the existing buffer without resetting any pointers. It is
        intended to accumulate data as needed for future bit-level extractions.
        """
        self._array += f.read(count)

    def _ensure_length(self, bit_count: int) -> None:
        """
        Ensures that the internal buffer has enough bits to fulfill the request of `bit_count` bits.
        If not enough data is available, raises a ValueError.

        Parameters:
        -----------
        bit_count : int
            The number of bits required to fulfill the request.

        Raises:
        -------
        ValueError:
            If the internal buffer does not contain enough bits to satisfy the request.

        Notes:
        ------
        This function checks the total number of bits in the buffer and compares it to the sum
        of the disregard pointer and the requested bit count. If the buffer lacks sufficient bits,
        an exception is raised to prevent invalid reads.
        """
        total_bits = len(self._array) * 8
        if self._disregard_pointer + bit_count > total_bits:
            raise ValueError("Not enough data in buffer to fulfill request")

    def get(self, bit_count: int) -> int:
        """
        Extracts `bit_count` bits from the buffer and returns them as an integer.

        Parameters:
        -----------
        bit_count : int
            The number of bits to extract from the buffer.

        Returns:
        --------
        int:
            The value of the extracted bits as an integer.

        Raises:
        -------
        ValueError:
            If the buffer does not contain enough bits to extract.

        Notes:
        ------
        This method processes the buffer bit by bit, extracting the specified number of bits
        efficiently. It adjusts the internal bit and byte pointers after each extraction,
        ensuring subsequent reads will be properly aligned.
        """
        self._ensure_length(bit_count)
        value = 0
        bits_needed = bit_count

        while bits_needed > 0:
            available_bits = 8 - self._bit_position
            bits_to_take = min(bits_needed, available_bits)

            # Extract the bits
            current_byte = self._array[self._byte_index]
            extracted_bits = (current_byte >> (available_bits - bits_to_take)) & ((1 << bits_to_take) - 1)

            # Build the value
            value = (value << bits_to_take) | extracted_bits

            # Update pointers
            self._bit_position += bits_to_take
            if self._bit_position == 8:
                self._bit_position = 0
                self._byte_index += 1

            bits_needed -= bits_to_take

        self._disregard_pointer += bit_count

        # Periodically clean the buffer (optional, if needed)
        if self._byte_index >= 1024 * 1024:
            self._clean_buffer()

        return value

    def get_multiple(self, n: int, bit_count: int) -> list[int]:
        """
        Extracts `n` values, each of `bit_count` bits, and returns them as a list of integers.

        Parameters:
        -----------
        n : int
            The number of values to extract.
        bit_count : int
            The number of bits per value to extract from the buffer.

        Returns:
        --------
        list[int]:
            A list of integers representing the extracted `n` values, each consisting of `bit_count` bits.

        Raises:
        -------
        ValueError:
            If the buffer does not contain enough bits to extract all requested values.

        Notes:
        ------
        This method is similar to `get()`, but it processes multiple values at once. It efficiently
        extracts `n` values by looping over the buffer and adjusting the internal pointers to
        ensure proper bit alignment.
        """
        values = []
        total_bits = n * bit_count
        self._ensure_length(total_bits)

        for _ in range(n):
            current_value = 0

            bits_needed = bit_count
            while bits_needed > 0:
                available_bits = 8 - self._bit_position
                bits_to_take = min(bits_needed, available_bits)

                # Extract the bits
                current_byte = self._array[self._byte_index]
                extracted_bits = (current_byte >> (available_bits - bits_to_take)) & ((1 << bits_to_take) - 1)

                # Build the value
                current_value = (current_value << bits_to_take) | extracted_bits

                # Update pointers
                self._bit_position += bits_to_take
                if self._bit_position == 8:
                    self._bit_position = 0
                    self._byte_index += 1

                bits_needed -= bits_to_take

            values.append(current_value)

        self._disregard_pointer += total_bits

        # Periodically clean the buffer (every 1 MB or any other appropriate threshold), could make it slower
        if self._byte_index >= 1024 * 1024:
            self._clean_buffer()

        return values

    def disregard(self, bit_count: int | None = None) -> None:
        """
        Moves the disregard pointer forward by `bit_count` bits, or to the start of the next byte if `bit_count` is None.

        Parameters:
        -----------
        bit_count : int, optional
            The number of bits to disregard. If not provided, the pointer will move to the next byte boundary.

        Notes:
        ------
        This method allows skipping a number of bits, either a specific count or until the
        next byte boundary. It also ensures that the disregard operation does not exceed
        the buffer length.
        """
        if bit_count is None:
            remaining_bits = 8 - self._bit_position
            bit_count = remaining_bits if remaining_bits != 8 else 0

        self._ensure_length(bit_count)
        self._disregard_pointer += bit_count
        self._bit_position += bit_count

        if self._bit_position >= 8:
            self._byte_index += self._bit_position // 8
            self._bit_position %= 8

        # Periodically clean the buffer
        if self._byte_index >= 1024 * 1024:
            self._clean_buffer()

    def _clean_buffer(self) -> None:
        """
        Cleans the internal buffer by removing fully disregarded bytes. This process frees memory
        used by the buffer once the data is no longer needed for future bit operations.

        Notes:
        ------
        The cleaning process involves shifting the buffer to discard already read bytes.
        This is typically done when the byte index exceeds a certain threshold, such as 1 MB,
        to maintain efficiency without excessive memory use.
        """
        if self._byte_index > 0:
            self._array = self._array[self._byte_index:]
            self._disregard_pointer -= self._byte_index * 8
            self._byte_index = 0


class CNumStorage:
    """
    CompressedNumberStorage for efficiently storing and handling integer arrays.
    Numbers are grouped based on their bit length to optimize storage space.

    By default negatives are not storable and will result in strange positive values.

    Technically any other class than ints can be stored but the methods to_bytes(), equality operators,
    bit_length() that scale with the equality operators (we are using max() to know the biggest bit size in a list)
    need to be implemented.
    You'd also need to subclass this class and change load() to load the bytes into your custom class.

    Attributes:
    -----------
    _groups : list[tuple[int, int]]
        A list of tuples where each tuple contains the bit length and index of the corresponding number group.
    _numbers : list[list[int] | None]
        A list where each element is a list of numbers grouped by bit length.
        Some entries may be None if groups have been merged.
    debug : bool
        A flag to enable or disable debugging messages during processing.
    """
    def __init__(self, debug: bool = False) -> None:
        self._groups: list[tuple[int, int]] = []  # (bit_length, idx_to_numbers)
        self._numbers: list[list[int] | None] = []  # Saved numbers, so we can merge, ...
        self.debug: bool = debug

    def _debug_print(self, message: str) -> None:
        """
        Prints a debug message if the debug flag is enabled.

        Parameters:
        -----------
        message : str
            The debug message to be printed.

        Notes:
        ------
        This method is used to facilitate debugging and can help trace the operations
        performed by the class if `debug` is set to True.
        """
        if self.debug:
            print(message)

    def add_numbers(self, numbers: _a.Iterable[int]) -> None:
        """
        Adds numbers from an iterable and groups them by their bit length, preserving the order.

        Parameters:
        -----------
        numbers : iterable of int
            A collection of integers to be added to the storage.

        Notes:
        ------
        This method groups numbers based on their bit length. If the bit length of a new number
        matches the last group's bit length, it is added to that group; otherwise, a new group is created.
        """
        for number in numbers:
            bit_length = number.bit_length()

            # Check if the last group has the same bit length
            if self._groups and self._groups[-1][0] == bit_length:
                # Add to the last group if bit length matches
                self._numbers[self._groups[-1][1]].append(number)
            else:
                # Create a new group if bit length is different
                self._groups.append((bit_length, len(self._numbers)))
                self._numbers.append([number])

    def add_numbers_unorganized(self, numbers: list[int]) -> None:
        """
        Adds a list of numbers as its own group, regardless of their bit length.

        Parameters:
        -----------
        numbers : list of int
            A list of integers to be added as a single group.

        Notes:
        ------
        This method creates a new group for the given list of numbers. It is useful when
        numbers do not need to be grouped by bit length, or when separation between sets of numbers is desired.
        """
        self._groups.append((max(numbers).bit_length(), len(self._numbers)))
        self._numbers.append(numbers.copy())  # Do we need to copy? Yes, as the user could change contents

    def save(self, to: str) -> None:
        """
        Saves the number groups to a binary file.

        Parameters:
        -----------
        to : str
            The path to the file where the data will be saved.

        Notes:
        ------
        The numbers are stored in groups, with each group's metadata (bit length, group size)
        written to the file, followed by the compressed bit-level representation of the numbers.
        """
        with open(to, "wb") as f:
            number_of_groups = len(self._groups)
            f.write(bytes_length(number_of_groups).to_bytes(1, "big"))  # So we get an error if this is longer than 1 byte
            f.write(encode_integer(number_of_groups))

            groups_to_write = []
            current_pos = 0  # f.tell()
            for (bit_length, group_idx) in self._groups:
                group = self._numbers[group_idx]
                groups_to_write.append((bit_length, group))
                f.write(max(1, bytes_length(current_pos)).to_bytes(1, "big"))
                f.write(encode_integer(current_pos))
                f.write(bit_length.to_bytes(1, "big"))  # So we get an error if this is longer than 1 byte
                group_length = len(group)
                f.write(max(1, bytes_length(group_length)).to_bytes(1, "big"))  # So we get an error if this is longer than 1 byte
                f.write(encode_integer(group_length))
                current_pos += ((bit_length * group_length) + 7) // 8

            for (bit_length, group) in groups_to_write:
                self._debug_print(f"Writing {bit_length} group")
                buffer = 0
                bits_in_buffer = 0

                for member in group:
                    buffer = (buffer << bit_length) | member
                    bits_in_buffer += bit_length

                    # Check if we have a full byte(s) in the buffer
                    if (bits_in_buffer / 8).is_integer():
                        f.write(buffer.to_bytes(bits_in_buffer // 8, "big"))
                        # f.write(encode_integer(buffer))
                        bits_in_buffer = 0
                        buffer = 0

                while bits_in_buffer >= 8:
                    bits_in_buffer -= 8
                    byte_to_write = (buffer >> bits_in_buffer) & 0xFF
                    f.write(bytes([byte_to_write]))

                # Write remaining bits if they don't form a full byte
                if bits_in_buffer > 0:
                    # Shift the remaining bits to the left to align to the next byte boundary
                    buffer <<= (8 - bits_in_buffer)
                    f.write(bytes([buffer & 0xFF]))

    def load(self, from_: str) -> None:
        """
        Loads the number groups from a binary file.

        Parameters:
        -----------
        from_ : str
            The path to the file from which the data will be loaded.

        Notes:
        ------
        This method reads the compressed number groups from a file and reconstructs the number
        groups by decompressing the bit-level data.
        """
        self._groups.clear()

        with open(from_, "rb") as f:
            num_groups_length = int.from_bytes(f.read(1), "big")
            num_groups = int.from_bytes(f.read(num_groups_length), "big")

            group_info = []

            for _ in range(num_groups):
                # Read the current group's offset
                offset_length = int.from_bytes(f.read(1), "big")
                offset = int.from_bytes(f.read(offset_length), "big")

                # Read the bit length for this group
                bit_length = int.from_bytes(f.read(1), "big")

                # Read the length of this group (number of elements)
                group_length_length = int.from_bytes(f.read(1), "big")
                group_length = int.from_bytes(f.read(group_length_length), "big")

                group_info.append((offset, bit_length, group_length))

            first_offset = f.tell()
            buffer = BitBuffer()

            for offset, bit_length, group_length in group_info:
                self._debug_print(f"Reading {bit_length} group")
                # Move the file pointer to the correct offset
                f.seek(first_offset + offset)
                buffer.read(f, ((bit_length * group_length) + 7) // 8)

                # Read and decode the data for this group
                self._groups.append((bit_length, len(self._numbers)))
                self._numbers.append(buffer.get_multiple(group_length, bit_length))  # This get multiple takes up
                buffer.disregard()  # 95% of the processing time. (4.5 seconds for 5.5 million 22-bit numbers from 4.6
                #                                                                                      seconds in total)

    def _merge_groups(self, idx0: int, idx1: int, merge_into: _ty.Literal[0, 1],
                      overwrite_bit_len: int | None = None) -> None:
        """
        Merges two groups of numbers into one, updating the group bit length if necessary.

        Parameters:
        -----------
        idx0 : int
            Index of the first group.
        idx1 : int
            Index of the second group.
        merge_into : Literal[0, 1]
            Determines which group to merge into (0 for the first, 1 for the second).
        overwrite_bit_len : int, optional
            If provided, this bit length will overwrite the bit length of the merged group.

        Notes:
        ------
        This method is useful for reducing the number of groups by merging them based on criteria such as
        their bit lengths and sizes. The merging strategy can be customized by setting `merge_into` and
        `overwrite_bit_len`.
        """
        group_0_bit_len, group_0_idx = self._groups[idx0]
        group_1_bit_len, group_1_idx = self._groups[idx1]
        merge_number_idx, other_number_idx, merge_group_idx, other_group_idx, group_bit_len, from_right_merge = (
            (group_0_idx, group_1_idx, idx0, idx1, group_0_bit_len, True),
            (group_1_idx, group_0_idx, idx1, idx0, group_1_bit_len, False)
        )[merge_into]
        del self._groups[other_group_idx]
        if from_right_merge:
            self._numbers[merge_number_idx].extend(self._numbers[other_number_idx])
        else:
            self._numbers[other_number_idx].extend(self._numbers[merge_number_idx])  # Extend is better than joining
            self._numbers[merge_number_idx] = self._numbers[other_number_idx]
        self._numbers[other_number_idx] = None
        self._groups[merge_group_idx] = (overwrite_bit_len or group_bit_len, merge_number_idx)

    def create_optimal_groups(self) -> None:
        """
        Creates space-optimal groups based on the bit length of the numbers.

        Notes:
        ------
        This method ensures that the numbers are grouped optimally by their bit lengths, minimizing
        the storage space required. It is automatically done when adding numbers, but can be manually
        invoked if numbers are added unorganized.
        """
        numbers = self.get_numbers_list()
        self._groups = []
        self._numbers = []
        current_bit_length = None
        current_group = []
        for number in numbers:
            bit_length = number.bit_length()
            if bit_length != current_bit_length:
                if current_group:  # Save the previous group
                    self._groups.append((current_bit_length, len(self._numbers)))
                    self._numbers.append(current_group)
                current_bit_length = bit_length
                current_group = []  # Lists are referenced
            current_group.append(number)
        # Add the last group
        if current_group:
            self._groups[current_bit_length] = current_group

    def adjust_groups(self, max_group_count: int = 5, multiple_of: _ty.Literal[2, 4, 8] | None = None) -> None:
        """
        Merges groups to reduce the total number of groups, optimizing for storage efficiency.

        Parameters:
        -----------
        max_group_count : int, optional
            The maximum number of groups allowed after merging (default is 5).
        multiple_of : Literal[2, 4, 8], optional
            If specified, the bit lengths of the groups will be adjusted to be a multiple of this value.

        Notes:
        ------
        This method merges groups intelligently by analyzing space loss when merging. It attempts
        to minimize the number of groups while optimizing space efficiency. If the `multiple_of`
        parameter is provided, the resulting bit lengths are adjusted to the nearest multiple of
        the specified value.
        """
        current_group_count = len(self._groups)
        if current_group_count <= max_group_count:
            return  # Already in spec

        # Merge groups until we reach the target
        spaces: list[tuple[int, int, int]] = []

        for (bit_len, numbers_idx) in self._groups:
            length = len(self._numbers[numbers_idx])
            spaces.append((bit_len, length, length * bit_len))

        while len(self._groups) > max_group_count:
            # Find two groups that can be merged with the least space loss
            min_loss = float('inf')
            merge_idx = None

            for i in range(len(self._groups) - 1):
                bit_len_1, length_1, curr_space_1 = spaces[i]
                bit_len_2, length_2, curr_space_2 = spaces[i + 1]
                new_bit_len = max(bit_len_1, bit_len_2)  # Can't merge 7 bits into 6

                # If multiple_of is specified, adjust the new bit length to the nearest multiple
                if multiple_of:
                    new_bit_len = ((new_bit_len + multiple_of - 1) // multiple_of) * multiple_of

                space_before = curr_space_2 + curr_space_1
                space_after = (length_2 + length_1) * new_bit_len
                space_loss = space_after - space_before

                if space_loss < min_loss:
                    min_loss = space_loss
                    merge_idx = i

            bit_len_1, length_1, curr_space_1 = spaces[merge_idx]
            bit_len_2, length_2, curr_space_2 = spaces[merge_idx + 1]
            new_bit_len = max(bit_len_1, bit_len_2)
            if multiple_of:
                new_bit_len = ((new_bit_len + multiple_of - 1) // multiple_of) * multiple_of
            self._merge_groups(merge_idx, merge_idx + 1, 0, overwrite_bit_len=new_bit_len)

            # Update the size and space after the merge
            new_length = length_1 + length_2
            new_space = new_length * new_bit_len
            spaces[merge_idx] = (new_bit_len, new_length, new_space)
            del spaces[merge_idx + 1]  # To keep it up to date

        if multiple_of:
            for i in range(len(self._groups)):
                bit_length, numbers_idx = self._groups[i]
                if bit_length % multiple_of != 0:
                    # Adjust the bit length to the nearest multiple
                    new_bit_length = ((bit_length + multiple_of - 1) // multiple_of) * multiple_of
                    self._groups[i] = (new_bit_length, numbers_idx)
                    old_length = spaces[i][1]
                    spaces[i] = (new_bit_length, old_length, old_length * new_bit_length)
        to_merge = []
        for i in range(len(self._groups) - 1):
            bit_len_1, length_1, curr_space_1 = spaces[i]
            bit_len_2, length_2, curr_space_2 = spaces[i + 1]
            if bit_len_1 == bit_len_2:  # Merge successive groups
                to_merge.append(i)
        for i, merge_idx in enumerate(to_merge):
            merge_idx = merge_idx - i  # To merge is in order so we know how many we already merged
            self._merge_groups(merge_idx, merge_idx + 1, 0)

    def _calculate_total_size(self, groups: list[tuple[int, int]], numbers: list[list[int] | None]) -> int:
        total_size = 0
        for (bit_len, numbers_idx) in groups:
            total_size += (len(numbers[numbers_idx]) * bit_len) // 8
        return total_size

    def get_total_size(self) -> int:
        """
        Returns the total size of all stored numbers in bits.

        Returns:
        --------
        int:
            The total number of bits required to store all the numbers in the instance.

        Notes:
        ------
        This method calculates the total number of bits required for all the numbers stored in the
        instance. It does not account for metadata or buffer overheads.
        """
        return self._calculate_total_size(self._groups, self._numbers)

    def get_total_number_of_numbers(self) -> int:
        """
        Returns the total number of elements (numbers) stored in this CNumStorage instance.

        Returns:
        --------
        int:
            The total number of numbers stored across all groups.

        Notes:
        ------
        This method sums up the lengths of all the number groups to determine how many numbers
        are stored in the instance.
        """
        return sum(len(self._numbers[x]) for (_, x) in self._groups)

    def get_numbers(self) -> list[list[int] | None]:
        """
        Returns the internal list of number groups.

        Returns:
        --------
        list[list[int] | None]:
            The internal list of number groups. Each element corresponds to a group of numbers
            and can be accessed by its group index.

        Notes:
        ------
        This method provides direct access to the internal `_numbers` attribute, allowing for inspection
        of the number groups based on their indices. Some entries may be `None` if groups have been merged.
        """
        return self._numbers

    def get_numbers_list(self) -> list[int]:
        """
        Returns a flattened list of all numbers stored in the instance.

        Returns:
        --------
        list[int]:
            A single list containing all numbers stored in the instance, regardless of grouping.

        Notes:
        ------
        This method flattens the number groups into a single list, removing `None` values from
        merged groups, and returns the complete list of stored numbers.
        """
        return sum([x for x in self._numbers if x is not None], [])

    def get_groups(self) -> list[tuple[int, int]]:
        """
        Returns the list of groups, where each group is a tuple containing the bit length and
        the index of the corresponding number group.

        Returns:
        --------
        list[tuple[int, int]]:
            A list of tuples representing the groups, where each tuple contains the bit length
            of the group and the index to the corresponding number list in `_numbers`.

        Notes:
        ------
        This method provides a structured overview of the stored groups, including their bit lengths
        and their indices within the `_numbers` attribute.
        """
        return self._groups

    def __eq__(self, other: _ty. Self) -> bool:
        """
        Compares two CNumStorage instances for equality based on their stored numbers.

        Parameters:
        -----------
        other : CNumStorage
            Another CNumStorage instance to compare against.

        Returns:
        --------
        bool:
            True if both instances contain the same numbers in the same structure; otherwise, False.

        Notes:
        ------
        This method checks for structural equality between two instances by comparing their internal
        number lists. If any differences are found, it returns False. Debug information is printed if
        the `debug` flag is enabled and differences are encountered.
        """
        numbers, other_numbers = self.get_numbers_list(), other.get_numbers_list()
        if len(numbers) != len(other_numbers):
            self._debug_print("Other CNumStorage Instance stores a different amount of numbers.")
            return False
        for i in range(len(numbers)):
            if numbers[i] != other_numbers[i]:
                self._debug_print(_cutoff_iterable(numbers, i, 0, 0, True))
                self._debug_print(_cutoff_iterable(other_numbers, i, 0, 0, True))
                return False
        return True


def set_bits(bytes_like: bytes | bytearray, start_position: int, bits_: str,
             byte_order: _ty.Literal["big", "little"] = "big", return_bytearray: bool = False,
             auto_expand: bool = False):
    """Set specific bits in a byte sequence.

    Args:
        bytes_like (bytes | bytearray): Original bytes or bytearray to modify.
        start_position (int): Start position for the bits.
        bits_ (str): A string of bits ('0' or '1') to set at the start position.
        byte_order (Literal["big", "little"], optional): Byte order. Defaults to "big".
        return_bytearray (bool, optional): If True, return a bytearray. Otherwise, return bytes.
        auto_expand (bool, optional): If True, automatically expand bytearray if necessary.

    Returns:
        bytes | bytearray: The modified byte sequence.
    """
    byte_arr = bytearray(bytes_like) if not isinstance(bytes_like, bytearray) else bytes_like
    for i, bit in zip(range(start_position, start_position + len(bits_)), [int(char) for char in bits_]):
        byte_index = i // 8
        bit_index = i % 8 if byte_order == "little" else ((len(bytes_like) * 8) - i % 8) - 1
        bit_index -= (((len(bytes_like) - 1) - byte_index) * 8)
        if byte_index >= len(byte_arr) and auto_expand:
            if byte_order == "big":
                byte_arr.append(0)
            else:
                byte_arr = bytearray(1) + byte_arr
        if bit:
            byte_arr[byte_index] |= (1 << (bit_index - (byte_index * 8)))
        else:
            byte_arr[byte_index] &= ~(1 << bit_index - (byte_index * 8))
    return bytes(byte_arr) if not return_bytearray else byte_arr


def bits(bytes_like: bytes | bytearray, return_str: bool = False) -> list | str:
    """Convert bytes or bytearray to a list or string of binary representations.

    Args:
        bytes_like (bytes | bytearray): The byte sequence to convert.
        return_str (bool, optional): If True, return as a single concatenated string.

    Returns:
        list | str: List of binary strings, or a single concatenated binary string.
    """
    bytes_like = bytes_like if isinstance(bytes_like, bytes) else bytes(bytes_like)
    binary = "00000000" + bin(int.from_bytes(bytes_like))[2:]
    if return_str:
        return ''.join(list(reversed([binary[i-8:i] for i in range(len(binary), 0, -8)[:-1]])))
    return list(reversed([binary[i-8:i] for i in range(len(binary), 0, -8)[:-1]]))


def nice_bits(bytes_like: bytes | bytearray, spaced: bool = False, wrap_count: int = 0,
              to_chars: bool = False, edge_space: bool = False) -> str:
    """Format bits with options for spacing, wrapping, and conversion to characters.

    Args:
        bytes_like (bytes | bytearray): Byte sequence to format.
        spaced (bool, optional): If True, add spaces between bits for readability.
        wrap_count (int, optional): Number of bits per line before wrapping.
        to_chars (bool, optional): If True, convert bits to characters when possible.
        edge_space (bool, optional): If True, add extra space at line edges.

    Returns:
        str: Formatted bit string.
    """
    bytes_like = bytes_like if isinstance(bytes_like, bytes) else bytes(bytes_like)
    this = [""] + bits(bytes_like)
    i = 0
    wrap_count = wrap_count if wrap_count > 0 else len(this) - 1
    for i in range(0, len(this), wrap_count):
        if edge_space and i+1 < len(this):
            this[i+1] = " " + this[i+1]
        if i + wrap_count < len(this):
            chars = "  " + ''.join([chr(int(x, 2)) for x in this[i+1:i+wrap_count+1] if x])
            this[i + wrap_count] += (chars if to_chars else "") + ("\n" if i+wrap_count != len(this)-1 else "")
            if spaced:
                for chunk_id in range(i+1, i+wrap_count):
                    this[chunk_id] += " "
        else:
            if spaced:
                for chunk_id in range(i+1, len(this)-1):
                    this[chunk_id] += " "
    if to_chars:
        this[-1] += ("         " if spaced else "        ")*((i + wrap_count)-len(this)+1) + "  " + ''.join([chr(int(x, 2)) for x in this[i+1:len(this)] if x])
    binary_str = ''.join(this)
    return binary_str  # ("00000000" + binary)[7 + (len(binary) // 8):]


def bytes_to_human_readable_binary_iec(size: int | float) -> str:
    """Convert bytes to a human-readable binary string using IEC units.

    Args:
        size (int | float): The size in bytes.

    Returns:
        str: The size formatted as a human-readable string (e.g., "1.00 MiB").
    """
    units = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.2f} {unit}"
        size /= 1024


def bytes_to_human_readable_decimal_si(size: int | float) -> str:
    """Convert bytes to a human-readable string using decimal SI units.

    Args:
        size (int | float): The size in bytes.

    Returns:
        str: The size formatted as a human-readable string (e.g., "1.00 MB").
    """
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB', 'RB', 'QB']
    for unit in units:
        if size < 1000 or unit == units[-1]:
            return f"{size:.2f} {unit}"
        size /= 1000


def bits_to_human_readable(size: int | float) -> str:
    """Convert bits to a human-readable string using SI units.

    Args:
        size (int | float): The size in bits.

    Returns:
        str: The size formatted as a human-readable string (e.g., "1.00 Mbps").
    """
    units = ['bps', 'Kbps', 'Mbps', 'Gbps', 'Tbps']
    for unit in units:
        if size < 1000 or unit == units[-1]:  # Ensure we don't exceed the last unit
            return f"{size:.2f} {unit}"
        size /= 1000
