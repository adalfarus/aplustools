"""TBA"""
import os
import tempfile

import pytest
from ...data.bintools import *

import io

# Standard typing imports for aps
import typing_extensions as _te
import collections.abc as _a
import typing as _ty
if _ty.TYPE_CHECKING:
    import _typeshed as _tsh
import types as _ts


def test_float_encoding_decoding() -> None:
    for value in [0.0, 1.0, -3.14, 123456.789]:
        for precision in ["single", "double"]:
            encoded = encode_float(value, precision)
            decoded = decode_float(encoded, precision)
            assert pytest.approx(decoded, rel=1e-5) == value


@pytest.mark.parametrize("val, negatives, will_panic", [
    (0, False, False),
    (0, True, False),
    (127, False, False),
    (127, True, False),
    (255, False, False),
    (255, True, False),
    (256, False, False),
    (256, True, False),
    (-1, False, True),
    (-1, True, False),
    (-256, False, True),
    (-256, True, False)
])
def test_integer_encoding_decoding(val: int, negatives: bool, will_panic: bool) -> None:
    if will_panic:
        with pytest.raises(ValueError):
            test_integer_encoding_decoding(val, negatives, False)
    else:
        encoded = encode_integer(val, negatives=negatives)
        decoded = decode_integer(encoded, negatives=negatives)
        assert decoded == val


def test_bytes_and_bit_length() -> None:
    assert bytes_length("hello") == 5
    assert bytes_length(42) >= 1
    assert bit_length(255) == 8
    assert bit_length("abc") == 24
    assert bit_length(3.14) > 0


