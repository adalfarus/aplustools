from aplustools.package import install_dependencies_lst as _install_dependencies_lst


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


def encode_int(num: int) -> bytes:
    byte_size = (num.bit_length() + 7) // 8  # Determine the required number of bytes
    return num.to_bytes(byte_size, 'big')


def decode_int(bytes_like: bytes) -> int:
    return int.from_bytes(bytes_like)


def encode(to_encode: _Union[int, str]) -> bytes:
    if type(to_encode) is int:
        return encode_int(to_encode)
    return b''.join([encode_int(ord(char)) for char in to_encode])


def decode(bytes_like: bytes, return_int: bool = False) -> _Union[int, str]:
    if len(bytes_like) > 1 and not return_int:
        return ''.join([chr(x) for x in bytes_like])
    return decode_int(bytes_like)


def bits(bytes_like: bytes) -> list:
    binary = "00000000" + bin(int.from_bytes(bytes_like))[2:]
    return list(reversed([binary[i-8:i] for i in range(len(binary), 0, -8)]))


def nice_bits(bytes_like: bytes, spaced: bool = False, wrap_count: int = 0, to_chars: bool = False) -> str:
    this = bits(bytes_like)
    i = 0
    for i in range(0, len(this), wrap_count if wrap_count > 0 else 1):
        if not i + wrap_count < len(this):
            break
        chars = "  " + ''.join([chr(int(x, 2)) for x in this[i+1:i+wrap_count+1] if x])
        this[i + wrap_count] += (chars if to_chars else "") + ("\n" if wrap_count > 0 else "")
    if to_chars:
        this[-1] += "         "*((i + wrap_count)-len(this)+1) + "  " + ''.join([chr(int(x, 2)) for x in this[i+1:len(this)] if x])
    binary_str = ' '.join(this)
    return binary_str if spaced else binary_str[1:]  # ("00000000" + binary)[7 + (len(binary) // 8):]


if __name__ == "__main__":
    bit = nice_bits(encode("Hello you world!"), True, 6, True)

    print(bit)
    encoded = encode_float(0.1)
    decoded = decode_float(encoded)
    print(f"0.1 -> {encoded} -> {decoded}")
    print(decode(encode("HELL")))
