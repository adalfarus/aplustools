# Made by me :)

# Concept:
# Is stream and chunk based (so chunks but not limited by byte sizes)
# Firstly we have a length indicator:
# 0 -> 8 bits
# 10 -> 16 bits
# 110 -> 21 bits (~2 million code points)
# 111 -> 0 bits

# We have 1 bit to tell us if it's in relation to the last chunk (bundle)
# 0 -> Off
# 1 -> On

# Then we have the rest of the data so it looks like this:

# 1 Encoded:
# 0 0 0000 0001
# ^ Size

# At the very end of the last chunk, it appends one 1 and then 0 to fill the last byte
# (Only if the communication can only transmit full bytes)

# or 10 000 that is a bundle end (If something is in-between a bundle start and a bundle end it is automatically
# in-relation, even if in-relation is turned off, so usually it's turned off and implied)
# 10 1 0 0010 0111 0001 0000
# ^^ ^ ^
# Size & in-relation & end of a bundle

from ..data import (encode_possible_negative_int, encode_positive_int, nice_bits, bits, nice_number,
                    decode_possible_negative_int, set_bits, decode_positive_int, bit_length)
import math


# From now on there is a 3 bit encoding that is just a regular number (1 trough 8)
# so 000 is 0, 001 is 1, 010 is 2, 011 is 3, 100 is 4, 101 is 5, 110 is 6, 111 is 7
# These correspond to bit lengths as followed:
# 0, 1, 2,  3,  4,  5,  6,  7
# 4, 6, 8, 10, 12, 16, 20, 24
#       ^      ^^          ^^
import warnings


warnings.warn(
    "This module is not yet finished and shouldn't be used yet",
    RuntimeWarning,
    stacklevel=2
)


def encode_length_svf(max_bit_length, length, pack_at_start: bool = True):
    """Encode Length small values first aims to make the encoding bits of small length very small in exchange for larger
    bit length when dealing with larger values."""
    if length - 1 > max_bit_length or length < 1:
        raise ValueError("Length out of allowed range")

    curr_length = 0
    curr_string = ""
    while curr_length < length:
        if curr_length == length - 1:
            # Add '0' if it's the last required digit and it's not the maximum length
            curr_string += "0"
        else:
            # Otherwise, continue with '1'
            curr_string += "1"
        curr_length += 1 if curr_length < max_bit_length - 1 else 2  # Break out if it's the maximum length

    bit_list = [int(x) for x in list(curr_string)]

    # Pack bits into bytes
    byte_array = bytearray(math.ceil(((length * 8) + (len(bit_list)) / 8)))
    byte_array = set_bits(byte_array, 0, ''.join((str(x) for x in bit_list)),
                          "big" if pack_at_start else "little", True)

    return bytes(byte_array), len(bit_list)


def decode_length_svf(max_bit_length, encoded_bytes):
    """Encode Length small values first decodes encode_length_svf."""
    length = 0
    bits_str = encoded_bytes#''.join(bits(encoded_bytes))

    for i, bit in enumerate(bits_str):
        if length == max_bit_length:
            return length + 1, i
        elif int(bit) == 0:  # Check if the current bit is 0 or the max bit length.
            return length + 1, i + 1
        length += 1
    raise ValueError("Invalid encoded length or incomplete data")


def pack_number_at_end(num, total_bytes):
    # Number of bits in the total output space
    output_capacity_bits = total_bytes * 8

    # Calculate how many bits are unused (padding needed to align right)
    padding_bits = output_capacity_bits - num.bit_length()

    # Prepare the output byte array
    output = bytearray(total_bytes)  # create a byte array of the specified size

    # Insert the number into the output, starting from the least significant bit
    for i in range(total_bytes):
        # Calculate bit positions for slicing the number
        start_bit = padding_bits + 8 * i

        byte_slice = (num >> (start_bit - padding_bits)) & 0xFF
        output[i] = byte_slice

    output.reverse()
    return output