def test_variable_length_encoding() -> None:
    lst = [b''.join([encode_integer(x) for x in range(0, y // 10_000)]) for y in range(0, 10_000_000, 100_000)]
    for original in lst:
        # original = b"hello world"
        encoded = get_variable_bytes_like(original)
        stream = io.BytesIO(encoded)
        result = read_variable_bytes_like(stream)
        assert result == original


def test_varint_encoding_decoding() -> None:
    for num in [0, 1, 127, 128, 255, 300, 16384, 2**32 - 1, 2**63 - 1]:
        encoded = to_varint_length(num)
        stream = io.BytesIO(encoded)
        decoded = read_varint_length(stream)
        assert decoded == num, f"Failed for {num}"


def test_varint_negative_input() -> None:
    with pytest.raises(ValueError):
        to_varint_length(-1)


def test_varint_eof() -> None:
    with pytest.raises(EOFError):
        read_varint_length(io.BytesIO(b""))  # No data


# @pytest.mark.filterwarnings("ignore:to_progressive_length ran out of buffer space")
def test_progressive_encoding() -> None:
    # with pytest.warns(RuntimeWarning):
    lst = [b''.join([bytes(x) for x in range(0, y // 10_000)]) for y in range(0, 10_000_000, 100_000)]
    for original in lst:
        # original = b"hello world"
        encoded = get_progressive_bytes_like(original)
        stream = io.BytesIO(encoded)
        result = read_progressive_bytes_like(stream)
        assert result == original


# @pytest.mark.filterwarnings("ignore:to_progressive_length ran out of buffer space")
def test_progressive_length_encoding() -> None:
    # with pytest.warns(RuntimeWarning):
    lst = [c for c in range(0, 10_000_000, 1_000)]
    for length in lst:
        encoded = to_progressive_length(length)
        stream = io.BytesIO(encoded)
        decoded = read_progressive_length(stream)
        assert decoded == length


def test_progressive_negative_input() -> None:
    with pytest.raises(ValueError):
        to_progressive_length(-1)


def test_progressive_eof() -> None:
    with pytest.raises(EOFError):
        read_progressive_length(io.BytesIO(b""))  # No data


def test_bitbuffer_get_single_bits() -> None:
    buffer = BitBuffer()
    buffer.read(io.BytesIO(b"\b"), 1)  # 0b00001000
    assert buffer.get(1) == 0
    assert buffer.get(3) == 0
    assert buffer.get(4) == 8  # Remaining bits: 1000 -> reads as 8


def test_bitbuffer_get_multiple() -> None:
    buffer = BitBuffer()
    buffer.read(io.BytesIO(b"\xF0"), 1)  # 0b11110000
    assert buffer.get_multiple(4, 2) == [3, 3, 0, 0]


def test_bitbuffer_disregard_specific() -> None:
    buffer = BitBuffer()
    buffer.read(io.BytesIO(b"\xAA"), 1)  # 0b10101010
    buffer.disregard(3)
    assert buffer.get(5) == 10  # Remaining bits: 01010 -> 10


def test_bitbuffer_disregard_to_byte_boundary() -> None:
    buffer = BitBuffer()
    buffer.read(io.BytesIO(b"\xFF\x0F"), 2)
    buffer.get(3)  # consume 3 bits
    buffer.disregard()  # should skip to next byte
    assert buffer.get(4) == 0  # from second byte: 00001111


def test_bitbuffer_insufficient_bits() -> None:
    buffer = BitBuffer()
    buffer.read(io.BytesIO(b"\x00"), 1)
    try:
        buffer.get(20)
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_add_and_group_numbers() -> None:
    s = CNumStorage()
    s.add_numbers([1, 2, 3, 8, 9])
    groups = s.get_groups()
    assert len(groups) >= 1
    all_nums = s.get_numbers_list()
    assert all_nums == [1, 2, 3, 8, 9]


def test_save_and_load_roundtrip() -> None:
    s1 = CNumStorage()
    s1.add_numbers([1, 2, 3, 8, 9, 127, 128, 300, 4000])

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        path = tmp.name

    try:
        s1.save(path)

        s2 = CNumStorage()
        s2.load(path)

        assert s1 == s2
        assert s2.get_numbers_list() == [1, 2, 3, 8, 9, 127, 128, 300, 4000]
    finally:
        os.remove(path)


def test_unorganized_add() -> None:
    s = CNumStorage()
    s.add_numbers_unorganized([1, 128, 2])
    nums = s.get_numbers_list()
    assert nums == [1, 128, 2]


def test_merge_groups_behavior() -> None:
    s = CNumStorage()
    s.add_numbers([1, 2])
    s.add_numbers([128, 255])
    assert len(s.get_groups()) == 3  # Not add numbers unorganized and 1 and 2 have different bit lengths
    s.merge_groups(0, 1)
    assert len(s.get_groups()) == 2
    assert s.get_total_number_of_numbers() == 4


def test_adjust_groups() -> None:
    s = CNumStorage()
    s.add_numbers_unorganized([1, 2])
    s.add_numbers_unorganized([128])
    s.add_numbers_unorganized([30000])
    s.add_numbers_unorganized([400000])
    s.add_numbers_unorganized([50000000])
    assert len(s.get_groups()) == 5
    s.adjust_groups(max_group_count=2)
    assert len(s.get_groups()) <= 2


def test_eq_and_debug() -> None:
    a = CNumStorage()
    b = CNumStorage()
    a.add_numbers([1, 2, 3])
    b.add_numbers([1, 2, 3])
    assert a == b
    b.add_numbers([4])
    assert a != b


def test_set_bits() -> None:
    assert set_bits(b"\x00", 0, "11", "big", False, False) == b"\xc0"
    assert set_bits(b"\x00", 0, "1111111111", "big", False, True) == b"\xff\xc0"
    b = bytearray(b'\x00\x00')
    out = set_bits(b, 3, '1011', return_bytearray=True)
    assert bits(out, return_str=True) == "00010110 00000000".replace(" ", "")


def test_bits() -> None:
    assert bits(b'\x01\x02') == ['00000001', '00000010']
    assert bits(b'\xFF', return_str=True) == "11111111"


def test_nice_bits() -> None:
    assert nice_bits(b'\xFF') == "11111111"
    assert nice_bits(b'\xFF\xFF', spaced=True) == "11111111 11111111"
    assert nice_bits(b'\x41', to_chars=True) == "01000001  A          "


def test_human_readables() -> None:
    assert bytes_to_human_readable_binary_iec(1024) == "1.00 KiB"
    assert bytes_to_human_readable_decimal_si(1000) == "1.00 kB"
    assert bits_to_human_readable(8192) == "8.19 Kbps"
