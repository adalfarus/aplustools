from cryptography.hazmat.primitives.ciphers import Cipher as _Cipher, algorithms as _algorithms, modes as _modes
from cryptography.hazmat.backends import default_backend as _default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC as _PBKDF2HMAC
from cryptography.hazmat.primitives import hashes as _hashes
from cryptography.hazmat.primitives import padding as _padding
from zxcvbn import zxcvbn as _zxcvbn

from ..data import beautify_json as _beautify_json, nice_number as _nice_number
from .rand import WeightedRandom as _WeightedRandom
from ..io.environment import strict as _strict

from typing import Union as _Union, Literal as _Literal, Optional as _Optional, Callable as _Callable
from importlib.resources import files as _files
from threading import Timer as _Timer
import unicodedata as _unicodedata
import secrets as _secrets
import string as _string
import base64 as _base64
import random as _random
import math as _math
import json as _json
import os as _os


class PasswordFilter:
    """Used to easily filter passwords based on a few simple concepts."""
    def __init__(self, exclude_chars: str = "", extra_chars: str = "", exclude_similar: bool = False):
        self.exclude_chars = exclude_chars
        self.extra_chars = extra_chars
        self.exclude_similar = exclude_similar
        self.extra_chars_dict = self._classify_extra_chars(extra_chars)

    def _classify_extra_chars(self, extra_chars: str) -> str:
        # Classify each extra char into the correct character set
        classified_chars = {
            "letters": "",
            "numbers": "",
            "punctuations": "",
            "unicode": ""
        }

        for char in extra_chars:
            if char in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ':
                classified_chars["letters"] += char
            elif char in '0123456789':
                classified_chars["numbers"] += char
            elif char in '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~':
                classified_chars["punctuations"] += char
            else:
                classified_chars["unicode"] += char

        return classified_chars

    def apply(self, character_set: str, set_name: _Literal["letters", "numbers", "punctuations", "unicode"]) -> str:
        """
        Applies the filter to a specific character set.

        :param character_set: The charset
        :param set_name: Which charset is being filtered
        :return: The filtered charset
        """
        if self.exclude_similar:
            similar_chars = "il1Lo0O"
            character_set = ''.join(ch for ch in character_set if ch not in similar_chars)
        if self.exclude_chars:
            character_set = ''.join(ch for ch in character_set if ch not in self.exclude_chars)
        character_set += self.extra_chars_dict[set_name]
        return character_set

    def filter_word(self, word: str) -> str:
        """
        Filters one word.

        :param word: The word to be filtered
        :return: The filtered word
        """
        # Filter the word according to the current settings
        filtered_word = ''.join(ch for ch in word if ch not in self.exclude_chars)
        if self.exclude_similar:
            similar_chars = "il1Lo0O"
            filtered_word = ''.join(ch for ch in filtered_word if ch not in similar_chars)
        return filtered_word

    def will_filter(self, char: str) -> bool:
        """
        Checks if a specific char would be filtered.

        :param char: The char to be checked
        :return: If the char would be filtered
        """
        return self.filter_word(char) == ""


class QuickGeneratePasswords:
    """Used to quickly generate a lot of passwords in minimal time"""
    _rng = _random
    characters = _string.ascii_letters + _string.digits
    debug = False

    @classmethod
    def _debug_print(cls, *args, **kwargs):
        if cls.debug:
            print(*args, **kwargs)

    @classmethod
    def quick_secure_password(cls, password: str, passes: int = 3, expand: bool = True) -> str:
        """
        Quicker version of SpecificPasswordGenerator.secure_password

        :param password: The password to be secured
        :param passes: How many iterations this should run for
        :param expand: If the password should be able to get larger
        :return: The secured password
        """
        cls._debug_print(f"Quick securing password: {password}")
        characters = _string.ascii_letters + _string.digits + _string.punctuation

        for _ in range(passes):
            if expand:
                # Add a random character
                password += cls._rng.choice(characters)
            else:
                rng = cls._rng.randint(0, len(password)-1)
                password = password[:rng] + cls._rng.choice(characters) + password[rng+1:]

            # Switch a random character's case
            pos = cls._rng.randint(0, len(password) - 1)
            char = password[pos]
            if char.islower():
                char = char.upper()
            elif char.isupper():
                char = char.lower()
            password = password[:pos] + char + password[pos+1:]

            # Add a random digit or punctuation
            pos = cls._rng.randint(0, len(password)-1)
            password = password[:pos] + cls._rng.choice(_string.digits + _string.punctuation) + password[(pos if expand else pos+1):]

        # Shuffle the resulting password to ensure randomness
        password_list = list(password)
        cls._rng.shuffle(password_list)
        password = ''.join(password_list)

        cls._debug_print(f"Quick secured password: {password}")
        return password

    @classmethod
    def generate_password(cls, length: int = 12, filter_: _Optional[PasswordFilter] = None) -> str:
        """
        Entirely random (uses the random module)

        :param length: The length of the password
        :param filter_: An optional password filter
        :return: The generated password
        """
        cls._debug_print(f"Generating password of length {length}")
        characters = _string.ascii_letters + _string.digits + _string.punctuation
        if filter_:
            characters = filter_.apply(characters, "letters")
            characters += filter_.apply(_string.digits, "numbers")
            characters += filter_.apply(_string.punctuation, "punctuations")
            cls._debug_print(f"Filtered characters: {characters}")
        password = ''.join(cls._rng.choice(characters) for _ in range(length))
        cls._debug_print(f"Generated password: {password}")
        return password

    @classmethod
    def generate_secure_password(cls, length: int = 12, filter_: _Optional[PasswordFilter] = None) -> str:
        """
        Entirely random (uses the secrets module)

        :param length: The length of the password
        :param filter_: An optional password filter
        :return: The generated password
        """
        cls._debug_print(f"Generating secure password of length {length}")
        characters = _string.ascii_letters + _string.digits + _string.punctuation
        if filter_:
            characters = filter_.apply(characters, "letters")
            characters += filter_.apply(_string.digits, "numbers")
            characters += filter_.apply(_string.punctuation, "punctuations")
            cls._debug_print(f"Filtered characters: {characters}")
        password = ''.join(_secrets.choice(characters) for _ in range(length))
        cls._debug_print(f"Generated secure password: {password}")
        return password

    @classmethod
    def generate_passphrase(cls, words: list, num_words: int = 4, filter_: _Optional[PasswordFilter] = None) -> str:
        """
        Passphrase, secure as it's very long

        :param words: Which words to use in the passphrase
        :param num_words: The number of words to be used
        :param filter_: An optional password filter
        :return: The generated password
        """
        cls._debug_print(f"Generating passphrase with {num_words} words")
        if filter_:
            words = list(filter(filter_.filter_word, words))
            cls._debug_print(f"Filtered words: {words[:10]}... (showing first 10)")
        passphrase = ' '.join(cls._rng.choice(words) for _ in range(num_words))
        cls._debug_print(f"Generated passphrase: {passphrase}")
        return passphrase

    @classmethod
    def generate_pattern_password(cls, pattern: str = "XXX-999-xxx", filter_: _Optional[PasswordFilter] = None) -> str:
        """
        A pattern password X for an uppercase letter, x for a lowercase letter and 9 for a number.
        All other characters are ignored and included as is in the final password

        :param pattern: The pattern to generate the password by
        :param filter_: An optional password filter
        :return: The generated password
        """
        cls._debug_print(f"Generating pattern password with pattern {pattern}")

        def _random_char(c):
            if c == 'X':
                chars = _string.ascii_uppercase
            elif c == 'x':
                chars = _string.ascii_lowercase
            elif c == '9':
                chars = _string.digits
            else:
                return c

            if filter_:
                chars = filter_.apply(chars, "letters" if c in 'Xx' else "numbers" if c == '9' else "punctuations")
                cls._debug_print(f"Filtered characters for '{c}': {chars}")

            return cls._rng.choice(chars)

        password = ''.join(_random_char(c) for c in pattern)
        cls._debug_print(f"Generated pattern password: {password}")
        return password

    @classmethod
    def generate_complex_password(cls, length: int = 12, filter_: _Optional[PasswordFilter] = None) -> str:
        """
        Entirely random, a complex password.

        :param length: The length of the password
        :param filter_: An optional password filter
        :return: The generated password
        """
        cls._debug_print(f"Generating complex password of length {length}")
        if length < 4:
            raise ValueError("Password length should be at least 4")

        all_characters = _string.ascii_letters + _string.digits + _string.punctuation
        if filter_:
            all_characters = filter_.apply(all_characters, "letters")
            all_characters += filter_.apply(_string.digits, "numbers")
            all_characters += filter_.apply(_string.punctuation, "punctuations")
            cls._debug_print(f"Filtered all characters: {all_characters}")

        password = [
            cls._rng.choice(filter_.apply(_string.ascii_uppercase, "letters")),
            cls._rng.choice(filter_.apply(_string.ascii_lowercase, "letters")),
            cls._rng.choice(filter_.apply(_string.digits, "numbers")),
            cls._rng.choice(filter_.apply(_string.punctuation, "punctuations"))
        ]

        remaining_chars = all_characters
        password += [cls._rng.choice(remaining_chars) for _ in range(length - 4)]
        cls._rng.shuffle(password)

        cls._debug_print(f"Generated complex password: {''.join(password)}")
        return ''.join(password)

    @classmethod
    def generate_mnemonic_password(cls, filter_: _Optional[PasswordFilter] = None) -> str:
        """
        A mnemonic password using adjectives and nouns

        :param filter_: An optional password filter
        :return:
        """
        cls._debug_print(f"Generating mnemonic password")
        adjectives = ["quick", "lazy", "sleepy", "noisy", "hungry"]
        nouns = ["fox", "dog", "cat", "mouse", "bear"]
        symbols = _string.punctuation
        numbers = _string.digits

        adj = cls._rng.choice(adjectives)
        noun = cls._rng.choice(nouns)
        symbol = cls._rng.choice(symbols)
        number = cls._rng.choice(numbers)

        if filter_:
            adj = filter_.filter_word(adj)
            noun = filter_.filter_word(noun)
            symbol = cls._rng.choice(filter_.apply(symbols, "punctuations"))
            number = cls._rng.choice(filter_.apply(numbers, "numbers"))

        password = f"{adj}{symbol}{noun}{number}"
        cls._debug_print(f"Generated mnemonic password: {password}")
        return password

    @classmethod
    def generate_ratio_based_password(cls, length: int = 12, letter_ratio: float = 0.4, digit_ratio: float = 0.3,
                                      symbol_ratio: float = 0.3, filter_: _Optional[PasswordFilter] = None) -> str:
        """
        Generate a simple ratio based password

        :param length: The length of the password
        :param letter_ratio: The ratio of letters in the final password
        :param digit_ratio: The ratio of digits in the final password
        :param symbol_ratio: The ratio of symbols in the final password
        :param filter_: An optional password filter
        :return: The generated password
        """
        cls._debug_print(f"Generating ratio-based password of length {length}")

        num_letters = int(length * letter_ratio)
        num_digits = int(length * digit_ratio)
        num_symbols = length - num_letters - num_digits

        characters = (
                (filter_.apply(_string.ascii_letters, "letters") if filter_ else _string.ascii_letters) * num_letters +
                (filter_.apply(_string.digits, "numbers") if filter_ else _string.digits) * num_digits +
                (filter_.apply(_string.punctuation, "punctuations") if filter_ else _string.punctuation) * num_symbols
        )

        password = ''.join(cls._rng.choice(characters) for _ in range(length))
        cls._debug_print(f"Generated ratio-based password: {password}")
        return password

    @classmethod
    def generate_sentence_based_password(cls, structure: str = "WwWn!") -> str:
        """
        A sentence based password, using a structure.
        W means a capitalized word, w means a lowercase word, n means a digit and ! means a symbol.

        :param structure:
        :return:
        """
        cls._debug_print(f"Generating sentence-based password with structure {structure}")

        words = ["quick", "brown", "fox", "jumps", "over", "lazy", "dog"]
        symbols = _string.punctuation
        digits = _string.digits

        password = []
        for char in structure:
            if char == 'W':
                password.append(cls._rng.choice(words).capitalize())
            elif char == 'w':
                password.append(cls._rng.choice(words))
            elif char == 'n':
                password.append(cls._rng.choice(digits))
            elif char == '!':
                password.append(cls._rng.choice(symbols))

        password_str = ''.join(password)
        cls._debug_print(f"Generated sentence-based password: {password_str}")
        return password_str

    @classmethod
    def generate_custom_sentence_based_password_v2(cls, sentence: str,
                                                   char_position: _Union[_Literal["random", "keep"], int] = 'random',
                                                   random_case: bool = False, extra_char: str = '', num_length: int = 0,
                                                   special_chars_length: int = 0):
        """
        A sentence based password, v2.

        :param sentence: The sentence to generate the password with, if this is not passed, a random sentence will be used.
        :param char_position: Which character in the word should be used in the password. You can also pass "random" for random and "keep" for keeping their position.
        :param random_case: If the case of characters in the final password should be randomized
        :param extra_char: Extra character part of the password
        :param num_length: The length of the numbers part of the password
        :param special_chars_length: The length of the punctuation part of the password
        :return: The generated password
        """
        words = sentence.split(' ')
        word_chars = []
        for word in words:
            if char_position == 'random':
                index = cls._rng.randint(0, len(word) - 1)
            elif char_position == 'keep':
                index = 0
            elif type(char_position) is int:
                index = min(char_position, len(word) - 1)
            else:
                return "Invalid char_position."
            char = word[index]
            if random_case:
                char = char.lower() if cls._rng.random() < 0.5 else char.upper()
            word_chars.append(char)
            cls._debug_print("Word characters after processing:", word_chars)
        num_string = ''.join(cls._rng.choices('0123456789', k=num_length))
        cls._debug_print("Numeric string after generation:", num_string)
        special_chars_string = ''.join(cls._rng.choices('!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~', k=special_chars_length))
        cls._debug_print("Special characters string after generation:", special_chars_string)
        password = ''.join(word_chars) + extra_char + num_string + special_chars_string
        cls._debug_print("Final password:", password)
        return password


