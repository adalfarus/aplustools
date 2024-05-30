from aplustools.package import install_dependencies_lst as _install_dependencies_lst
from typing import Union as _Union
import ctypes as _ctypes
import typing as _typing
from aplustools.package.argumint import EndPoint as _EndPoint


def install_dependencies():
    success = _install_dependencies_lst(["requests==2.31.0", "PySide6==6.6.1", "Pillow==10.3.0", "aiohttp==3.9.4",
                                         "opencv-python==4.9.0.80", "pillow_heif==0.15.0", "numpy==1.26.4"])
    if not success:
        return
    print("Done, all possible dependencies for the data module installed ...")


def truedivmod(__x, __y):
    return (lambda q, r: (int(q), r))(*divmod(__x, __y))


def encode_float(floating_point: float) -> bytes:
    return _ctypes.c_uint32.from_buffer(_ctypes.c_float(floating_point)).value.to_bytes(4, 'big')


def decode_float(bytes_like: bytes) -> float:
    value_bits = int.from_bytes(bytes_like, 'big')
    return _ctypes.c_float.from_buffer(_ctypes.c_uint32(value_bits)).value


def encode_int(num: int, overwrite_signed: bool = False) -> bytes:
    byte_size = (num.bit_length() + 7) // 8  # Determine the required number of bytes
    return num.to_bytes(byte_size if num != 0 else 1, 'big', signed=(True if num < 0 else False) or overwrite_signed)


def encode_positive_int(num: int) -> bytes:
    byte_size = (num.bit_length() + 7) // 8  # Determine the required number of bytes
    return num.to_bytes(byte_size if num != 0 else 1, 'big')


def encode_possible_negative_int(num: int) -> bytes:
    byte_size = (num.bit_length() + 7) // 8  # Determine the required number of bytes
    return num.to_bytes(byte_size if num != 0 else 1, 'big', signed=True)


def decode_int(bytes_like: bytes, signed: bool = False) -> int:
    return int.from_bytes(bytes_like, 'big', signed=signed)


def decode_positive_int(bytes_like: bytes) -> int:
    return int.from_bytes(bytes_like, 'big')


def decode_possible_negative_int(bytes_like: bytes) -> int:
    return int.from_bytes(bytes_like, 'big', signed=True)


def encode(to_encode: _Union[int, str]) -> bytes:
    if type(to_encode) is int:
        return encode_int(to_encode)
    return b''.join([encode_int(ord(char)) for char in to_encode])


def decode(bytes_like: bytes, return_int: bool = False) -> _Union[int, str]:
    if len(bytes_like) > 1 and not return_int:
        return ''.join([chr(x) for x in bytes_like])  # [chr(decode_int(x)) for x in bytes_like.iter_bytes()]
    return decode_int(bytes_like)


def bits(bytes_like: _typing.Union[bytes, bytearray]) -> list:
    bytes_like = bytes_like if isinstance(bytes_like, bytes) else bytes(bytes_like)
    binary = "00000000" + bin(int.from_bytes(bytes_like))[2:]
    return list(reversed([binary[i-8:i] for i in range(len(binary), 0, -8)[:-1]]))


def nice_bits(bytes_like: _typing.Union[bytes, bytearray], spaced: bool = False, wrap_count: int = 0,
              to_chars: bool = False, edge_space: bool = False) -> str:
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


def minmax(min_val, max_val, to_reduce):
    return max(max_val, min(min_val, to_reduce))


def isEven(x: _Union[int, float, str]) -> bool:
    return (int(x) & 1) == 0 if not isinstance(x, str) else (len(x) & 1) == 0


def isOdd(x: _Union[int, float, str]) -> bool:
    return (int(x) & 1) == 1 if not isinstance(x, str) else (len(x) & 1) == 1


def isEvenInt(x: int) -> bool:
    return (x & 1) == 0


def isOddInt(x: int) -> bool:
    return (x & 1) == 1


def isEvenFloat(x: _Union[float, str]) -> _typing.Tuple[bool, bool]:
    if x != x:  # Check for NaN
        return False, False
    if x in [float('inf'), float('-inf')]:  # Check for infinities
        return False, False
    if x == 0.0:  # Zero is even by conventional definition
        return True, True

    expo, dec = str(x).split(".")

    return isEvenInt(int(expo)), isEvenInt(int(dec))


def isOddFloat(x: _Union[float, str]) -> _typing.Tuple[bool, bool]:
    if x != x:  # Check for NaN
        return False, False
    if x in [float('inf'), float('-inf')]:  # Check for infinities
        return False, False
    if x == 0.0:  # Zero is even by conventional definition
        return False, False

    expo, dec = str(x).split(".")

    return isOddInt(int(expo)), isOddInt(int(dec))


def isEvenString(x: str) -> bool:
    return (len(x) & 1) == 0


def isOddString(x: str) -> bool:
    return (len(x) & 1) == 1


def nice_number(number: int, seperator: str = "."):
    formatted_number = [str(number)[-((i * 3) + 1) - 2:-(i * 3) or None] for i, part in enumerate(str(number)[-1::-3])]
    formatted_number.reverse()
    return f"{seperator.join(formatted_number)}"


