from cryptography.hazmat.primitives.ciphers import Cipher as _Cipher, algorithms as _algorithms, modes as _modes
from cryptography.hazmat.backends import default_backend as _default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC as _PBKDF2HMAC
from cryptography.hazmat.primitives import hashes as _hashes
from cryptography.hazmat.primitives import padding as _padding
from zxcvbn import zxcvbn as _zxcvbn

from aplustools.security.rand import WeightedRandom as _WeightedRandom
from aplustools.data import beautify_json as _beautify_json
from aplustools.io.environment import strict as _strict

from typing import Union as _Union, Literal as _Literal, Optional as _Optional, Dict as _Dict, Tuple as _Tuple
from importlib import resources as _resources
import unicodedata as _unicodedata
import secrets as _secrets
import string as _string
import random as _random
import math as _math
import os as _os


class PasswordFilter:
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
        if self.exclude_similar:
            similar_chars = "il1Lo0O"
            character_set = ''.join(ch for ch in character_set if ch not in similar_chars)
        if self.exclude_chars:
            character_set = ''.join(ch for ch in character_set if ch not in self.exclude_chars)
        character_set += self.extra_chars_dict[set_name]
        return character_set

    def filter_word(self, word: str) -> str:
        # Filter the word according to the current settings
        filtered_word = ''.join(ch for ch in word if ch not in self.exclude_chars)
        if self.exclude_similar:
            similar_chars = "il1Lo0O"
            filtered_word = ''.join(ch for ch in filtered_word if ch not in similar_chars)
        return filtered_word

    def will_filter(self, char: str) -> bool:
        return self.filter_word(char) == ""