class SpecificPasswordGenerator:
    """The random generators security can be adjusted, and all default arguments will result in a password
    that has an average worst case crack time of multiple years (Verified using zxcvbn)."""
    def __init__(self, random_generator: _Union[_Literal["weak", "average", "strong"], _WeightedRandom] = "strong",
                 debug: bool = False):
        if not isinstance(random_generator, _WeightedRandom):
            self._rng = _WeightedRandom({"weak": "random", "average": "np_random", "strong": "secrets"}[random_generator])
        else:
            self._rng = random_generator
        self.debug = debug
        self.words = []

    def _debug_print(self, *args, **kwargs):
        if self.debug:
            print(*args, **kwargs)

    def _add_unique_words(self, words):
        unique_words = set(self.words)  # Create a set of current words for fast membership testing
        for word in words:
            if word not in unique_words:
                self.words.append(word)
                unique_words.add(word)

    def load_def_dict(self):
        """
        Loads the default dictionary for random sentence generation.
        :return:
        """
        file_path = _files("aplustools.security.dicts").joinpath("def-dict.txt")
        with file_path.open("r") as f:
            self._add_unique_words([line.strip() for line in f])

    def load_google_10000_dict(self):
        """
        Loads google 10 000 dictionary for random sentence generation (uk & us without swears).
        :return:
        """
        file_path = _files("aplustools.security.dicts").joinpath("google-10000-dict.txt")
        with file_path.open("r") as f:
            self._add_unique_words([line.strip() for line in f])

    def load_scowl_dict(self, size: _Literal["50", "60", "70", "80", "95"] = "50"):
        """
        Loads one of scowl dicts, specified by their size.
        Larger sizes have all words of the smaller ones and more.
        :param size: The size of the dictionary to be loaded
        :type size: Literal["50", "60", "70", "80", "95"]
        :return:
        """
        file_path = _files("aplustools.security.dicts").joinpath(f"scowl-{size}-dict.txt")
        with file_path.open("r") as f:
            self._add_unique_words([line.strip() for line in f])

    def load_12_dicts(self):
        """
        Loads a selection of the 12 dicts which were deemed the most useful in sentence generation.
        :return:
        """
        dir_path = _files("aplustools.security.dicts").joinpath("12-dicts")
        for file in dir_path.iterdir():
            with file.open("r") as f:
                self._add_unique_words([line.strip() for line in f])

    def unload_dicts(self):
        """Unloads all currently loaded dictionaries."""
        self.words = []

    def basic_secure_password(self, password: str, passes: int = 3, expand: bool = True) -> str:
        """
        Makes the inputted password more secure by introducing slight changes each iteration.

        :param password: The password to be secured
        :param passes: How many iterations this should run for
        :param expand: If the password should be able to get larger
        :return: The secured password
        """
        self._debug_print(f"Securing password: {password}")
        characters = _string.ascii_letters + _string.digits + _string.punctuation

        for _ in range(passes):
            rnd = self._rng.randint(0, 3)

            match rnd:
                case 0:
                    if expand:
                        # Add a random character
                        password += self._rng.choice(characters)
                    else:
                        rng = self._rng.randint(0, len(password)-1)
                        password = password[:rng] + self._rng.choice(characters) + password[rng+1:]
                case 1:
                    # Switch a random character's case
                    pos = self._rng.randint(0, len(password) - 1)
                    char = password[pos]
                    if char.islower():
                        char = char.upper()
                    elif char.isupper():
                        char = char.lower()
                    password = password[:pos] + char + password[pos+1:]
                case 2:
                    # Add a random digit
                    pos = self._rng.randint(0, len(password)-1)
                    password = password[:pos] + self._rng.choice(_string.digits) + password[(pos if expand else pos+1):]
                case 3:
                    # Add a random punctuation
                    pos = self._rng.randint(0, len(password)-1)
                    password = password[:pos] + self._rng.choice(_string.punctuation) + password[(pos if expand else pos+1):]

        # Calculate the number of characters to switch
        length = len(password)
        percentage_to_switch = self._rng.choice([10, 20, 30])
        num_to_switch = max(2, (length * percentage_to_switch) // 100)

        # Switch around the selected percentage of characters
        password_list = list(password)
        for _ in range(num_to_switch // 2):
            idx1, idx2 = self._rng.sample(range(length), 2)
            password_list[idx1], password_list[idx2] = password_list[idx2], password_list[idx1]

        self._debug_print(f"Secured password: {password}")
        return password

    def dynamic_secure_password(self, password: str, passes: int = 3, expand: bool = True) -> str:
        """
        Makes the inputted password more secure by introducing slight changes each iteration.
        Dynamically changes less the longer the password, as they are already really secure.

        :param password: The password to be secured
        :param passes: How many iterations this should run for
        :param expand: If the password should be able to get larger
        :return: The secured password
        """
        self._debug_print(f"Securing password: {password}")
        characters = _string.ascii_letters + _string.digits + _string.punctuation

        for _ in range(passes):
            if expand:
                # Add a random character
                password += self._rng.choice(characters)
            else:
                rng = self._rng.randint(0, len(password)-1)
                password = password[:rng] + self._rng.choice(characters) + password[rng+1:]

            # Switch a random character's case
            pos = self._rng.randint(0, len(password) - 1)
            char = password[pos]
            if char.islower():
                char = char.upper()
            elif char.isupper():
                char = char.lower()
            password = password[:pos] + char + password[pos+1:]

            # Add a random digit
            pos = self._rng.randint(0, len(password)-1)
            password = password[:pos] + self._rng.choice(_string.digits) + password[(pos if expand else pos+1):]

            # Add a random punctuation
            pos = self._rng.randint(0, len(password)-1)
            password = password[:pos] + self._rng.choice(_string.punctuation) + password[(pos if expand else pos+1):]

        # Calculate the number of characters to switch
        length = len(password)
        percentage_to_switch = self._rng.choice([10, 20, 30])
        num_to_switch = max(2, (length * percentage_to_switch) // 100)

        # Switch around the selected percentage of characters
        password_list = list(password)
        for _ in range(num_to_switch // 2):
            idx1, idx2 = self._rng.sample(range(length), 2)
            password_list[idx1], password_list[idx2] = password_list[idx2], password_list[idx1]

        self._debug_print(f"Secured password: {password}")
        return password

    def static_secure_password(self, password: str, passes: int = 3, expand: bool = True) -> str:
        """
        Makes the inputted password more secure by introducing slight changes each iteration.

        :param password: The password to be secured
        :param passes: How many iterations this should run for
        :param expand: If the password should be able to get larger
        :return: The secured password
        """
        self._debug_print(f"Securing password: {password}")
        characters = _string.ascii_letters + _string.digits + _string.punctuation
        length = len(password)
        get_num = lambda: max(2, (length * self._rng.choice([10, 20, 30])) // 100)

        for _ in range(passes):
            for _ in range(get_num()):
                if expand:
                    # Add a random character
                    password += self._rng.choice(characters)
                else:
                    rng = self._rng.randint(0, len(password)-1)
                    password = password[:rng] + self._rng.choice(characters) + password[rng+1:]

                # Switch a random character's case
                pos = self._rng.randint(0, len(password) - 1)
                char = password[pos]
                if char.islower():
                    char = char.upper()
                elif char.isupper():
                    char = char.lower()
                password = password[:pos] + char + password[pos+1:]

                # Add a random digit
                pos = self._rng.randint(0, len(password)-1)
                password = password[:pos] + self._rng.choice(_string.digits) + password[(pos if expand else pos+1):]

                # Add a random punctuation
                pos = self._rng.randint(0, len(password)-1)
                password = password[:pos] + self._rng.choice(_string.punctuation) + password[(pos if expand else pos+1):]

        # Calculate the number of characters to switch
        num_to_switch = get_num()

        # Switch around the selected percentage of characters
        password_list = list(password)
        for _ in range(num_to_switch // 2):
            idx1, idx2 = self._rng.sample(range(length), 2)
            password_list[idx1], password_list[idx2] = password_list[idx2], password_list[idx1]

        self._debug_print(f"Secured password: {password}")
        return password

    def generate_secure_sentence(self, length: int = 4) -> str:
        """
        Generates a secure sentence using the currently loaded dictionaries,
        often used internally for secure sentence generation.
        [Choices is more secure than sample]

        :param length: The length of the sentence in words
        :return: The generated sentence
        """
        return ' '.join(self._rng.choices(self.words, length))

    def reduce_password(self, password: str, by: _Union[int, _Literal["all"]] = 0) -> str:
        """
        Reduces a given password using random binary operations to ensure a secure password.

        :param password: The password to be reduces
        :param by: How many characters each character should be joined with (0 means none and "all" means all).
        :return: The reduced password
        """
        by = by if by != "all" else len(password)
        result = []

        for chunk in (password[i:i+by+1] for i in range(0, len(password), by + 1)):
            if by == 0:
                chunk = chunk + chunk  # Duplicate the character to make a two-character chunk
            while len(chunk) < by + 1:
                chunk += chunk  # Repeat the chunk until it reaches the desired size
            chunk = chunk[:by + 1]  # Trim the chunk to the exact desired size

            rnd = self._rng.randint(0, 5)
            reduced_char = chunk[0]

            match rnd:
                case 0:
                    for char in chunk[1:]:
                        reduced_char = chr(ord(reduced_char) | ord(char))
                case 1:
                    for char in chunk[1:]:
                        reduced_char = chr(ord(reduced_char) & ord(char))
                case 2:
                    for char in chunk[1:]:
                        reduced_char = chr(ord(reduced_char) ^ ord(char))
                case 3:
                    reduced_char = chr(~ord(reduced_char) & 0xFF)  # NOT operation
                case 4:
                    for char in chunk[1:]:
                        reduced_char = chr((ord(reduced_char) << 1) & 0xFF)  # Left shift
                case 5:
                    for char in chunk[1:]:
                        reduced_char = chr(ord(reduced_char) >> 1)  # Right shift

            result.append(reduced_char)

        return ''.join(result)

    def generate_random_password(self, length: int = 18, filter_: _Optional[PasswordFilter] = None) -> str:
        """
        Entirely random

        :param length: The length of the password
        :param filter_: An optional password filter
        :return: The generated password
        """
        self._debug_print(f"Generating password of length {length}")
        characters = _string.ascii_letters + _string.digits + _string.punctuation
        if filter_:
            characters = filter_.apply(characters, "letters")
            characters += filter_.apply(_string.digits, "numbers")
            characters += filter_.apply(_string.punctuation, "punctuations")
            self._debug_print(f"Filtered characters: {characters}")
        password = ''.join(self._rng.choice(characters) for _ in range(length))
        self._debug_print(f"Generated password: {password}")
        return password

    def _generate_passphrase(self, words: list = None, num_words: int = 6, filter_: _Optional[PasswordFilter] = None
                             ) -> str:
        if words is None:
            words = ["These", "can", "be", "insecure", "as", "long", "as", "the", "password", "is", "long"]
        self._debug_print(f"Generating passphrase with {num_words} words")
        if filter_:
            words = list(filter(filter_.filter_word, words))
            self._debug_print(f"Filtered words: {words[:10]}... (showing first 10)")
        passphrase = ' '.join(self._rng.choice(words) for _ in range(num_words))
        self._debug_print(f"Generated passphrase: {passphrase}")
        return passphrase

    def generate_secure_passphrase(self, words: list = None, num_words: int = 6,
                                   filter_: _Optional[PasswordFilter] = None, _return_info=True) -> str:
        """
        Passphrase, secure as it's very long

        :param words: Which words to use in the passphrase
        :param num_words: The number of words to be used
        :param filter_: An optional password filter
        :param _return_info: If extra info about the password should be returned
        :return: The generated password
        """
        passphrase = self._generate_passphrase(words, num_words, filter_)
        secure_passphrase = self.dynamic_secure_password(passphrase, passes=1)
        return (secure_passphrase, passphrase) if _return_info else secure_passphrase

    def generate_pattern_password(self, pattern: str = "9/XxX-999xXx-99/XxX-999xXx-9",
                                  filter_: _Optional[PasswordFilter] = None) -> str:
        """
        A pattern password X for an uppercase letter, x for a lowercase letter and 9 for a number.
        All other characters are ignored and included as is in the final password

        :param pattern: The pattern to generate the password by
        :param filter_: An optional password filter
        :return: The generated password
        """
        self._debug_print(f"Generating pattern password with pattern {pattern}")
        if filter_:
            upper = filter_.apply(_string.ascii_uppercase, "letters")
            self._debug_print(f"Filtered characters for '{_string.ascii_uppercase}': {upper}")
            lower = filter_.apply(_string.ascii_lowercase, "letters")
            self._debug_print(f"Filtered characters for '{_string.ascii_lowercase}': {lower}")
            digits = filter_.apply(_string.digits, "numbers")
            self._debug_print(f"Filtered characters for '{_string.digits}': {digits}")
        else:
            upper = _string.ascii_uppercase
            lower = _string.ascii_lowercase
            digits = _string.digits

        def _random_char(c):
            if c == 'X':
                chars = upper
            elif c == 'x':
                chars = lower
            elif c == '9':
                chars = digits
            else:
                return c

            return self._rng.choice(chars)

        password = ''.join(_random_char(c) for c in pattern)
        self._debug_print(f"Generated pattern password: {password}")
        return password

    def generate_complex_pattern_password(self, pattern: str = '9nX9XWn9Ww9x9X-W!/999wnwwx!!',
                                          filter_: _Optional[PasswordFilter] = None) -> str:
        """
        A pattern password X for an uppercase letter, x for a lowercase letter, 9 for a number,
        W for a capitalized word, w for a lowercase word, n for a negative number and ! for a symbol.
        All other characters are ignored and included as is in the final password

        :param pattern: The pattern to generate the password by
        :param filter_: An optional password filter
        :return: The generated password
        """
        self._debug_print(f"Generating pattern password with pattern {pattern}")
        if filter_:
            upper = filter_.apply(_string.ascii_uppercase, "letters")
            self._debug_print(f"Filtered characters for '{_string.ascii_uppercase}': {upper}")
            lower = filter_.apply(_string.ascii_lowercase, "letters")
            self._debug_print(f"Filtered characters for '{_string.ascii_lowercase}': {lower}")
            digits = filter_.apply(_string.digits, "numbers")
            self._debug_print(f"Filtered characters for '{_string.digits}': {digits}")
            symbols = filter_.apply(_string.punctuation, "punctuations")
            self._debug_print(f"Filtered characters for '{_string.punctuation}': {digits}")
        else:
            upper = _string.ascii_uppercase
            lower = _string.ascii_lowercase
            digits = _string.digits
            symbols = _string.punctuation
        password = []

        for char in pattern:
            match char:
                case "X":
                    password.append(self._rng.choice(upper))
                case "x":
                    password.append(self._rng.choice(lower))
                case "9":
                    password.append(self._rng.choice(digits))
                case "W":
                    word = self._rng.choice(self.words)
                    if filter_:
                        word = filter_.filter_word(word)
                    password.append(word.title())
                case "w":
                    word = self._rng.choice(self.words)
                    if filter_:
                        word = filter_.filter_word(word)
                    password.append(word)
                case "n":
                    password.append("-" + self._rng.choice(digits))
                case "!":
                    password.append(self._rng.choice(symbols))
                case _:
                    password.append(char)

        return ''.join(password)

    def generate_complex_password(self, length: int = 18, filter_: _Optional[PasswordFilter] = None) -> str:
        """
        Entirely random, a complex password.

        :param length: The length of the password
        :param filter_: An optional password filter
        :return: The generated password
        """
        self._debug_print(f"Generating complex password of length {length}")
        if length < 4:
            raise ValueError("Password length should be at least 4")

        all_characters = _string.ascii_letters + _string.digits + _string.punctuation

        if filter_:
            upper_chars = filter_.apply(_string.ascii_uppercase, "letters")
            lower_chars = filter_.apply(_string.ascii_lowercase, "letters")
            digit_chars = filter_.apply(_string.digits, "numbers")
            punct_chars = filter_.apply(_string.punctuation, "punctuations")

            all_characters = filter_.apply(all_characters, "letters") + \
                             filter_.apply(_string.digits, "numbers") + \
                             filter_.apply(_string.punctuation, "punctuations")
        else:
            upper_chars = _string.ascii_uppercase
            lower_chars = _string.ascii_lowercase
            digit_chars = _string.digits
            punct_chars = _string.punctuation

        self._debug_print(f"Filtered all characters: {all_characters}")

        password = [
            self._rng.choice(upper_chars),
            self._rng.choice(lower_chars),
            self._rng.choice(digit_chars),
            self._rng.choice(punct_chars)
        ]

        remaining_chars = all_characters
        password += [self._rng.choice(remaining_chars) for _ in range(length - 4)]
        self._rng.shuffle(password)

        self._debug_print(f"Generated complex password: {''.join(password)}")
        return ''.join(password)

    def generate_mnemonic_password(self, length: int = 20, filter_: _Optional[PasswordFilter] = None,
                                   _return_info: bool = False) -> str:
        """
        A mnemonic password using adjectives and nouns

        :param length: The length of the password
        :param filter_: An optional password filter
        :param _return_info: If extra info about the password should be returned
        :return:
        """
        self._debug_print(f"Generating mnemonic password")
        adjectives = ["quick", "lazy", "sleepy", "noisy", "hungry", "brave", "clever", "fierce", "jolly", "kind"]
        nouns = ["fox", "dog", "cat", "mouse", "bear", "tiger", "lion", "wolf", "eagle", "shark"]
        symbols = _string.punctuation
        numbers = _string.digits

        adj = self._rng.choice(adjectives)
        noun = self._rng.choice(nouns)

        if filter_:
            adj = filter_.filter_word(adj)
            noun = filter_.filter_word(noun)

        # Randomize case
        adj = ''.join([char.upper() if self._rng.random() > 0.5 else char for char in adj])
        noun = ''.join([char.upper() if self._rng.random() > 0.5 else char for char in noun])

        # Calculate additional characters needed
        extra_length = max(0, length - (len(adj) + len(noun)))
        symbols_needed = extra_length // 2
        numbers_needed = extra_length - symbols_needed

        extra_symbols = ''.join(self._rng.choice(filter_.apply(symbols, "punctuations") if filter_ else symbols) for _ in range(symbols_needed))
        extra_numbers = ''.join(self._rng.choice(filter_.apply(numbers, "numbers") if filter_ else numbers) for _ in range(numbers_needed))

        password = f"{adj}{extra_symbols}{noun}{extra_numbers}"
        self._debug_print(f"Generated mnemonic password: {password}")
        return (password, adj, noun) if _return_info else password

    def generate_ratio_based_password_v3(self, length: int = 24, letters_ratio: float = 0.5, numbers_ratio: float = 0.3,
                                         punctuations_ratio: float = 0.2, unicode_ratio: float = 0.0,
                                         filter_: _Optional[PasswordFilter] = None) -> str:
        """
        Generate a ratio based password, version 3

        :param length: The length of the password
        :param letters_ratio: The ratio of letters in the final password
        :param numbers_ratio: The ratio of numbers in the final password
        :param punctuations_ratio: The ratio of punctuations in the final password
        :param unicode_ratio: The ratio of unicode in the final password
        :param filter_: An optional password filter
        :return:
        """
        character_sets = {
            "letters": 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ',
            "numbers": '0123456789',
            "punctuations": '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~',
            "unicode": unicode_ratio and   # Not generated, because it's 0 in most cases
            ''.join(chr(i) for i in range(0x110000) if _unicodedata.category(chr(i)).startswith('P'))
        }
        self._debug_print(f"Generated char_sets {character_sets}")

        if filter_:
            for key in character_sets:
                if character_sets[key]:
                    character_sets[key] = filter_.apply(character_sets[key], key)

        self._debug_print(f"Filtered char_sets {character_sets}")

        non_zero_lengths = {ratio_name: ratio for ratio_name, ratio in
                            {"letters": _math.ceil(length * letters_ratio),
                             "numbers": _math.ceil(length * numbers_ratio),
                             "punctuations": _math.ceil(length * punctuations_ratio),
                             "unicode": _math.ceil(length * unicode_ratio)}.items()
                            if ratio != 0 and len(character_sets[ratio_name]) != 0}
        remaining_length = length - sum(non_zero_lengths.values())

        self._debug_print(f"Generated non-zero lengths {non_zero_lengths}, remaining_length {remaining_length}")
        if remaining_length != 0:
            keys = list(non_zero_lengths.keys())
            for i in range(abs(remaining_length)):
                non_zero_lengths[keys[i % len(non_zero_lengths)]] += 1 if remaining_length > 0 else -1
        self._debug_print(f"After adjustment to chosen length, lengths {non_zero_lengths}")

        # Generate password characters
        password_characters = []
        for key, num_chars in non_zero_lengths.items():
            if character_sets[key]:
                password_characters.extend(self._rng.choices(character_sets[key], k=num_chars))

        self._debug_print(f"Generated password chars {password_characters}")

        # Shuffle the resulting password characters to ensure randomness
        self._rng.shuffle(password_characters)

        self._debug_print(f"Final password chars {password_characters}")

        return ''.join(password_characters)

    def generate_words_based_password_v3(self, sentence: _Optional[str] = None, shuffle_words: bool = True,
                                         shuffle_characters: bool = True, repeat_words: bool = False,
                                         filter_: PasswordFilter = None, _return_info: bool = False) -> str:
        """
        Generate a words based password, v3.

        :param sentence: The sentence to generate the password with, if this is not passed, a random sentence will be used.
        :param shuffle_words: If the order of the words should change in the final password
        :param shuffle_characters: If the order of the characters in each word should change
        :param repeat_words: If words should be able to be repeated
        :param filter_: An optional password filter
        :param _return_info: If extra info about the password should be returned
        :return: The generated password
        """
        if sentence is None:
            sentence = self.generate_secure_sentence(length=5)
        words = sentence.split(' ')

        self._debug_print("Words", words)
        if shuffle_words:
            self._rng.shuffle(words)
            self._debug_print("Words after shuffling", words)

        if shuffle_characters:
            words = [''.join(self._rng.sample(word, len(word))) for word in words]
            self._debug_print("Words after character shuffling", words)

        if filter_:
            words = [filter_.filter_word(word) for word in words]

        if repeat_words:
            length = len(words)
            password = ''.join(self._rng.choice(words) for _ in range(length))
        else:
            password = ''.join(words)

        self._debug_print("Generated password", password)
        return (password, sentence) if _return_info else password

    def generate_sentence_based_password_v3(self, sentence: _Optional[str] = None,
                                            char_position: _Union[_Literal["random", "keep"], int] = 'keep',
                                            random_case: bool = True, extra_char: str = '/', num_length: int = 6,
                                            special_chars_length: int = 4,
                                            password_format: str = "{words}{special}{extra}{numbers}",
                                            filter_: PasswordFilter = None, _return_info: bool = False) -> str:
        """
        A sentence based password, v3.

        :param sentence: The sentence to generate the password with, if this is not passed, a random sentence will be used.
        :param char_position: Which character in the word should be used in the password. You can also pass "random" for random and "keep" for keeping their position.
        :param random_case: If the case of characters in the final password should be randomized
        :param extra_char: Extra character part of the password
        :param num_length: The length of the numbers part of the password
        :param special_chars_length: The length of the punctuation part of the password
        :param password_format: How to structure the different parts of the password into one.
        :param filter_: An optional password filter
        :param _return_info: If extra info about the password should be returned
        :return: The generated password
        """
        if sentence is None:
            sentence = self.generate_secure_sentence(length=8)
        words = sentence.split(' ')
        word_chars = []
        for word in words:
            if not word:
                continue

            if char_position == 'random':
                indices = list(range(len(word)))
                self._rng.shuffle(indices)
            elif char_position == 'keep':
                indices = [x for x in range(len(word))]
            elif isinstance(char_position, int):
                indices = [min(char_position, len(word) - 1)]
            else:
                return "Invalid char_position."

            char_selected = False
            for index in indices:
                char = word[index]
                if random_case:
                    char = char.lower() if self._rng.random() < 0.5 else char.upper()
                if filter_ is None or not filter_.will_filter(char):
                    word_chars.append(char)
                    self._debug_print("Word characters after processing:", word_chars)
                    char_selected = True
                    break

            if not char_selected:
                self._debug_print("No valid character found for word:", word)

        word_string = ''.join(word_chars)
        num_string = ''.join(self._rng.choices('0123456789', k=num_length))
        self._debug_print("Numeric string after generation:", num_string)
        special_chars_string = ''.join(self._rng.choices('!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~', k=special_chars_length))
        self._debug_print("Special characters string after generation:", special_chars_string)

        password = password_format.format(words=word_string, extra=extra_char, numbers=num_string,
                                          special=special_chars_string)
        self._debug_print("Final password:", password)

        return (password, sentence) if _return_info else password


class SecurePasswordGenerator:
    """
    Generates an always secure password that takes at least over one year to crack in the worst case
    (Verified by zxcvbn).
    This is also guaranteed if some of your passwords are already compromised as the password generation pattern is also
    entirely random.

    The number of unique words for random sentence generation grows with the security settings (All duplicates are
    filtered out):
    - Weak: 10.027 words (random module for random number generation)
    - Average: 105.705 words (numpy.random module for random number generation)
    - Strong: 223.242 words (secrets module for random number generation)
    - Super Strong: 400.172 words (secrets module for random number generation)
    """

    def __init__(self, security: _Literal["weak", "average", "strong", "super_strong"]):
        self._rng = _WeightedRandom({"weak": "random", "average": "np_random", "strong": "secrets",
                                     "super_strong": "secrets"}[security])
        self._gen = SpecificPasswordGenerator(self._rng)

        match security:
            case "weak":
                self._gen.load_def_dict()
                self._gen.load_google_10000_dict()
            case "average":
                self._gen.load_def_dict()
                self._gen.load_google_10000_dict()
                self._gen.load_scowl_dict()
            case "strong":
                self._gen.load_def_dict()
                self._gen.load_google_10000_dict()
                self._gen.load_scowl_dict(size="70")
                self._gen.load_12_dicts()
            case "super_strong":
                self._gen.load_def_dict()
                self._gen.load_google_10000_dict()
                self._gen.load_scowl_dict(size="80")
                self._gen.load_12_dicts()
        print(f"Loaded {_nice_number(len(self._gen.words))} unique words")

    def generate_secure_password(self, return_worst_case: bool = True, predetermined: _Optional[
                                                                                      _Literal["random", "passphrase",
                                                                                               "pattern", "complex",
                                                                                               "mnemonic", "ratio",
                                                                                               "words", "sentence",
                                                                                               "complex_pattern"
                                                                                      ]] = None) -> dict:
        """
        Generates always secure, always changing passwords that are designed to be human readable.
        The target worst time to crack is one century for each generated password.

        :param return_worst_case: Return the worst case estimate by zxcvbn
        :param predetermined: Choose which type of password you want to generate, this will make it 8 times easier to crack your password.
        :return:
        """
        rnd = int(self._rng.exponential(0, 8, 0.9)) if predetermined is None else \
            {
                "mnemonic": 0,
                "passphrase": 1,
                "pattern": 2,
                "complex_pattern": 3,
                "sentence": 4,
                "words": 5,
                "random": 6,
                "complex": 7,
                "ratio": 8
            }[predetermined]
        result = {"extra_info": "", "password": "", "worst_case": ""}

        match rnd:
            case 0:
                pw, adj, noun = self._gen.generate_mnemonic_password(_return_info=True)
                result = {"extra_info": f"A mnemonic password using the adj '{adj}' and the noun '{noun}'.",
                          "password": pw}
            case 1:
                pw, sentence = self._gen.generate_secure_passphrase(self._gen.words, _return_info=True)
                result = {"extra_info": f"Passphrase, secure as it's very long, using the sentence '{sentence}'", "password": pw}
            case 2:
                pattern = ''.join(self._rng.choices("/XXXxxx-999", 28))
                pw = self._gen.generate_pattern_password(pattern)
                result = {"extra_info": f"A pattern password with the pattern '{pattern}'.", "password": pw}
            case 3:
                pattern = ''.join(self._rng.choices("/XXXxxx-999nnWw!!!", 28))
                pw = self._gen.generate_complex_pattern_password(pattern)
                result = {"extra_info": f"A complex pattern password with the pattern '{pattern}'.", "password": pw}
            case 4:
                spec_char = self._rng.choice('!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~')
                pattern = ''.join(self._rng.sample(["{words}", "{special}", "{extra}", "{numbers}"], 4))
                pw, sentence = self._gen.generate_sentence_based_password_v3(extra_char=spec_char,
                                                                             password_format=pattern, _return_info=True)
                result = {"extra_info": f"A sentence based password using the sentence '{sentence}' "
                                        f"and the pattern '{pattern}'.", "password": pw}
            case 5:
                pw, sentence = self._gen.generate_words_based_password_v3(_return_info=True)
                result = {"extra_info": f"A words based password using the sentence '{sentence}_.", "password": pw}
            case 6:
                pw = self._gen.generate_random_password()
                result = {"extra_info": "Entirely random", "password": pw}
            case 7:
                pw = self._gen.generate_complex_password()
                result = {"extra_info": "Entirely random, a complex password.", "password": pw}
            case 8:
                pw = self._gen.generate_ratio_based_password_v3()
                result = {"extra_info": "Entirely random, a ratio based password.", "password": pw}
            case _:
                raise ValueError()

        if return_worst_case:
            result["worst_case"] = _zxcvbn(result["password"])["crack_times_display"]["offline_fast_hashing_1e10_per_second"]

        return result


def reducer_3(input_str: str, ord_range: range):
    """Around 3.34 times faster than reducer_2 (7ms vs 18ms)"""
    chars = tuple(chr(x) for x in ord_range)
    return ''.join(chars[ord(b) % len(chars)] for b in input_str if ord(b) not in ord_range)


def quick_reducer_3(input_str: str, ord_range: range):
    """Around 3.6 times faster than reducer_2 (5ms vs 18ms)"""
    chars = tuple(chr(x) for x in ord_range)
    return ''.join(chars[ord(b) % len(chars)] for b in input_str)


def big_reducer_3(input_str: str, ord_ranges: list[range], debug: bool = False):
    """Around twice as fast as big_reducer_2 (43ms vs 24ms)"""
    def _debug_print(*args, **kwargs):
        if debug:
            print(*args, **kwargs)

    def _within_ranges(ord_val, ranges):
        for minimum, maximum in ranges.values():
            _debug_print(f"Min: {minimum}, Max: {maximum}, Char: {chr(ord_val)}({ord_val})")
            if minimum <= ord_val <= maximum:
                return True
        return False

    def _adjust_to_nearest_range(ord_val, ranges: dict):
        def _nearest_int(target, int1, int2):
            diff1 = abs(target - int1)
            diff2 = abs(target - int2)

            if diff1 < diff2:
                return int1
            elif diff2 < diff1:
                return int2
            else:
                # If both are equal, just use the one that better fits the jump_size
                diff1_jump = diff1 / 1
                diff2_jump = diff2 / 1
                return int1 if diff1_jump < diff2_jump else int2

        range_items: list[tuple[range, tuple[int, int]]] = list(ranges.items())

        for i, (range1, _) in enumerate(range_items):
            range2 = range_items[i + 1][0] if i != len(range_items) - 1 else range(range1.stop, range1.stop)
            end, start = range1.stop, range2.start

            _debug_print(end, "<", ord_val, "<", start)

            if end < ord_val < start:
                target = _nearest_int(ord_val, end, start)
                _debug_print("Target: ", target)
                if target == end:
                    num = end - range1.start
                    if num <= 0:  # Handle empty or single-character range
                        ord_val = range1.start
                    else:
                        ord_val = range1.start + (ord_val % num)
                else:
                    num = range2.stop - start
                    if num <= 0:  # Handle empty or single-character range
                        ord_val = range2.start
                    else:
                        ord_val = range2.start + (ord_val % num)
                break
            elif ord_val < range1.start and i == 0:
                num = end - range1.start
                if num <= 0:  # Handle empty or single-character range
                    ord_val = range1.start
                else:
                    ord_val = range1.start + (ord_val % num)
                break
            elif ord_val > range2.stop and i == len(ranges) - 1:
                num = range2.stop - start
                if num <= 0:  # Handle empty or single-character range
                    ord_val = range2.start
                else:
                    ord_val = range2.start + (ord_val % num)
                break

        else:
            _debug_print(f"Recalculating char {chr(ord_val)}, {ord_val}")

        return ord_val

    range_tuples = [(r, [r.start, r.stop]) for r in ord_ranges]
    sorted_range_tuples = sorted(range_tuples, key=lambda r: r[0].start)
    ranges = {k: v for k, v in sorted_range_tuples}
    _debug_print(ranges)

    output = ""
    for char in input_str:
        ord_i = ord(char)
        _debug_print(f"Char {repr(char)} -> Ord {ord_i}")

        if not _within_ranges(ord_i, ranges):
            ord_i = _adjust_to_nearest_range(ord_i, ranges)
            char = chr(ord_i)
            _debug_print(f"New char {repr(char)} -> Ord {ord_i}")

        output += char
    return output


def quick_big_reducer_3(input_str: str, ord_ranges: list[range]):
    """Around 10.75 times faster than big_reducer_2 (43ms vs 4ms) and
    around 6 times faster than big_reducer_3 (24ms vs 4ms)"""
    chars = [chr(c) for rng in ord_ranges for c in rng]
    return ''.join(chars[ord(b) % len(chars)] for b in input_str)


@_strict(mark_class_as_cover=False)  # For security purposes
class PasswordReGenerator:
    """Create a secure password from a weak one plus an identifier like a website name. This is made possible by used
    an encrypted seed file in combination with the PBKDF2HMAC algorithm (using 100_000 iterations and sha 256)."""
    def __init__(self, key: bytes, seed_file_or_seed: str | bytes = "seed_file.enc", debug: bool = False,
                 _got_seed: bool = False):
        self._key = key
        self._seed_file = seed_file_or_seed
        self._debug = debug

        if not _got_seed:
            self._load_or_create_seed_file()
        else:
            self._seed = self._seed_file
            self._seed_file = None

    @classmethod
    def load_from_file(cls, file_path: str) -> "PasswordReGenerator":
        """Use a default file as the seed (hashed)."""
        from aplustools.security.crypto import CryptUtils
        try:
            with open(file_path, "r") as f:
                contents = f.read()
        except IOError:
            with open(file_path, "rb") as f:
                contents = f.read()
        seed = CryptUtils.pbkdf2(contents, CryptUtils.generate_hash(file_path, "strong").encode(), 32, 1_000_000)
        return cls(CryptUtils.generate_hash(_os.path.basename(file_path), "strong").encode(), seed, False, True)

    @staticmethod
    def generate_suitable_password() -> bytes:
        """
        Generates a suitable password for encryption
        :return: The suitable password
        :rtype: bytes
        """
        return _os.urandom(32)

    def _load_or_create_seed_file(self):
        if _os.path.exists(self._seed_file):
            self._load_seed_file()
        else:
            self._create_seed_file()

    def _load_seed_file(self):
        with open(self._seed_file, 'rb') as f:
            encrypted_seed = f.read()

        # Decrypt the seed
        iv = encrypted_seed[:16]
        cipher = _Cipher(_algorithms.AES(self._key), _modes.CBC(iv), backend=_default_backend())
        decryptor = cipher.decryptor()
        padded_seed = decryptor.update(encrypted_seed[16:]) + decryptor.finalize()

        # Unpad the seed
        unpadder = _padding.PKCS7(_algorithms.AES.block_size).unpadder()
        self._seed = unpadder.update(padded_seed) + unpadder.finalize()

    def _create_seed_file(self):
        self._seed = _os.urandom(32)

        # Encrypt the seed
        iv = _os.urandom(16)
        cipher = _Cipher(_algorithms.AES(self._key), _modes.CBC(iv), backend=_default_backend())
        encryptor = cipher.encryptor()

        # Pad the seed
        padder = _padding.PKCS7(_algorithms.AES.block_size).padder()
        padded_seed = padder.update(self._seed) + padder.finalize()

        encrypted_seed = iv + encryptor.update(padded_seed) + encryptor.finalize()

        with open(self._seed_file, 'wb') as f:
            f.write(encrypted_seed)

    def generate_password(self, identifier: str, simple_password: str, length: int = 64,
                          charset: _Literal["hex", "base64", "alphanumeric", "ascii"] = "hex") -> str:
        """
        "Generate" a new password from the hash of an identifier and a simple password to the given length and charset.

        :param identifier: A unique identifier for the password, ideally something you can remember easily.
        :type identifier: str
        :param simple_password: A simple password
        :type simple_password: str
        :param length: The length of the new password
        :type length: int
        :param charset: The charset to which the new password should be collapsed to
        :type charset: Literal["hex", "base64", "alphanumeric", "ascii"]
        :return: The generated password
        :rtype: str
        """
        salt = self._seed + identifier.encode() + simple_password.encode()
        kdf = _PBKDF2HMAC(
            algorithm=_hashes.SHA256(),
            length=length,
            salt=salt,
            iterations=100000,
            backend=_default_backend()
        )
        password = kdf.derive(self._key)
        return self._format_password(password, length, charset.lower())

    def _format_password(self, password: bytes, length: int, charset: _Literal["hex", "base64", "alphanumeric", "ascii"]
                         ) -> str:
        # Convert to a readable password
        match charset:
            case "hex":
                return password.hex()[:length]
            case "base64":
                return _base64.urlsafe_b64encode(password).decode('utf-8')[:length]
            case "alphanumeric":
                chars = _string.ascii_letters + _string.digits
                return ''.join(chars[b % len(chars)] for b in password)[:length]
            case "ascii":
                chars = _string.printable[:94]  # Exclude non-printable characters
                return ''.join(chars[b % len(chars)] for b in password)[:length]
            case _:
                raise ValueError(f"Unsupported charset: {charset}")


@_strict(mark_class_as_cover=False)  # For security purposes
class SecurePasswordManager:
    """Securely stores passwords and gives various options to generate them too."""
    def __init__(self, key: bytes, buffer_timeout: int = 30, debug: bool = False):
        # The key should be securely generated and stored.
        self._key = key
        self._storage: dict[str, dict[str, bytes]] = {}
        self._quick_access_buffer = {}
        self._buffer_timeout = buffer_timeout  # Time in seconds before clearing the buffer
        self.debug = debug

    @staticmethod
    def generate_suitable_password() -> bytes:
        """
        Generates a suitable password for encryption
        :return: The suitable password
        :rtype: bytes
        """
        return _secrets.token_bytes(32)

    def store_password(self, identifier: str, password: str):
        """
        Adds a password for a specific account and username.

        :param identifier: The identifier of the password
        :type identifier: str
        :param password: The password of the identifier
        :type password: str
        :return:
        """
        iv = _secrets.token_bytes(16)
        cipher = _Cipher(_algorithms.AES(self._key), _modes.CBC(iv), backend=_default_backend())
        encryptor = cipher.encryptor()

        # Padding for AES block size
        padded_password = password + ' ' * (16 - len(password) % 16)
        ciphertext = encryptor.update(padded_password.encode()) + encryptor.finalize()

        self._storage[identifier] = {'password': ciphertext, 'iv': iv}

    def retrieve_password(self, identifier: str) -> str:
        """
        Get the password of a given account.

        :param identifier: The identifier of the password
        :type identifier: str
        :return: The password of the given identifier
        :rtype: str
        """
        # Check if password is in quick access buffer
        if identifier in self._quick_access_buffer:
            return self._quick_access_buffer[identifier]

        data = self._storage.get(identifier)
        if data:
            cipher = _Cipher(_algorithms.AES(self._key), _modes.CBC(data['iv']), backend=_default_backend())
            decryptor = cipher.decryptor()

            decrypted_password = decryptor.update(data['password']) + decryptor.finalize()
            self._add_to_buffer(identifier, decrypted_password.rstrip().decode())
            return decrypted_password.rstrip().decode()  # Removing padding
        else:
            raise KeyError("Password not found")

    def _add_to_buffer(self, identifier, password):
        self._quick_access_buffer[identifier] = password
        timer = _Timer(self._buffer_timeout, self._remove_from_buffer, [identifier])
        timer.start()

    def _remove_from_buffer(self, identifier):
        if identifier in self._quick_access_buffer:
            del self._quick_access_buffer[identifier]

    def dump_encrypted_passwords(self, file_path):
        """
        Dumps all encrypted passwords to the specified filepath.

        :param file_path: The specified filepath
        :type file_path: str
        :return:
        """
        with open(file_path, 'wb') as file:
            data = {
                "storage": self._storage
            }
            file.write(_json.dumps(data).encode())

    def load_encrypted_passwords(self, file_path):
        """
        Loads a dumped file into the current instance.
        The passwords from the loaded file will overwrite all duplicate identifiers.
        
        :param file_path: 
        :return: 
        """
        with open(file_path, 'rb') as file:
            data = _json.loads(file.read().decode())
            self._storage.update(data["storage"])


class PasswordCrackEstimator:
    """Using zxcvbn to deliver an easy result as it's a hard to find and a bit confusing package for beginners."""
    long_presets = [
        (tuple(), {'length': 12}),
        (tuple(), {'length': 14}),
        (tuple(), {'length': 16}),
        (tuple(), {'length': 18}),
        (tuple(), {'length': 20}),
        (tuple(), {'length': 22}),
        (tuple(), {'length': 24}),
        (tuple(), {'length': 26})
    ]
    short_presets = [
        (tuple(), {'length': 1}),
        (tuple(), {'length': 2}),
        (tuple(), {'length': 3}),
        (tuple(), {'length': 4}),
        (tuple(), {'length': 5}),
        (tuple(), {'length': 6}),
        (tuple(), {'length': 7}),
        (tuple(), {'length': 8})
    ]

    @staticmethod
    def estimate_time_to_crack(password: str) -> tuple[str, tuple[str]]:
        """
        Calculates the different times it takes to crack a given password and returns it as tuple[password, tuple[times]].

        Calculates the different times it takes to crack a given password using zxcvbn["crack_times_display"] and returns it as tuple[password, tuple[times]].

        :param password:
        :type password: str
        :return: A tuple containing the password and the different times it takes to crack.
        :rtype: tuple[str, tuple[str]]
        """
        result = _zxcvbn(password)
        return result["password"], result["crack_times_display"]

    @staticmethod
    def tell_pass_sec(password: str) -> tuple[str, str]:
        """
        Calculates the average time to crack of a given password and returns it as tuple[password, average time to crack].

        Calculates the average time to crack of a given password using zxcvbn["crack_times_seconds"] and returns it as tuple[password, average time to crack].

        :param password:
        :type password: str
        :return: A tuple containing the password and the average time to crack.
        :rtype: tuple[str, str]
        """
        result = _zxcvbn(password)
        return result["password"], result["crack_times_seconds"]

    @staticmethod
    def tell_worst_case(password: str) -> tuple[str, str]:
        """
        Calculates the worst case of a given password and returns it as tuple[password, worst_case].

        Calculates the worst case of a given password using zxcvbn["crack_times_display"]["offline_fast_hashing_1e10_per_second"] and returns it as tuple[password, worst_case].

        :param password:
        :type password: str
        :return: A tuple containing the password and the worst case formatted as a string.
        :rtype: tuple[str, str]
        """
        result = _zxcvbn(password)
        return result["password"], "Worst Case: " + result["crack_times_display"][
            "offline_fast_hashing_1e10_per_second"]

    @staticmethod
    def zxcvbn(password: str, user_inputs: list[str] = None) -> str:
        """
        A basic wrapper around the default zxcvbn function that simply beautifies the returned dictionary in a json style.

        :param password: The password to test.
        :type password: str
        :param user_inputs: Any personal user data
        :type user_inputs: list[str]
        :return: A beautified dictionary of information about the passwords crack security.
        :rtype: str
        """
        if user_inputs is None:
            user_inputs = []
        return _beautify_json(_zxcvbn(password, user_inputs))

    @classmethod
    def _test_password_strength(cls, function: _Callable, preset: tuple[tuple, dict], num_passwords: int = 1000
                                ) -> tuple[str, float]:
        worst_times = []

        password = None
        for _ in range(max(1, num_passwords)):
            password = function(*preset[0], **preset[1])
            security = cls.tell_pass_sec(password)
            worst_time = security[1]['offline_fast_hashing_1e10_per_second']
            worst_times.append(float(worst_time))

        average_worst_time = sum(worst_times) / len(worst_times)
        return password, average_worst_time / (60 * 60 * 24 * 365.25)  # Convert seconds to years

    @classmethod
    def find_best_preset(cls, function: _Callable, presets: tuple[tuple[tuple, dict]]):
        """
        Finds the best preset (the average worst case time is above 2 years) of a given function and presets tuple).
        This function doesn't return anything, it prints out all results.

        Finds the best preset (the average worst case time is above 2 years) of a given function and preset tuple[tuple[tuple[args], dict[kwargs]]].
        This function doesn't return anything, it prints out all results.

        :param function: The function to test and find the best preset for.
        :type function: Callable
        :param presets: All presets to test (should be sorted from small -> big as it stops as soon as it finds a suitable one)
        :type presets: tuple[tuple[tuple, dict]]
        :return:
        """
        for preset in presets:
            sec, average_worst_case_years = cls._test_password_strength(function, preset)
            print(f"Preset {preset} average worst-case time to crack: {average_worst_case_years:.2f} years [{sec}]")
            if average_worst_case_years >= 2:  # Adjust the threshold as needed
                print(
                    f"Preset {preset} meets the security criteria with an average worst-case time to crack of {average_worst_case_years:.2f} years.")
                break


class PasswordTypeHelper:
    """
    Types out a password in any of the defined layout. If it isn't able to type out a specific character, it will mark
    it with [UT], which means UnicodeTyper, a program I develop to be able to type unicode on a default ascii keyboard.
    """
    layouts = {
        "us": {
            "a": "a", "b": "b", "c": "c", "d": "d", "e": "e", "f": "f",
            "g": "g", "h": "h", "i": "i", "j": "j", "k": "k", "l": "l",
            "m": "m", "n": "n", "o": "o", "p": "p", "q": "q", "r": "r",
            "s": "s", "t": "t", "u": "u", "v": "v", "w": "w", "x": "x",
            "y": "y", "z": "z", "1": "1", "2": "2", "3": "3", "4": "4",
            "5": "5", "6": "6", "7": "7", "8": "8", "9": "9", "0": "0",
            " ": "space", ",": "comma", ".": "period", ";": "semicolon",
            "'": "quote", "-": "minus", "=": "equal", "[": "left_bracket",
            "]": "right_bracket", "\\": "backslash", "/": "slash",
            "`": "grave"
        },
        "de": {
            "a": "a", "b": "b", "c": "c", "d": "d", "e": "e", "f": "f",
            "g": "g", "h": "h", "i": "i", "j": "j", "k": "k", "l": "l",
            "m": "m", "n": "n", "o": "o", "p": "p", "q": "q", "r": "r",
            "s": "s", "t": "t", "u": "u", "v": "v", "w": "w", "x": "x",
            "y": "y", "z": "z", "1": "1", "2": "2", "3": "3", "4": "4",
            "5": "5", "6": "6", "7": "7", "8": "8", "9": "9", "0": "0",
            " ": "space", ",": "comma", ".": "period", ";": "semicolon",
            "'": "quote", "-": "minus", "=": "equal", "[": "left_bracket",
            "]": "right_bracket", "\\": "backslash", "/": "slash",
            "`": "grave", "ü": "ue", "ä": "ae", "ö": "oe"
        }
        # Add more layouts as needed
    }

    # Define the shift mappings for special characters
    shift_mappings = {
        "us": {
            "!": "1", "@": "2", "#": "3", "$": "4", "%": "5", "^": "6",
            "&": "7", "*": "8", "(": "9", ")": "0", "_": "-", "+": "=",
            "{": "[", "}": "]", ":": ";", "\"": "'", "<": ",", ">": ".",
            "?": "/", "|": "\\"
        },
        "de": {
            "!": "1", "\"": "2", "§": "3", "$": "4", "%": "5", "&": "6",
            "/": "7", "(": "8", ")": "9", "=": "0", "?": "ß", "*": "+",
            "`": "´", "²": "2", "³": "3", "{": "[", "}": "]", "\\": "\\",
            "'": "#", "<": "<", ">": ">", "|": "|"
        }
        # Add more mappings as needed
    }

    def __init__(self, layout: str):
        self._current_layout = None
        self.set_layout(layout)

    def get_layout(self) -> str:
        """
        Get the current keyboard layout/mapping.

        :return:
        """
        return self._current_layout

    def set_layout(self, layout: str):
        """
        Set the current keyboard layout/mapping.

        :param layout: The keyboard layout/mapping to use.
        :type layout: str
        :return:
        """
        if layout in self.layouts:
            self._current_layout = layout
        else:
            raise ValueError(f"Layout '{layout}' is not defined.")

    def _char_to_keystrokes(self, char: str) -> list[str]:
        if char.isupper():
            return [f"shift+{char.lower()}"]
        if char in self.shift_mappings[self._current_layout]:
            return [f"shift+{self.shift_mappings[self._current_layout][char]}"]
        if char in self.layouts[self._current_layout]:
            return [self.layouts[self._current_layout][char]]
        # Use UnicodeTyper for characters not in the layout
        return [f"alt+caps+{ord(char):04X} [UT]"]

    def type_out(self, password: str) -> list[str]:
        """
        Types out a password in the current keyboard layout/mapping.

        Takes in a password and returns a list of keyboard instructions to type the password in the current keyboard layout/mapping.

        :param password: The password to be typed out.
        :type password: str
        :return: A list of typing instructions.
        :rtype: list[str]
        """
        keystrokes = []
        for char in password:
            keystrokes.extend(self._char_to_keystrokes(char))
        return keystrokes

    @classmethod
    def type_out_static(cls, password: str, layout: str) -> list[str]:
        """
        Types out a password statically (no need for an instance) in the current keyboard layout/mapping.

        Takes in a password and returns a list of keyboard instructions to type the password in the current keyboard
        layout/mapping statically (no need for an instance).

        :param password: The password to type out.
        :type password: str
        :param layout: The keyboard layout/mapping to use.
        :type layout: str
        :return: The typed out password as a list.
        :rtype: list[str]
        """
        if layout not in cls.layouts:
            raise ValueError(f"Layout '{layout}' is not defined.")

        keystrokes = []
        for char in password:
            if char.isupper():
                keystroke = [f"shift+{char.lower()}"]
            elif char in cls.shift_mappings[layout]:
                keystroke = [f"shift+{cls.shift_mappings[layout][char]}"]
            elif char in cls.layouts[layout]:
                keystroke = [cls.layouts[layout][char]]
            else:
                # Use UnicodeTyper for characters not in the layout
                keystroke = [f"alt+caps+{ord(char):04X} [UT]"]
            keystrokes.extend(keystroke)
        return keystrokes


if __name__ == "__main__":
    from aplustools.package.timid import TimidTimer

    QuickGeneratePasswords.debug = False
    password_filter = PasswordFilter(exclude_chars="abc", extra_chars="@", exclude_similar=True)

    timer = TimidTimer()

    print("QuickGeneratePassword: ")
    print(PasswordCrackEstimator.tell_worst_case(QuickGeneratePasswords.generate_password(12, filter_=password_filter)))
    print(PasswordCrackEstimator.tell_worst_case(QuickGeneratePasswords.generate_secure_password(12, filter_=password_filter)))
    print(PasswordCrackEstimator.tell_worst_case(QuickGeneratePasswords.generate_passphrase(["Hello", "world", "abc"], 4, filter_=password_filter)))
    print(PasswordCrackEstimator.tell_worst_case(QuickGeneratePasswords.generate_pattern_password("XXX-999-xxx", filter_=password_filter)))
    print(PasswordCrackEstimator.tell_worst_case(QuickGeneratePasswords.generate_complex_password(12, filter_=password_filter)))
    print(PasswordCrackEstimator.tell_worst_case(QuickGeneratePasswords.generate_mnemonic_password(filter_=password_filter)))
    print(PasswordCrackEstimator.tell_worst_case(QuickGeneratePasswords.generate_ratio_based_password(12, letter_ratio=0.4, digit_ratio=0.3, symbol_ratio=0.3,
                                                               filter_=password_filter)))
    print(PasswordCrackEstimator.tell_worst_case(QuickGeneratePasswords.generate_sentence_based_password("WwWn!")))
    print(timer.end())

    print("----------------------------------------- DONE -----------------------------------------")

    password_generator = SpecificPasswordGenerator("strong")

    # Generate different types of passwords
    timer.start()
    password_generator.load_def_dict()
    print("SpecificPasswordGenerator: ")
    print("Sentence_V3", PasswordCrackEstimator.tell_worst_case(password_generator.generate_sentence_based_password_v3()))
    print("Default", PasswordCrackEstimator.tell_worst_case(password_generator.generate_random_password(filter_=password_filter)))
    print("Phrase", PasswordCrackEstimator.tell_worst_case(password_generator._generate_passphrase(filter_=password_filter)))
    print("Pattern", PasswordCrackEstimator.tell_worst_case(password_generator.generate_pattern_password(filter_=password_filter)))
    print("Complex", PasswordCrackEstimator.tell_worst_case(password_generator.generate_complex_password(filter_=password_filter)))
    print("Mnemonic", PasswordCrackEstimator.tell_worst_case(password_generator.generate_mnemonic_password(filter_=password_filter)))
    print("Sentence", password_generator.generate_sentence_based_password_v3(
        "Exploring the unknown -- discovering new horizons...", char_position="keep", num_length=5,
        special_chars_length=2))
    print(timer.end())

    print("----------------------------------------- DONE -----------------------------------------")

    print("SecurePasswordGenerator: ")
    generator = SecurePasswordGenerator("strong")
    for _ in range(12):
        print(generator.generate_secure_password())

    print("----------------------------------------- DONE -----------------------------------------")

    print("REDC", SpecificPasswordGenerator().reduce_password("HELLO WORLD", by=0))
    print(SpecificPasswordGenerator().dynamic_secure_password("Hello World", passes=1, expand=False))

    password = "HMBlw:_88008?@"
    print(PasswordCrackEstimator.zxcvbn(password))

    print("----------------------------------------- DONE -----------------------------------------")

    # from matplotlib import pyplot

    # print("V2", timer.complexity(gen.gen_ratio_pw_v2, range(1000, 24_000, 100), matplotlib_pyplt=pyplot))
    # print("V3", timer.complexity(gen.gen_ratio_pw_v3, range(1000, 24_000, 100), matplotlib_pyplt=pyplot))
    # password = PasswordGenerator().gen_ratio_pw_v3(length=24_000_000)
    # print(password, timer.end())
    # print(gen.gen_sentence_pw_v2("Hello my beautiful world!!", shuffle_words=False, shuffle_characters=False), timer.tock())
    # print(gen.gen_sentence_pw_v3("Hello my beautiful world!!", shuffle_words=False, shuffle_characters=False,
    #                              repeat_words=True, filter_=PasswordFilter(exclude_chars="Hello")), timer.end())
    # print(gen.gen_sentence_pw_v2("Hello my beautiful world!!", char_position="keep"), timer.tock())
    # print(gen.gen_sentence_pw_v3("Hello my beautiful world!!", char_position="keep", filter_=PasswordFilter(exclude_chars="Helo")), timer.end())

    print("SecurePasswordManager: ")
    manager = SecurePasswordManager(SecurePasswordManager.generate_suitable_password())
    manager.store_password("example.com", password)
    timer.start()
    password = manager.retrieve_password("example.com")
    print(password, "|", timer.tock())
    fast_password = manager.retrieve_password("example.com")  # for faster access.
    print(fast_password, "|", timer.tock())
    timer.end()

    print("----------------------------------------- DONE -----------------------------------------")

    print("PasswordReGenerator: ")
    gen = PasswordReGenerator(b'\x13V\xf8\xa8\xab\x96\xe6\x15\xdb\xbf?\xd0\xb5\x0c\xc6\x07\x94\n~Jy3\\\x97\x87\xfd\xff\x9d\x8c\xac\x90a')
    print(gen.generate_password("websize.com", "mypass"))
    print(gen.generate_password("web3", "my_pass", charset="ascii"))

    print("----------------------------------------- DONE -----------------------------------------")

    print("PasswordTypeHelper: ")
    pth = PasswordTypeHelper("us")
    print(pth.type_out("MyPeassword$$"))
    print(pth.type_out("Hello, World! 😊"))
    print(PasswordTypeHelper.type_out_static("MySecurePASSWORD", "us"))

    print("----------------------------------------- DONE -----------------------------------------")

    print("Reducers: ")
    print("REdC3", reducer_3("Hello Worl", range(70, 73)),
          reducer_3("SAtar", range(128, 255)))
    print("QREdC3", quick_reducer_3("Hello Worl", range(70, 73)),
          quick_reducer_3("SAtar", range(128, 255)))
    print("BREdC3", big_reducer_3("Hello Worl", [range(32, 126), range(128, 255)]),
          big_reducer_3("SAtar", [range(32, 55), range(128, 255)]))
    print("QBREdC3", quick_big_reducer_3("Hello Worl", [range(32, 126), range(128, 255)]),
          quick_big_reducer_3("SAtar", [range(32, 55), range(128, 255)]))

    print("----------------------------------------- DONE -----------------------------------------")