def what_func(func, type_names: bool = False):
    endpoint = _EndPoint(func)

    def get_type_name(t):
        if hasattr(t, '__origin__') and t.__origin__ is _typing.Union or type(t) is _typing.Union and type(None) in t.__args__:
            non_none_types = [arg for arg in t.__args__ if arg is not type(None)]
            return f"{t.__name__}[{', '.join(get_type_name(arg) for arg in non_none_types)}]"
        return t.__name__ if hasattr(t, '__name__') else (type(t).__name__ if t is not None else None)

    arguments_str = ''.join([f"{argument.name}: "
                             f"{(get_type_name(argument.type) or type(argument.default)).__name__ if type_names else get_type_name(argument.type) or type(argument.default)}"
                             f" = {argument.default}, " for argument in endpoint.arguments])[:-2]
    print(f"{func.__module__}.{endpoint.name}({arguments_str}){(' -> ' + str(endpoint.return_type)) if endpoint.return_type is not None else ''}")


def bytes_to_human_readable_binary_iec(size: int) -> str:
    """Convert bytes to a human-readable string."""
    units = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.2f} {unit}"
        size /= 1024


def bytes_to_human_readable_decimal_si(size: int) -> str:
    """Convert bytes to a human-readable string."""
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB', 'RB', 'QB']
    for unit in units:
        if size < 1000 or unit == units[-1]:
            return f"{size:.2f} {unit}"
        size /= 1000


def bits_to_human_readable(size: float) -> str:
    """Convert bits to a human-readable string using SI units."""
    units = ['bps', 'Kbps', 'Mbps', 'Gbps', 'Tbps']
    for unit in units:
        if size < 1000 or unit == units[-1]:  # Ensure we don't exceed the last unit
            return f"{size:.2f} {unit}"
        size /= 1000


def iterbytes(bytes_like: _typing.Union[bytes, bytearray]):
    for byte in bytes_like:
        yield chr(byte).encode()


def set_bits(bytes_like: _typing.Union[bytes, bytearray], start_position: int, bits: str,
             byte_order: _typing.Literal["big", "little"] = "big", return_bytearray: bool = False,
             auto_expand: bool = False):
    byte_arr = bytearray(bytes_like) if not isinstance(bytes_like, bytearray) else bytes_like
    for i, bit in zip(range(start_position, start_position + len(bits)), [int(char) for char in bits]):
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


def bytes_length(data: _typing.Union[int, float, str]) -> int:
    total_length = 0
    if isinstance(data, str):
        for char in data:
            total_length += (ord(char).bit_length() + 7) // 8
    elif isinstance(data, float):
        total_length = len(encode_float(data))
    else:
        total_length = (data.bit_length() + 7) // 8
    return total_length


def bit_length(data: _typing.Union[int, float, str]) -> int:
    total_length = 0
    if isinstance(data, str):
        for char in data:
            total_length += ord(char).bit_length()
    elif isinstance(data, float):
        total_length = len(encode_float(data))
    else:
        total_length = data.bit_length()
    return total_length


class Bits:
    def __init__(self, bytes_like):
        self.bytes = bytes_like

    def __repr__(self):
        return f"{self.__class__.__name__}({nice_bits(self.bytes, True)})"


class UniversalBits(Bits):
    def __init__(self, object: _Union[str, float, int, bytes, bytearray, bool]):
        if type(object) in [str, int]:
            my_bytes = encode(object)
        elif isinstance(object, float):
            my_bytes = encode_float(object)
        elif isinstance(object, bool):
            my_bytes = b"\x01" if object else b"\x00"
        else:
            my_bytes = object
        super().__init__(my_bytes)


def lod_helper(curr_lod, big_lster, depth):  # Make iterative instead of recursive
    for x in curr_lod:
        if isinstance(x, list) and depth > 0:
            lod_helper(x, big_lster, depth - 1)
        else:
            big_lster.append(x)
    return big_lster


def unnest_iterable(iterable, max_depth: int = 4):
    return lod_helper(iterable, [], max_depth)


if __name__ == "__main__":
    bit = nice_bits(encode("Hello you world!"), True, 6, True, True)
    bitss = bits(encode_float(0.3))
    print(bitss)
    print(decode_int(encode_int(-2000), True))

    print(bit)
    encoded = encode_float(0.1)
    decoded = decode_float(encoded)
    print(f"0.1 -> {encoded!r} -> {decoded}")
    print(decode(encode("HELL")))

    print(isEven(4))
    print(isOddString("jel"))
    print(isEvenFloat(1238.2312))
    print(isEvenFloat(1239.2312))

    print(nice_number(1666))
    print(decode_possible_negative_int(encode_possible_negative_int(2000)))

    what_func(lambda x=1, y=2: 1, True)

    def func(x: _typing.Optional[1] = None, u: _typing.Union[8, 1] = 1):
        pass
    what_func(func)

    print(bits(set_bits(int(255).to_bytes(1, "big"), 0, "0000000")))

    print(Bits(b"\x00"), UniversalBits(bytearray(b"\x11")))