class Unien:
    def __init__(self):
        self._buffer = ""
        self._completed = ""

    def add_chunk(self, chunk: bytes, completed: bool = True):
        bit_str = nice_bits(chunk)
        decoded_str = ""
        last_char_value = 0
        bit_index = 0

        if completed:
            bit_str = bit_str.rstrip("0")[:-1]

        while bit_index < len(bit_str):
            length_encoding, len_bits_len = decode_length_svf(3, bit_str[bit_index:])
            length_encoding = {4: 0,
                               1: 1,
                               2: 2,
                               3: 3}[length_encoding]

            bit_index += len_bits_len

            bundle = int(bit_str[bit_index])
            bit_index += 1

            bit_index += length_encoding * 8 if bit_index != 3 else 21
            char_bits = bit_str[bit_index:bit_index + bit_index]

            if bundle:
                char_value = decode_possible_negative_int(encode_positive_int(int(char_bits, 2))) + last_char_value
            else:
                char_value = decode_positive_int(encode_positive_int(int(char_bits, 2)))

            decoded_str += chr(char_value)
            last_char_value = char_value

        self._buffer += decoded_str
        if completed:
            self._completed += self._buffer
            self._buffer = ""

    def get_buffer(self) -> str:
        returns = self._buffer
        self._buffer = ""
        return returns

    def get_completed(self) -> str:
        returns = self._completed
        self._completed = ""
        return returns

    @staticmethod
    def encode(data: str, completed: bool = True) -> bytes:
        last_char_value = 0
        final_byte_arr = bytearray()
        i, bits_len = 0, 0
        for char in data:
            char_length, bundle = len(encode_positive_int(ord(char))), 0

            char_value = ord(char)
            char_bytes = encode_positive_int(char_value)

            bundle_num = encode_possible_negative_int(char_value - last_char_value)
            if len(bundle_num) < len(char_bytes):
                bundle = 1
                char_length = len(bundle_num)

            to_pack_len = {0: 4,
                           1: 1,
                           2: 2,
                           3: 3}[char_length]
            length_encoding, len_bits_len = encode_length_svf(3, to_pack_len)

            # Pack everything into the length_encoding
            meta_bytes = set_bits(length_encoding, len_bits_len, str(bundle))
            len_bits_len += 1
            if bundle:
                new_char_value = char_value - last_char_value
                char_bytes = encode_possible_negative_int(new_char_value)
                # meta_bytes = meta_bytes[
                #              :-(len(char_bytes) - len(encode_possible_negative_int(char_value - last_char_value)))]
                # print("BU")

            to_set_bytes = set_bits(meta_bytes, len_bits_len, nice_bits(char_bytes))
            final_byte_arr = set_bits(final_byte_arr, bits_len, nice_bits(to_set_bytes), return_bytearray=True,
                                      auto_expand=True)
            # if bundle:
            #     print(bits(final_byte_arr), bits(meta_bytes), len_bits_len, nice_bits(char_bytes))
            # final_byte_arr[i:i+len(to_set_bytes)] = to_set_bytes
            i += len(to_set_bytes)

            last_char_value = char_value
            bits_len += len_bits_len + ((len(char_bytes) * 8) if len(char_bytes) != 3 else 21)
            i += 1

        if completed:
            final_byte_arr = set_bits(final_byte_arr, bits_len, "1", return_bytearray=True, auto_expand=True)
        return bytes(final_byte_arr)


if __name__ == "__main__":
    un = Unien()
    encoded_uni_str = un.encode("👋Hell🆕o World„„🏃“")
    utf8_uni_str = "👋Hell🆕o World„„🏃“".encode("utf-8")
    print(f"{encoded_uni_str}/{utf8_uni_str} ({len(encoded_uni_str)}/{len(utf8_uni_str)})")
    normal_str = un.encode("Hello")
    print("Unien max supported code point: ", nice_number(int.from_bytes(b'\x1f\xff\xff')))

    print(bits(encoded_uni_str))
    un.add_chunk(encoded_uni_str)
    un.add_chunk(normal_str)
    print(un.get_completed())