class QuickGeneratePasswords:
    _rng = _random
    characters = _string.ascii_letters + _string.digits
    debug = False

    @classmethod
    def _debug_print(cls, *args, **kwargs):
        if cls.debug:
            print(*args, **kwargs)

    @classmethod
    def quick_secure_password(cls, password: str, passes: int = 3, expand: bool = True) -> str:
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
        cls._debug_print(f"Generating passphrase with {num_words} words")
        if filter_:
            words = list(filter(filter_.filter_word, words))
            cls._debug_print(f"Filtered words: {words[:10]}... (showing first 10)")
        passphrase = ' '.join(cls._rng.choice(words) for _ in range(num_words))
        cls._debug_print(f"Generated passphrase: {passphrase}")
        return passphrase

    @classmethod
    def generate_pattern_password(cls, pattern: str = "XXX-999-xxx", filter_: _Optional[PasswordFilter] = None) -> str:
        cls._debug_print(f"Generating pattern password with pattern {pattern}")

        def random_char(c):
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

        password = ''.join(random_char(c) for c in pattern)
        cls._debug_print(f"Generated pattern password: {password}")
        return password

    @classmethod
    def generate_complex_password(cls, length: int = 12, filter_: _Optional[PasswordFilter] = None) -> str:
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

    def load_def_dict(self):
        with _resources.path("aplustools.security.dicts", "def-dict.txt") as file_path:
            with open(file_path, "r") as f:
                self.words.extend([line.strip() for line in f])

    def load_google_10000_dict(self):
        with _resources.path("aplustools.security.dicts", "google-10000-dict.txt") as file_path:
            with open(file_path, "r") as f:
                self.words.extend([line.strip() for line in f])

    def load_scowl_dict(self, size: _Literal[50, 60, 70, 80, 95] = 50):
        with _resources.path("aplustools.security.dicts", f"scowl-{size}-dict.txt") as file_path:
            with open(file_path, "r") as f:
                self.words.extend([line.strip() for line in f])

    def load_12_dicts(self):
        with _resources.path("aplustools.security.dicts", "12-dicts") as file_path:
            for file in _os.listdir(file_path):
                with open(_os.path.join(file_path, file), "r") as f:
                    self.words.extend([line.strip() for line in f])

    def unload_dicts(self):
        self.words = []

    def secure_password(self, password: str, passes: int = 3, expand: bool = True) -> str:
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

    def generate_secure_sentence(self, length: int = 4) -> str:
        return ' '.join(self._rng.sample(self.words, length))

    def reduce_password(self, password: str, by: _Union[int, _Literal["all"]] = 0) -> str:
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
                                   filter_: _Optional[PasswordFilter] = None) -> str:
        return self.secure_password(self._generate_passphrase(words, num_words, filter_), passes=1)

    def generate_pattern_password(self, pattern: str = "9/XxX-999xXx-99/XxX-999xXx-9",
                                  filter_: _Optional[PasswordFilter] = None) -> str:
        self._debug_print(f"Generating pattern password with pattern {pattern}")

        def random_char(c):
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
                self._debug_print(f"Filtered characters for '{c}': {chars}")

            return self._rng.choice(chars)

        password = ''.join(random_char(c) for c in pattern)
        self._debug_print(f"Generated pattern password: {password}")
        return password

    def generate_complex_password(self, length: int = 18, filter_: _Optional[PasswordFilter] = None) -> str:
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
        """Generate a ratio based password, version 3"""
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
    def __init__(self, security: _Literal["weak", "average", "strong"]):
        self._rng = _WeightedRandom({"weak": "random", "average": "np_random", "strong": "secrets"}[security])
        self._gen = SpecificPasswordGenerator(self._rng)
        self._gen.load_def_dict()

    def generate_secure_password(self, return_worst_case: bool = True, predetermined: _Optional[
                                                                                      _Literal["random", "passphrase",
                                                                                               "pattern", "complex",
                                                                                               "mnemonic", "ratio",
                                                                                               "words", "sentence"
                                                                                      ]] = None) -> dict:
        rnd = self._rng.randint(0, 7) if predetermined is None else \
            {
                "random": 0,
                "passphrase": 1,
                "pattern": 2,
                "complex": 3,
                "mnemonic": 4,
                "ratio": 5,
                "words": 6,
                "sentence": 7
            }[predetermined]
        result = {"extra_info": "", "password": "", "worst_case": ""}

        match rnd:
            case 0:
                pw = self._gen.generate_random_password()
                result = {"extra_info": "Entirely random", "password": pw}
            case 1:
                pw = self._gen.generate_secure_passphrase(self._gen.words)
                result = {"extra_info": "Passphrase, secure as it's very long.", "password": pw}
            case 2:
                pattern = ''.join(self._rng.choices("/XXXxxx-999", 28))
                pw = self._gen.generate_pattern_password(pattern)
                result = {"extra_info": f"A pattern password with the pattern '{pattern}'.", "password": pw}
            case 3:
                pw = self._gen.generate_complex_password()
                result = {"extra_info": "Entirely random, a complex password.", "password": pw}
            case 4:
                pw, adj, noun = self._gen.generate_mnemonic_password(_return_info=True)
                result = {"extra_info": f"A mnemonic password using the adj '{adj}' and the noun '{noun}'.",
                          "password": pw}
            case 5:
                pw = self._gen.generate_ratio_based_password_v3()
                result = {"extra_info": "Entirely random, a ratio based password.", "password": pw}
            case 6:
                pw, sentence = self._gen.generate_words_based_password_v3(_return_info=True)
                result = {"extra_info": f"A words based password using the sentence '{sentence}_.", "password": pw}
            case 7:
                spec_char = self._rng.choice('!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~')
                pattern = ''.join(self._rng.sample(["{words}", "{special}", "{extra}", "{numbers}"], 4))
                pw, sentence = self._gen.generate_sentence_based_password_v3(extra_char=spec_char,
                                                                             password_format=pattern, _return_info=True)
                result = {"extra_info": f"A sentence based password using the sentence '{sentence}' "
                                        f"and the pattern '{pattern}'.", "password": pw}

        if return_worst_case:
            result["worst_case"] = _zxcvbn(result["password"])["crack_times_display"]["offline_fast_hashing_1e10_per_second"]

        return result


