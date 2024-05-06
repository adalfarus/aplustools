from aplustools.package import install_dependencies_lst as _install_dependencies_lst
from typing import Union as _Union
import ctypes as _ctypes
from typing import Tuple as _Tuple


def install_dependencies():
    success = _install_dependencies_lst(["requests==2.31.0", "PySide6==6.6.1", "Pillow==10.3.0", "aiohttp==3.9.3",
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
    byte_size = (num.bit_length() + 8) // 8  # Determine the required number of bytes
    return num.to_bytes(byte_size, 'big', signed=(True if num < 0 else False) or overwrite_signed)


def decode_int(bytes_like: bytes, signed: bool = False) -> int:
    return int.from_bytes(bytes_like, 'big', signed=signed)


def encode(to_encode: _Union[int, str]) -> bytes:
    if type(to_encode) is int:
        return encode_int(to_encode)
    return b''.join([encode_int(ord(char)) for char in to_encode])


def decode(bytes_like: bytes, return_int: bool = False) -> _Union[int, str]:
    if len(bytes_like) > 1 and not return_int:
        return ''.join([chr(x) for x in bytes_like])  # [chr(decode_int(x)) for x in bytes_like.iter_bytes()]
    return decode_int(bytes_like)


def bits(bytes_like: bytes) -> list:
    binary = "00000000" + bin(int.from_bytes(bytes_like))[2:]
    return list(reversed([binary[i-8:i] for i in range(len(binary), 0, -8)[:-1]]))


def nice_bits(bytes_like: bytes, spaced: bool = False, wrap_count: int = 0, to_chars: bool = False, edge_space: bool = False) -> str:#
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


def isEvenFloat(x: _Union[float, str]) -> _Tuple[bool, bool]:
    if x != x:  # Check for NaN
        return False, False
    if x in [float('inf'), float('-inf')]:  # Check for infinities
        return False, False
    if x == 0.0:  # Zero is even by conventional definition
        return True, True

    expo, dec = str(x).split(".")

    return isEvenInt(int(expo)), isEvenInt(int(dec))


def isOddFloat(x: _Union[float, str]) -> _Tuple[bool, bool]:
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
