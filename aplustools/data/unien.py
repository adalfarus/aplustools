# Made by me :)

# Concept:
# Is stream and chunk based (so chunks but not limited by byte sizes)
# Firstly we have a length indicator:
# 0 -> 1 byte
# 10 -> 2 bytes
# 11 -> 3 bytes

# If the size is above 1 byte we have 1 bit to tell us if it's in relation to the last chunk
# 0 -> Off
# 1 -> On

# If it's on the next bit is if it's the start or end of a bundle
# 0 -> End of a bundle
# 1 -> Start of a bundle

# Then we have the rest of the data so it looks like this:

# 1 Encoded:
# 0 0000 0001
# ^ Size

# At the very end of the last chunk, it appends one 1 and then 0 to fill the last byte
# (Only if the communication can only transmit full bytes)

# or 10 000 that is a bundle end (If something is in-between a bundle start and a bundle end it is automatically
# in-relation, even if in-relation is turned off, so usually it's turned off and implied)
# 10 1 0 0010 0111 0001 0000
# ^^ ^ ^
# Size & in-relation & end of a bundle

from aplustools.data import (encode_possible_negative_int, encode_positive_int, nice_bits, bits, nice_number,
                             decode_possible_negative_int, set_bits, decode_positive_int)
import math


# From now on there is a 3 bit encoding that is just a regular number (1 trough 8)
# so 000 is 0, 001 is 1, 010 is 2, 011 is 3, 100 is 4, 101 is 5, 110 is 6, 111 is 7
# These correspond to bit lengths as followed:
# 0, 1, 2,  3,  4,  5,  6,  7
# 4, 6, 8, 10, 12, 16, 20, 24
#       ^      ^^          ^^


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
    byte_array = bytearray(math.ceil(((length * 8) + len(bit_list)) / 8))
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


class UnienEnAndDeCoder:
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
            length_encoding, len_bits_len = decode_length_svf(2, bit_str[bit_index:])
            bit_index += len_bits_len

            bundle = 0
            if len_bits_len > 1:
                bundle = int(bit_str[bit_index])
                bit_index += 2

            char_bits = bit_str[bit_index:bit_index + length_encoding * 8]
            bit_index += length_encoding * 8

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
            length_encoding, len_bits_len = encode_length_svf(2, char_length)
            char_value = ord(char)
            char_bytes = encode_positive_int(char_value)
            if len(encode_possible_negative_int(char_value - last_char_value)) < len(char_bytes):
                bundle = 1

            # Pack everything into the length_encoding
            meta_bytes = length_encoding
            if len_bits_len > 1:
                if bundle:
                    new_char_value = char_value - last_char_value
                    char_bytes = encode_possible_negative_int(new_char_value)
                    length_encoding, _ = encode_length_svf(2, len(char_bytes))
                    print("BU")
                meta_bytes = set_bits(length_encoding, len_bits_len, str(bundle) + "0")
                print(bits(meta_bytes))
                len_bits_len += 2
                if bundle:
                    meta_bytes = meta_bytes[:-(len(char_bytes) - len(encode_possible_negative_int(char_value - last_char_value)))]

            to_set_bytes = set_bits(meta_bytes, len_bits_len, nice_bits(char_bytes))
            final_byte_arr = set_bits(final_byte_arr, bits_len, nice_bits(to_set_bytes), return_bytearray=True,
                                      auto_expand=True)
            if bundle:
                print(bits(final_byte_arr), bits(meta_bytes), len_bits_len, nice_bits(char_bytes))
            # final_byte_arr[i:i+len(to_set_bytes)] = to_set_bytes
            i += len(to_set_bytes)

            last_char_value = char_value
            bits_len += len_bits_len + (len(char_bytes) * 8)
            i += 1

        if completed:
            final_byte_arr = set_bits(final_byte_arr, bits_len, "1", return_bytearray=True, auto_expand=True)
        return bytes(final_byte_arr)


if __name__ == "__main__":
    un = UnienEnAndDeCoder()
    encoded_uni_str = un.encode("👋Hell🆕o World„„🏃“")
    utf8_uni_str = "👋Hell🆕o World„„🏃“".encode("utf-8")
    print(f"{encoded_uni_str}/{utf8_uni_str} ({len(encoded_uni_str)}/{len(utf8_uni_str)})")
    normal_str = un.encode("Hello")
    print("Unien max supported code point: ", nice_number(int.from_bytes(b'\xff\xff\xff')))

    print(bits(encoded_uni_str))
    un.add_chunk(encoded_uni_str)
    un.add_chunk(normal_str)
    print(un.get_completed())