class PasswordReGenerator:
    def __init__(self, key: bytes = None, seed_file: str = "seed_file.enc", debug: bool = False):
        self._key = key or _os.urandom(32)
        self._seed_file = seed_file
        self._debug = debug
        self._load_or_create_seed_file()

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

    def generate_password(self, identifier: str, simple_password: str, length: int = 64) -> str:
        salt = self._seed + identifier.encode() + simple_password.encode()
        kdf = _PBKDF2HMAC(
            algorithm=_hashes.SHA256(),
            length=length,
            salt=salt,
            iterations=100000,
            backend=_default_backend()
        )
        password = kdf.derive(self._key)
        return self._format_password(password, length)

    def _format_password(self, password: bytes, length: int) -> str:
        # Convert to a readable password
        return password.hex()[:length]


@_strict
class SecurePasswordManager:
    def __init__(self, key: bytes = _secrets.token_bytes(32), debug: bool = False):
        # The key should be securely generated and stored.
        self._key = key
        self._passwords: _Dict[str, str] = {}
        self._temp_buffer: _Dict[int, str] = {}

        self._pass_gen = SpecificPasswordGenerator(debug=debug)
        self._debug = debug

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, new_value):
        self._debug = self._pass_gen.debug = new_value

    def add_password(self, account: str, username: str, password: str) -> None:
        iv = _secrets.token_bytes(16)
        cipher = _Cipher(_algorithms.AES(self._key), _modes.CBC(iv), backend=_default_backend())
        encryptor = cipher.encryptor()

        # Padding for AES block size
        padded_password = password + ' ' * (16 - len(password) % 16)
        ciphertext = encryptor.update(padded_password.encode()) + encryptor.finalize()

        self._passwords[account] = {'username': username, 'password': ciphertext, 'iv': iv}

    def get_password(self, account: str) -> str:
        if account not in self._passwords:
            raise ValueError("Account not found")

        data = self._passwords[account]
        cipher = _Cipher(_algorithms.AES(self._key), _modes.CBC(data['iv']), backend=_default_backend())
        decryptor = cipher.decryptor()

        decrypted_password = decryptor.update(data['password']) + decryptor.finalize()
        return decrypted_password.rstrip().decode()  # Removing padding

    def store_in_buffer(self, account: str, password_id: int) -> None:
        self._temp_buffer[password_id] = self.get_password(account)

    def use_from_buffer(self, password_id: int) -> str:
        if password_id not in self._temp_buffer:
            raise ValueError("Password ID not found in buffer")

        return self._temp_buffer[password_id]

    def generate_ratio_based_password(self, length: int = 16, letters_ratio: float = 0.5, numbers_ratio: float = 0.3,
                                      punctuations_ratio: float = 0.2, unicode_ratio: float = 0,
                                      extra_chars: str = '', exclude_chars: str = '', exclude_similar: bool = False
                                      ) -> str:
        return self._pass_gen.generate_ratio_based_password_v3(length, letters_ratio, numbers_ratio, punctuations_ratio,
                                                               unicode_ratio, filter_=PasswordFilter(exclude_chars,
                                                                                                     extra_chars,
                                                                                                     exclude_similar))

    def generate_sentence_based_password(self, sentence: str, shuffle_words: bool = True,
                                         shuffle_characters: bool = True) -> str:
        return self._pass_gen.generate_words_based_password_v3(sentence, shuffle_words, shuffle_characters)

    def generate_custom_sentence_based_password(self, sentence: str,
                                                char_position: _Union[_Literal["random", "keep"], int] = 'random',
                                                random_case: bool = False, extra_char: str = '', num_length: int = 0,
                                                special_chars_length: int = 0) -> str:
        return self._pass_gen.generate_sentence_based_password_v3(sentence, char_position, random_case, extra_char,
                                                                  num_length, special_chars_length)


