"""TBA"""
from importlib.resources import files as _files
import unicodedata as _unicodedata
import secrets as _secrets
import string as _string
import base64 as _base64
import random as _random
import math as _math
import json as _json
import os as _os

from ..package import enforce_hard_deps as _enforce_hard_deps, optional_import as _optional_import
from .rand import generator as _generator

# Standard typing imports for aps
from abc import abstractmethod
import collections.abc as _a
import typing as _ty
import types as _ts

__deps__: list[str] = ["zxcvbn"]
__hard_deps__: list[str] = []
_enforce_hard_deps(__hard_deps__, __name__)

_zxcvbn: _ts.ModuleType | None = _optional_import("zxcvbn.zxcvbn")  # TODO: Fix returned type


class PasswordFilter:
    """Used to easily filter passwords based on a few simple concepts."""
    def __init__(self, exclude_chars: str = "", extra_chars: str = "", exclude_similar: bool = False):
        self.exclude_chars: str = exclude_chars
        self.extra_chars: str = extra_chars
        self.exclude_similar: bool = exclude_similar
        self.extra_chars_dict: dict[str, str] = self._classify_extra_chars(extra_chars)

    def _classify_extra_chars(self, extra_chars: str) -> dict[str, str]:
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

    def apply(self, character_set: str, set_name: _ty.Literal["letters", "numbers", "punctuations", "unicode"]) -> str:
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
    characters: str = _string.ascii_letters + _string.digits
    debug: bool = False

    @classmethod
    def _debug_print(cls, *args: _ty.Any, **kwargs: _ty.Any) -> None:
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
    def generate_password(cls, length: int = 12, filter_: PasswordFilter | None = None) -> str:
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
    def generate_secure_password(cls, length: int = 12, filter_: PasswordFilter | None = None) -> str:
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
    def generate_passphrase(cls, words: list[str], num_words: int = 4, filter_: PasswordFilter | None = None) -> str:
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
    def generate_pattern_password(cls, pattern: str = "XXX-999-xxx", filter_: PasswordFilter | None = None) -> str:
        """
        A pattern password X for an uppercase letter, x for a lowercase letter and 9 for a number.
        All other characters are ignored and included as is in the final password

        :param pattern: The pattern to generate the password by
        :param filter_: An optional password filter
        :return: The generated password
        """
        cls._debug_print(f"Generating pattern password with pattern {pattern}")

        def _random_char(c: str) -> str:
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

            return str(cls._rng.choice(chars))

        password = ''.join(_random_char(c) for c in pattern)
        cls._debug_print(f"Generated pattern password: {password}")
        return password

    @classmethod
    def generate_complex_password(cls, length: int = 12, filter_: PasswordFilter | None = None) -> str:
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

        if filter_:
            password = [
                cls._rng.choice(filter_.apply(_string.ascii_uppercase, "letters")),
                cls._rng.choice(filter_.apply(_string.ascii_lowercase, "letters")),
                cls._rng.choice(filter_.apply(_string.digits, "numbers")),
                cls._rng.choice(filter_.apply(_string.punctuation, "punctuations"))
            ]
        else:
            password = [
                cls._rng.choice(_string.ascii_uppercase),
                cls._rng.choice(_string.ascii_lowercase),
                cls._rng.choice(_string.digits),
                cls._rng.choice(_string.punctuation)
            ]

        remaining_chars = all_characters
        password += [cls._rng.choice(remaining_chars) for _ in range(length - 4)]
        cls._rng.shuffle(password)

        cls._debug_print(f"Generated complex password: {''.join(password)}")
        return ''.join(password)

    @classmethod
    def generate_mnemonic_password(cls, filter_: PasswordFilter | None = None) -> str:
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
                                      symbol_ratio: float = 0.3, filter_: PasswordFilter | None = None) -> str:
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
                                                   char_position: _ty.Literal["random", "keep"] | int = 'random',
                                                   random_case: bool = False, extra_char: str = '', num_length: int = 0,
                                                   special_chars_length: int = 0) -> str:
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
    def __init__(self, random_generator: _ty.Literal["weak", "average", "strong"] | _ty.Any = "strong",
                 debug: bool = False) -> None:
        if isinstance(random_generator, str):
            self._rng = _generator({"weak": "random", "average": "np_random", "strong": "secrets"}[random_generator])  # type: ignore
        else:
            self._rng = random_generator
        self.debug: bool = debug
        self.words: list[str] = []

    def _debug_print(self, *args: _ty.Any, **kwargs: _ty.Any) -> None:
        if self.debug:
            print(*args, **kwargs)

    def _add_unique_words(self, words: list[str]) -> None:
        unique_words = set(self.words)  # Create a set of current words for fast membership testing
        for word in words:
            if word not in unique_words:
                self.words.append(word)
                unique_words.add(word)

    def load_def_dict(self) -> None:
        """
        Loads the default dictionary for random sentence generation.
        :return:
        """
        file_path = _files("aplustools.security.dicts").joinpath("def-dict.txt")
        with file_path.open("r") as f:
            self._add_unique_words([line.strip() for line in f])

    def load_google_10000_dict(self) -> None:
        """
        Loads google 10 000 dictionary for random sentence generation (uk & us without swears).
        :return:
        """
        file_path = _files("aplustools.security.dicts").joinpath("google-10000-dict.txt")
        with file_path.open("r") as f:
            self._add_unique_words([line.strip() for line in f])

    def load_scowl_dict(self, size: _ty.Literal["50", "60", "70", "80", "95"] = "50") -> None:
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

    def load_12_dicts(self) -> None:
        """
        Loads a selection of the 12 dicts which were deemed the most useful in sentence generation.
        :return:
        """
        dir_path = _files("aplustools.security.dicts").joinpath("12-dicts")
        for file in dir_path.iterdir():
            with file.open("r") as f:
                self._add_unique_words([line.strip() for line in f])

    def unload_dicts(self) -> None:
        """Unloads all currently loaded dictionaries."""
        self.words.clear()

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
            idx1, idx2 = self._rng.sample(list(range(length)), 2)
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
            idx1, idx2 = self._rng.sample(list(range(length)), 2)
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
        get_num: _ty.Callable[[], int] = lambda: max(2, (length * self._rng.choice([10, 20, 30])) // 100)

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
            idx1, idx2 = self._rng.sample(list(range(length)), 2)
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
        return ' '.join(self._rng.choices(self.words, k=length))

    def reduce_password(self, password: str, by: int | _ty.Literal["all"] = 0) -> str:
        """
        Reduces a given password using random binary operations to ensure a secure password.

        :param password: The password to be reduces
        :param by: How many characters each character should be joined with (0 means none and "all" means all).
        :return: The reduced password
        """
        byi: int = int(by if by != "all" else len(password))
        result = []

        for chunk in (password[i:i+byi+1] for i in range(0, len(password), byi + 1)):
            if byi == 0:
                chunk = chunk + chunk  # Duplicate the character to make a two-character chunk
            while len(chunk) < byi + 1:
                chunk += chunk  # Repeat the chunk until it reaches the desired size
            chunk = chunk[:byi + 1]  # Trim the chunk to the exact desired size

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

    def generate_random_password(self, length: int = 18, filter_: PasswordFilter | None = None) -> str:
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

    def _generate_passphrase(self, words: list[str] | None = None, num_words: int = 6, filter_: PasswordFilter | None = None
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

    def generate_secure_passphrase(self, words: list[str] | None = None, num_words: int = 6,
                                   filter_: PasswordFilter | None = None, _return_info: bool = True) -> str | tuple[str, str]:
        """
        Passphrase, secure as it's very long

        :param words: Which words to use in the passphrase
        :param num_words: The number of words to be used
        :param filter_: An optional password filter
        :param _return_info: If extra info about the password should be returned
        :return: The generated password
        """
        passphrase: str = self._generate_passphrase(words, num_words, filter_)
        secure_passphrase: str = self.dynamic_secure_password(passphrase, passes=1)
        return (secure_passphrase, passphrase) if _return_info else secure_passphrase

    def generate_pattern_password(self, pattern: str = "9/XxX-999xXx-99/XxX-999xXx-9",
                                  filter_: PasswordFilter | None = None) -> str:
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

        def _random_char(c: str) -> str:
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
                                          filter_: PasswordFilter | None = None) -> str:
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

    def generate_complex_password(self, length: int = 18, filter_: PasswordFilter | None = None) -> str:
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

    def generate_mnemonic_password(self, length: int = 20, filter_: PasswordFilter | None = None,
                                   _return_info: bool = False) -> str | tuple[str, str, str]:
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
                                         filter_: PasswordFilter | None = None) -> str:
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
        character_sets: dict[str, str] = {
            "letters": 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ',
            "numbers": '0123456789',
            "punctuations": '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
        }
        if unicode_ratio != 0.0:
            character_sets["unicode"] = ''.join(chr(i) for i in range(0x110000) if _unicodedata.category(chr(i)).startswith('P'))
        self._debug_print(f"Generated char_sets {character_sets}")

        if filter_:
            for key in character_sets:
                if character_sets[key]:
                    character_sets[key] = filter_.apply(character_sets[key], key)  # type: ignore

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
        password_characters: list[str] = []
        for key, num_chars in non_zero_lengths.items():
            if character_sets[key]:
                password_characters.extend(self._rng.choices(character_sets[key], k=num_chars))

        self._debug_print(f"Generated password chars {password_characters}")

        # Shuffle the resulting password characters to ensure randomness
        self._rng.shuffle(password_characters)

        self._debug_print(f"Final password chars {password_characters}")

        return ''.join(password_characters)

    def generate_words_based_password_v3(self, sentence: str | None = None, shuffle_words: bool = True,
                                         shuffle_characters: bool = True, repeat_words: bool = False,
                                         filter_: PasswordFilter | None = None, _return_info: bool = False) -> str | tuple[str, str]:
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
            words = [''.join(self._rng.sample(list(word), len(word))) for word in words]
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

    def generate_sentence_based_password_v3(self, sentence: str | None = None,
                                            char_position: _ty.Literal["random", "keep"] | int = 'keep',
                                            random_case: bool = True, extra_char: str = '/', num_length: int = 6,
                                            special_chars_length: int = 4,
                                            password_format: str = "{words}{special}{extra}{numbers}",
                                            filter_: PasswordFilter | None = None, _return_info: bool = False) -> str | tuple[str, str]:
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

    def __init__(self, security: _ty.Literal["weak", "average", "strong", "super_strong"]):
        self._rng = _generator({"weak": "random", "average": "np_random", "strong": "secrets",
                                "super_strong": "secrets"}[security])  # type: ignore
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
        print(f"Loaded {len(self._gen.words):,} unique words")

    def exponential(self, lower_bound: float | int = 0, upper_bound: float | int = 1,
                    multiplier: float = 1.0) -> float:
        """
        Generate a random number based on the exponential distribution and scale it within the specified bounds.

        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :param multiplier: Multiplier parameter x**mult e of the distribution.
        :return: Scaled random number from the exponential distribution.
        """
        transformed_value: float = (lambda x: x ** (multiplier * _math.e))(self._rng.random())
        scaled_value: float = lower_bound + (upper_bound - lower_bound) * transformed_value
        return scaled_value

    def generate_secure_password(self, return_worst_case: bool = False, predetermined: _ty.Literal["random", "passphrase",
                                                                                               "pattern", "complex",
                                                                                               "mnemonic", "ratio",
                                                                                               "words", "sentence",
                                                                                               "complex_pattern"
                                                                                      ] | None = None) -> dict[str, str]:
        """
        Generates always secure, always changing passwords that are designed to be human readable.
        The target worst time to crack is one century for each generated password.

        :param return_worst_case: Return the worst case estimate by zxcvbn
        :param predetermined: Choose which type of password you want to generate, this will make it 8 times easier to crack your password.
        :return:
        """
        rnd = int(self.exponential(0, 8, 0.9)) if predetermined is None else \
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
        match rnd:
            case 0:
                pw, adj, noun = self._gen.generate_mnemonic_password(_return_info=True)
                result = {"extra_info": f"A mnemonic password using the adj '{adj}' and the noun '{noun}'.",
                          "password": pw}
            case 1:
                pw, sentence = self._gen.generate_secure_passphrase(self._gen.words, _return_info=True)
                result = {"extra_info": f"Passphrase, secure as it's very long, using the sentence '{sentence}'", "password": pw}
            case 2:
                pattern = ''.join(self._rng.choices("/XXXxxx-999", k=28))
                pw = self._gen.generate_pattern_password(pattern)
                result = {"extra_info": f"A pattern password with the pattern '{pattern}'.", "password": pw}
            case 3:
                pattern = ''.join(self._rng.choices("/XXXxxx-999nnWw!!!", k=28))
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
                result = {"extra_info": "", "password": "", "worst_case": ""}

        if return_worst_case:
            if _zxcvbn is None:
                raise RuntimeError("zxcvbn is not installed")
            result["worst_case"] = _zxcvbn(result["password"])["crack_times_display"]["offline_fast_hashing_1e10_per_second"]  # type: ignore

        return result
