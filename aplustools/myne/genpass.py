import os
from enum import Enum
import re
from typing import Union, Tuple, Literal


class CryptMode(Enum):
    ENCRYPT = 'e'
    DECRYPT = 'd'


class Crypt:
    @staticmethod
    def a1z26(plaintext: Union[str, list], mode: CryptMode = CryptMode.ENCRYPT) -> list:
        if mode == CryptMode.ENCRYPT:
            return [(ord(x.lower()) - 96) if x.isalpha() else int() for x in plaintext]
        elif mode == CryptMode.DECRYPT:
            l = []
            for x in plaintext:
                if (isinstance(x, int) and x != 0) or (isinstance(x, str) and x.isdigit() and int(x) != 0):
                    l.append(chr(int(x) + 96))
            return l

    @staticmethod
    def _rot155(plaintext: str, random_array: list = None) -> list:
        if random_array is None:
            random_array = [x + ord(os.urandom(1)) for x in range(len(plaintext))]
        if isinstance(plaintext, str):
            return [ord(plaintext[x]) - random_array[x] for x in range(len(plaintext))]
        else:
            return [plaintext[x] - random_array[x] for x in range(len(plaintext))]

    @staticmethod
    def _crack_case(ciphertext: list) -> list:
        result = []
        pattern = r"-?\d{1,3}"
        for part in ciphertext:
            matches = re.findall(pattern, part)
            result.extend(matches)
        return [int(match) for match in result]

    @staticmethod
    def _join_items_with_condition(items):
        result = []
        for x, y in zip(items[::2], items[1::2]):
            if ord(os.urandom(1)) % 2 == 0:
                result.append(f"{x}-{y}")
            else:
                result.append(f"{x}{y}")
        return result

    @classmethod
    def rot_away115(cls, plaintext: Union[str, list], random_array_overwrite: list = None,
                    mode: CryptMode = CryptMode.ENCRYPT) -> Tuple[list, list]:
        if isinstance(plaintext, str) and len(plaintext) % 2 != 0:
            plaintext += " "
        if random_array_overwrite is None:
            random_array_overwrite = []

        if mode == CryptMode.ENCRYPT:
            while True:
                random_array = random_array_overwrite or [x + ord(os.urandom(1)) for x in range(len(plaintext))]
                encrypted = cls._rot155(plaintext, random_array)
                double_encrypted = cls._join_items_with_condition(encrypted)
                rotten = cls._rot155(plaintext)
                double_rotten = cls._join_items_with_condition(rotten)
                encrypted2 = [int(x) for x in cls._crack_case(double_encrypted)]
                negated_random_array = [(x * -1) for x in random_array]
                plainnumbers = cls._rot155(encrypted2, negated_random_array)
                decrypted = [chr(x) if x > 0 and x < 126 else x for x in plainnumbers]
                decryptedtext = "".join([str(x) if not isinstance(x, str) else x for x in decrypted])
                if decryptedtext == plaintext:
                    return double_encrypted, random_array
        elif mode == CryptMode.DECRYPT:
            random_array = random_array_overwrite or [x + ord(os.urandom(1)) for x in range(len(plaintext))]
            encrypted_numbers = [int(x) for x in cls._crack_case(plaintext)]
            negated_random_array = [-x for x in random_array]
            plainnumbers = cls._rot155(encrypted_numbers, negated_random_array)
            decrypted = [chr(x) if 0 < x < 126 else x for x in plainnumbers]
            decrypted_text = ''.join([str(x) if not isinstance(x, str) else x for x in decrypted])
            return decrypted_text

    @staticmethod
    def caesar_ciper_adv(shift_value: int, plaintext: str,
                         char_string: str = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
                         maintain_case: Literal["output", "char_string", None] = None,
                         missing_char_error: bool = True) -> str:
        strict_case_char_string = maintain_case == "char_string"
        maintain_case_in_output = maintain_case == "output"
        if not strict_case_char_string:
            seen = set()
            lower_char_string = []
            for c in char_string:
                lower_c = c.lower()
                if lower_c not in seen:
                    seen.add(lower_c)
                    lower_char_string.append(lower_c)
            char_string = ''.join(lower_char_string)

        char_index_map = {char: idx for idx, char in enumerate(char_string)}
        char_string_length = len(char_string)
        result = []

        for char in plaintext:
            case = char.isupper() and maintain_case_in_output
            if not strict_case_char_string:
                char = char.lower()

            if char in char_index_map:
                char_index = char_index_map[char]
                new_pos = (char_index + shift_value) % char_string_length
                new_char = char_string[new_pos].upper() if case else char_string[new_pos]
                result.append(new_char)
            else:
                if missing_char_error:
                    raise ValueError(f"Char '{char}' not in char_string '{char_string}'.")
                print(f"Char '{char}' not in char_string '{char_string}'.")
                result += char
        return ''.join(result)


if __name__ == "__main__":
    encrypted, random_array = Crypt.rot_away115(("HELLO WORLD" * 10_000), [], CryptMode.ENCRYPT)
    print("decrypted", Crypt.rot_away115(encrypted, random_array, CryptMode.DECRYPT))
    encrypted = Crypt.caesar_ciper_adv(7000000000000, "HEL:", missing_char_error=False)
    print(Crypt.caesar_ciper_adv(-7, encrypted, missing_char_error=False))