class PasswordCrackEstimator:
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

    """Using zxcvbn to deliver an easy result as it's a hard to find and a bit confusing package for beginners."""
    @staticmethod
    def estimate_time_to_crack(password: str) -> tuple:
        result = _zxcvbn(password)
        return result["password"], result["crack_times_display"]

    @staticmethod
    def tell_pass_sec(password: str) -> tuple:
        result = _zxcvbn(password)
        return result["password"], result["crack_times_seconds"]

    @staticmethod
    def zxcvbn(password: str, user_inputs: list = None):
        if user_inputs is None:
            user_inputs = []
        return _beautify_json(_zxcvbn(password, user_inputs))

    @classmethod
    def _test_password_strength(cls, function, preset, num_passwords=1000):
        worst_times = []

        for _ in range(max(1, num_passwords)):
            password = function(*preset[0], **preset[1])
            security = cls.tell_pass_sec(password)
            worst_time = security[1]['offline_fast_hashing_1e10_per_second']
            worst_times.append(float(worst_time))

        average_worst_time = sum(worst_times) / len(worst_times)
        return security[0], average_worst_time / (60 * 60 * 24 * 365.25)  # Convert seconds to years

    @classmethod
    def find_best_preset(cls, function, presets: _Tuple[tuple, dict]):
        for preset in presets:
            sec, average_worst_case_years = cls._test_password_strength(function, preset)
            print(f"Preset {preset} average worst-case time to crack: {average_worst_case_years:.2f} years [{sec}]")
            if average_worst_case_years >= 2:  # Adjust the threshold as needed
                print(
                    f"Preset {preset} meets the security criteria with an average worst-case time to crack of {average_worst_case_years:.2f} years.")
                break

    @staticmethod
    def tell_worst_case(password: str) -> tuple:
        result = _zxcvbn(password)
        return result["password"], "Worst Case: " + result["crack_times_display"][
            "offline_fast_hashing_1e10_per_second"]


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
    print(timer.end())

    print("----------------------------------------- DONE -----------------------------------------")

    print("SecurePasswordGenerator: ")
    generator = SecurePasswordGenerator("strong")
    for _ in range(6):
        print(PasswordCrackEstimator.tell_worst_case(generator.generate_secure_password()["password"]))
        print(PasswordCrackEstimator.tell_worst_case(generator.generate_secure_password(predetermined="passphrase")["password"]))

    print("----------------------------------------- DONE -----------------------------------------")

    print("REDC", SpecificPasswordGenerator().reduce_password("HELLO WORLD", by=0))
    print(SpecificPasswordGenerator().secure_password("Hello World", passes=1, expand=False))

    password = "HMBlw:_88008?@"
    print(PasswordCrackEstimator.zxcvbn(password))

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

    manager = SecurePasswordManager()
    password = manager.generate_ratio_based_password(length=26, letters_ratio=0.5, numbers_ratio=0.3,
                                                     punctuations_ratio=0.2, exclude_similar=True)
    manager.add_password("example.com", "json-the-greatest", password)
    manager.store_in_buffer("example.com", 0)  # Stores unencrypted password in a buffer
    print(manager.get_password("example.com"), "|", manager.use_from_buffer(0))  # for faster access.

    print(manager.generate_custom_sentence_based_password(
        "Exploring the unknown -- discovering new horizons...", char_position="keep", num_length=5,
        special_chars_length=2))

    gen = PasswordReGenerator(b'\x13V\xf8\xa8\xab\x96\xe6\x15\xdb\xbf?\xd0\xb5\x0c\xc6\x07\x94\n~Jy3\\\x97\x87\xfd\xff\x9d\x8c\xac\x90a')
    print(gen.generate_password("websize.com", "mypass"))
