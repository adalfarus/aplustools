from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from aplustools.security.rand import WeightedRandom
from typing import Union, Literal, Dict, Optional
from aplustools.io.environment import strict
from aplustools.data import nice_number
from enum import Enum
import unicodedata
import secrets
import string
import random
import math


class PasswordFilter:
    def __init__(self, exclude_chars: str = "", extra_chars: str = "", exclude_similar: bool = False):
        self.exclude_chars = exclude_chars
        self.extra_chars = extra_chars
        self.exclude_similar = exclude_similar
        self.extra_chars_dict = self._classify_extra_chars(extra_chars)

    def _classify_extra_chars(self, extra_chars):
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

    def apply(self, character_set, set_name):
        if self.exclude_similar:
            similar_chars = "il1Lo0O"
            character_set = ''.join(ch for ch in character_set if ch not in similar_chars)
        if self.exclude_chars:
            character_set = ''.join(ch for ch in character_set if ch not in self.exclude_chars)
        character_set += self.extra_chars_dict[set_name]
        return character_set

    def filter_word(self, word):
        # Filter the word according to the current settings
        filtered_word = ''.join(ch for ch in word if ch not in self.exclude_chars)
        if self.exclude_similar:
            similar_chars = "il1Lo0O"
            filtered_word = ''.join(ch for ch in filtered_word if ch not in similar_chars)
        return filtered_word

    def will_filter(self, char):
        return self.filter_word(char) == ""


class QuickGeneratePasswords:
    _rng = random
    characters = string.ascii_letters + string.digits
    debug = False

    @classmethod
    def _debug_print(cls, *args, **kwargs):
        if cls.debug:
            print(*args, **kwargs)

    @classmethod
    def generate_password(cls, length=12, filter_=None):
        cls._debug_print(f"Generating password of length {length}")
        characters = string.ascii_letters + string.digits + string.punctuation
        if filter_:
            characters = filter_.apply(characters, "letters")
            characters += filter_.apply(string.digits, "numbers")
            characters += filter_.apply(string.punctuation, "punctuations")
            cls._debug_print(f"Filtered characters: {characters}")
        password = ''.join(cls._rng.choice(characters) for _ in range(length))
        cls._debug_print(f"Generated password: {password}")
        return password

    @classmethod
    def generate_secure_password(cls, length=12, filter_=None):
        cls._debug_print(f"Generating secure password of length {length}")
        characters = string.ascii_letters + string.digits + string.punctuation
        if filter_:
            characters = filter_.apply(characters, "letters")
            characters += filter_.apply(string.digits, "numbers")
            characters += filter_.apply(string.punctuation, "punctuations")
            cls._debug_print(f"Filtered characters: {characters}")
        password = ''.join(secrets.choice(characters) for _ in range(length))
        cls._debug_print(f"Generated secure password: {password}")
        return password

    @classmethod
    def generate_passphrase(cls, words: list, num_words=4, filter_=None):
        cls._debug_print(f"Generating passphrase with {num_words} words")
        if filter_:
            words = list(filter(filter_.filter_word, words))
            cls._debug_print(f"Filtered words: {words[:10]}... (showing first 10)")
        passphrase = ' '.join(cls._rng.choice(words) for _ in range(num_words))
        cls._debug_print(f"Generated passphrase: {passphrase}")
        return passphrase

    @classmethod
    def generate_pattern_password(cls, pattern="XXX-999-xxx", filter_=None):
        cls._debug_print(f"Generating pattern password with pattern {pattern}")

        def random_char(c):
            if c == 'X':
                chars = string.ascii_uppercase
            elif c == 'x':
                chars = string.ascii_lowercase
            elif c == '9':
                chars = string.digits
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
    def generate_complex_password(cls, length=12, filter_=None):
        cls._debug_print(f"Generating complex password of length {length}")
        if length < 4:
            raise ValueError("Password length should be at least 4")

        all_characters = string.ascii_letters + string.digits + string.punctuation
        if filter_:
            all_characters = filter_.apply(all_characters, "letters")
            all_characters += filter_.apply(string.digits, "numbers")
            all_characters += filter_.apply(string.punctuation, "punctuations")
            cls._debug_print(f"Filtered all characters: {all_characters}")

        password = [
            cls._rng.choice(filter_.apply(string.ascii_uppercase, "letters")),
            cls._rng.choice(filter_.apply(string.ascii_lowercase, "letters")),
            cls._rng.choice(filter_.apply(string.digits, "numbers")),
            cls._rng.choice(filter_.apply(string.punctuation, "punctuations"))
        ]

        remaining_chars = all_characters
        password += [cls._rng.choice(remaining_chars) for _ in range(length - 4)]
        cls._rng.shuffle(password)

        cls._debug_print(f"Generated complex password: {''.join(password)}")
        return ''.join(password)

    @classmethod
    def generate_mnemonic_password(cls, filter_=None):
        cls._debug_print(f"Generating mnemonic password")
        adjectives = ["quick", "lazy", "sleepy", "noisy", "hungry"]
        nouns = ["fox", "dog", "cat", "mouse", "bear"]
        symbols = string.punctuation
        numbers = string.digits

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
    def generate_ratio_based_password(cls, length=12, letter_ratio=0.4, digit_ratio=0.3, symbol_ratio=0.3,
                                      filter_=None):
        cls._debug_print(f"Generating ratio-based password of length {length}")

        num_letters = int(length * letter_ratio)
        num_digits = int(length * digit_ratio)
        num_symbols = length - num_letters - num_digits

        characters = (
                (filter_.apply(string.ascii_letters, "letters") if filter_ else string.ascii_letters) * num_letters +
                (filter_.apply(string.digits, "numbers") if filter_ else string.digits) * num_digits +
                (filter_.apply(string.punctuation, "punctuations") if filter_ else string.punctuation) * num_symbols
        )

        password = ''.join(cls._rng.choice(characters) for _ in range(length))
        cls._debug_print(f"Generated ratio-based password: {password}")
        return password

    @classmethod
    def generate_sentence_based_password(cls, structure="WwWn!"):
        cls._debug_print(f"Generating sentence-based password with structure {structure}")

        words = ["quick", "brown", "fox", "jumps", "over", "lazy", "dog"]
        symbols = string.punctuation
        digits = string.digits

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


class PasswordGenerator:
    def __init__(self, random_generator: Literal["weak", "ok", "strong"] = "strong", debug: bool = False):
        self._rng = WeightedRandom({"weak": "random", "ok": "os", "strong": "secrets"}[random_generator])
        self.debug = debug

    def _debug_print(self, *args, **kwargs):
        if self.debug:
            print(*args, **kwargs)

    def generate_password(self, length=12, filter_=None):
        self._debug_print(f"Generating password of length {length}")
        characters = string.ascii_letters + string.digits + string.punctuation
        if filter_:
            characters = filter_.apply(characters, "letters")
            characters += filter_.apply(string.digits, "numbers")
            characters += filter_.apply(string.punctuation, "punctuations")
            self._debug_print(f"Filtered characters: {characters}")
        password = ''.join(self._rng.choice(characters) for _ in range(length))
        self._debug_print(f"Generated password: {password}")
        return password

    def generate_passphrase(self, words: list, num_words=4, filter_=None):
        self._debug_print(f"Generating passphrase with {num_words} words")
        if filter_:
            words = list(filter(filter_.filter_word, words))
            self._debug_print(f"Filtered words: {words[:10]}... (showing first 10)")
        passphrase = ' '.join(self._rng.choice(words) for _ in range(num_words))
        self._debug_print(f"Generated passphrase: {passphrase}")
        return passphrase

    def generate_pattern_password(self, pattern="XXX-999-xxx", filter_=None):
        self._debug_print(f"Generating pattern password with pattern {pattern}")

        def random_char(c):
            if c == 'X':
                chars = string.ascii_uppercase
            elif c == 'x':
                chars = string.ascii_lowercase
            elif c == '9':
                chars = string.digits
            else:
                return c

            if filter_:
                chars = filter_.apply(chars, "letters" if c in 'Xx' else "numbers" if c == '9' else "punctuations")
                self._debug_print(f"Filtered characters for '{c}': {chars}")

            return self._rng.choice(chars)

        password = ''.join(random_char(c) for c in pattern)
        self._debug_print(f"Generated pattern password: {password}")
        return password

    def generate_complex_password(self, length=12, filter_=None):
        self._debug_print(f"Generating complex password of length {length}")
        if length < 4:
            raise ValueError("Password length should be at least 4")

        all_characters = string.ascii_letters + string.digits + string.punctuation
        if filter_:
            all_characters = filter_.apply(all_characters, "letters")
            all_characters += filter_.apply(string.digits, "numbers")
            all_characters += filter_.apply(string.punctuation, "punctuations")
            self._debug_print(f"Filtered all characters: {all_characters}")

        password = [
            self._rng.choice(filter_.apply(string.ascii_uppercase, "letters")),
            self._rng.choice(filter_.apply(string.ascii_lowercase, "letters")),
            self._rng.choice(filter_.apply(string.digits, "numbers")),
            self._rng.choice(filter_.apply(string.punctuation, "punctuations"))
        ]

        remaining_chars = all_characters
        password += [self._rng.choice(remaining_chars) for _ in range(length - 4)]
        self._rng.shuffle(password)

        self._debug_print(f"Generated complex password: {''.join(password)}")
        return ''.join(password)

    def generate_mnemonic_password(self, filter_=None):
        self._debug_print(f"Generating mnemonic password")
        adjectives = ["quick", "lazy", "sleepy", "noisy", "hungry"]
        nouns = ["fox", "dog", "cat", "mouse", "bear"]
        symbols = string.punctuation
        numbers = string.digits

        adj = self._rng.choice(adjectives)
        noun = self._rng.choice(nouns)
        symbol = self._rng.choice(symbols)
        number = self._rng.choice(numbers)

        if filter_:
            adj = filter_.filter_word(adj)
            noun = filter_.filter_word(noun)
            symbol = self._rng.choice(filter_.apply(symbols, "punctuations"))
            number = self._rng.choice(filter_.apply(numbers, "numbers"))

        password = f"{adj}{symbol}{noun}{number}"
        self._debug_print(f"Generated mnemonic password: {password}")
        return password

    @staticmethod
    def generate_ratio_based_password_v1(length: int = 16, debug: bool = False, letters_ratio: float = 0.5,
                                         numbers_ratio: float = 0.3, punctuations_ratio: float = 0.2,
                                         unicode_ratio: float = 0, extra_chars: str = '', exclude_chars: str = ''):
        def debug_print(*args):
            if debug:
                print(*args)
        ratios = [letters_ratio, numbers_ratio, punctuations_ratio, unicode_ratio]
        if sum(ratios) != 1:
            raise ValueError("The sum of the ratios must be 1.")
        char_types = ['abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ', '0123456789',
                      '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~',
                      [chr(i) for i in range(0x110000) if unicodedata.category(chr(i)).startswith('P')]]
        char_lengths = [int(length * ratio) for ratio in ratios]
        debug_print("Character lengths before adjustment:", char_lengths)
        difference = length - sum(char_lengths)
        for i in range(difference):
            char_lengths[i % len(char_lengths)] += 1
        debug_print("Character lengths after adjustment:", char_lengths)
        all_chars = ''
        for i in range(len(char_types)):
            debug_print(f"Processing character type {i}: {char_types[i][:50]}...")
            if isinstance(char_types[i], str):
                char_type = char_types[i].translate(str.maketrans('', '', exclude_chars))
            else:
                char_type = ''.join([c for c in char_types[i] if c not in exclude_chars])
            debug_print(f"Character type {i} after excluding characters: {char_type[:50]}...")
            if char_lengths[i] > 0:
                generated_chars = ''.join(random.choices(char_type, k=char_lengths[i]))
                debug_print(f"Generated characters for character type {i}: {generated_chars}")
                all_chars += generated_chars
        debug_print("All characters before adding extra characters:", all_chars)
        all_chars += extra_chars
        all_chars = list(all_chars)
        random.shuffle(all_chars)
        debug_print("All characters after processing:", all_chars)
        if length > len(all_chars):
            raise ValueError("Password length is greater than the number of available characters.")
        password = ''.join(all_chars[:length])
        return password

    def generate_ratio_based_password_v2(self, length: int = 16, letters_ratio: float = 0.5, numbers_ratio: float = 0.3,
                                         punctuations_ratio: float = 0.2, unicode_ratio: float = 0,
                                         extra_chars: str = '', exclude_chars: str = '', exclude_similar: bool = False,
                                         _recur=False):
        """Generate a ratio based password, version 2"""
        ratios = [letters_ratio, numbers_ratio, punctuations_ratio, unicode_ratio]
        if sum(ratios) != 1:
            raise ValueError("The sum of the ratios must be 1.")
        char_types = ['abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ', '0123456789',
                      '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~',
                      [chr(i) for i in range(0x110000) if unicodedata.category(chr(i)).startswith('P')]]
        char_lengths = [int(length * ratio) for ratio in ratios]
        self._debug_print("Character lengths before adjustment:", char_lengths)
        difference = length - sum(char_lengths)
        for i in range(difference):
            char_lengths[i % len(char_lengths)] += 1
        self._debug_print("Character lengths after adjustment:", char_lengths)
        all_chars = ''
        for i in range(len(char_types)):
            self._debug_print(f"Processing character type {i}: {char_types[i][:50]}"
                              + "..." if len(char_types) > 50 else "")
            if isinstance(char_types[i], str):
                char_type = char_types[i].translate(str.maketrans('', '', exclude_chars))
            else:
                char_type = ''.join([c for c in char_types[i] if c not in exclude_chars])
            self._debug_print(f"Character type {i} after excluding characters: {char_type[:50]}"
                              + "..." if len(char_types) > 50 else "")
            if char_lengths[i] > 0:
                generated_chars = ''.join(self._rng.choice(char_type) for _ in range(char_lengths[i]))
                self._debug_print(f"Generated characters for character type {i}: {generated_chars}")
                all_chars += generated_chars
        self._debug_print("All characters before adding extra characters:", all_chars)
        all_chars += extra_chars
        all_chars_lst = list(all_chars)
        if exclude_similar:
            similar_chars = 'Il1O0'  # Add more similar characters if needed
            all_chars_lst = [c for c in all_chars_lst if c not in similar_chars]
            while len(all_chars_lst) < length and not _recur:
                all_chars_lst.extend(self.generate_ratio_password_v2(length, letters_ratio, numbers_ratio, punctuations_ratio,
                                                                     unicode_ratio, extra_chars, exclude_chars, exclude_similar,
                                                                     _recur=True))
        self._rng.shuffle(all_chars_lst)
        self._debug_print("All characters after processing:", all_chars_lst)
        if length > len(all_chars_lst) and not _recur:
            raise ValueError("Password length is greater than the number of available characters.")
        return ''.join(all_chars_lst[:length])

    def generate_ratio_based_password_v3(self, length: int = 24, letters_ratio: float = 0.5, numbers_ratio: float = 0.3,
                                         punctuations_ratio: float = 0.2, unicode_ratio: float = 0.0,
                                         filter_: PasswordFilter = None):
        """Generate a ratio based password, version 3"""
        character_sets = {
            "letters": 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ',
            "numbers": '0123456789',
            "punctuations": '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~',
            "unicode": unicode_ratio and   # Not generated, because it's 0 in most cases
            ''.join(chr(i) for i in range(0x110000) if unicodedata.category(chr(i)).startswith('P'))
        }
        self._debug_print(f"Generated char_sets {character_sets}")

        if filter_:
            for key in character_sets:
                if character_sets[key]:
                    character_sets[key] = filter_.apply(character_sets[key], key)

        self._debug_print(f"Filtered char_sets {character_sets}")

        non_zero_lengths = {ratio_name: ratio for ratio_name, ratio in
                            {"letters": math.ceil(length * letters_ratio),
                             "numbers": math.ceil(length * numbers_ratio),
                             "punctuations": math.ceil(length * punctuations_ratio),
                             "unicode": math.ceil(length * unicode_ratio)}.items()
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

    @staticmethod
    def generate_words_based_password_v1(sentence: str, debug: bool = False, shuffle_words: bool = True,
                                         shuffle_characters: bool = True):
        def debug_print(*args):
            if debug:
                print(*args)
        words = sentence.split(' ')
        if len(words) < 2:
            print("Error: Input must have more than one word.")
            return None
        password = ""
        if shuffle_words:
            debug_print("Words before shuffling", words)
            random.shuffle(words)
            debug_print("Words after shuffling", words)
        for word in words:
            if shuffle_characters:
                debug_print("Word before shuffling", list(word))
                word_chars = list(word)
                random.shuffle(word_chars)
                word = "".join(word_chars)
                debug_print("Word after shuffling", word)
            password += word
            debug_print("Words", words)
        return password

    def generate_words_based_password_v2(self, sentence: str, shuffle_words: bool = True,
                                         shuffle_characters: bool = True):
        words = sentence.split(' ')
        if len(words) < 2:
            print("Error: Input must have more than one word.")
            return None
        password = ""
        if shuffle_words:
            self._debug_print("Words before shuffling", words)
            self._rng.shuffle(words)
            self._debug_print("Words after shuffling", words)
        for word in words:
            if shuffle_characters:
                self._debug_print("Word before shuffling", list(word))
                word_chars = list(word)
                self._rng.shuffle(word_chars)
                word = "".join(word_chars)
                self._debug_print("Word after shuffling", word)
            password += word
            self._debug_print("Words", words)
        return password

    def generate_words_based_password_v3(self, sentence: str, shuffle_words: bool = True,
                                         shuffle_characters: bool = True, repeat_words: bool = False,
                                         filter_: PasswordFilter = None):
        words = sentence.split(' ')

        self._debug_print("Words", words)
        if shuffle_words:
            self._rng.shuffle(words)
            self._debug_print("Words after shuffling", words)

        password = ""
        i, length = 0, len(words)
        while i < length:
            if not repeat_words:
                word = words.pop(0)
            else:
                word = words[self._rng.randint(0, length-1)]
            if shuffle_characters:
                self._debug_print("Word before shuffling", list(word))
                word_chars = list(word)
                self._rng.shuffle(word_chars)
                word = "".join(word_chars)
                self._debug_print("Word after shuffling", word)
            password += filter_.filter_word(word) if filter_ is not None else word
            i += 1
        return password

    @staticmethod
    def generate_sentence_based_password_v1(sentence: str, debug: bool = False,
                                            char_position: Union[Literal["random", "keep"], int] = 'random',
                                            random_case: bool = False, extra_char: str = '', num_length: int = 0,
                                            special_chars_length: int = 0):
        def debug_print(*args):
            if debug:
                print(*args)
        words = sentence.split(' ')
        word_chars = []
        for word in words:
            if char_position == 'random':
                index = random.randint(0, len(word) - 1)
            elif char_position == 'keep':
                index = 0
            elif type(char_position) is int:
                index = min(char_position, len(word) - 1)
            else:
                return "Invalid char_position."
            char = word[index]
            if random_case:
                char = char.lower() if random.random() < 0.5 else char.upper()
            word_chars.append(char)
            debug_print("Word characters after processing:", word_chars)
        num_string = ''.join(random.choices('0123456789', k=num_length))
        debug_print("Numeric string after generation:", num_string)
        special_chars_string = ''.join(random.choices('!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~', k=special_chars_length))
        debug_print("Special characters string after generation:", special_chars_string)
        password = ''.join(word_chars) + extra_char + num_string + special_chars_string
        debug_print("Final password:", password)
        return password

    def generate_sentence_based_password_v2(self, sentence: str,
                                            char_position: Union[Literal["random", "keep"], int] = 'random',
                                            random_case: bool = False, extra_char: str = '', num_length: int = 0,
                                            special_chars_length: int = 0):
        words = sentence.split(' ')
        word_chars = []
        for word in words:
            if char_position == 'random':
                index = self._rng.randint(0, len(word) - 1)
            elif char_position == 'keep':
                index = 0
            elif type(char_position) is int:
                index = min(char_position, len(word) - 1)
            else:
                return "Invalid char_position."
            char = word[index]
            if random_case:
                char = char.lower() if self._rng.random() < 0.5 else char.upper()
            word_chars.append(char)
            self._debug_print("Word characters after processing:", word_chars)
        num_string = ''.join(self._rng.choices('0123456789', k=num_length))
        self._debug_print("Numeric string after generation:", num_string)
        special_chars_string = ''.join(self._rng.choices('!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~', k=special_chars_length))
        self._debug_print("Special characters string after generation:", special_chars_string)
        password = ''.join(word_chars) + extra_char + num_string + special_chars_string
        self._debug_print("Final password:", password)
        return password

    def generate_sentence_based_password_v3(self, sentence: str,
                                            char_position: Union[Literal["random", "keep"], int] = 'random',
                                            random_case: bool = False, extra_char: str = '', num_length: int = 0,
                                            special_chars_length: int = 0,
                                            password_format: str = "{words}{extra}{numbers}{special}",
                                            filter_: PasswordFilter = None):
        words = sentence.split(' ')
        word_chars = []
        for word in words:
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

        return password


@strict
class SecurePasswordManager:
    def __init__(self, key: bytes = secrets.token_bytes(32), debug: bool = False):
        # The key should be securely generated and stored.
        self._key = key
        self._passwords: Dict[str, str] = {}
        self._temp_buffer: Dict[int, str] = {}

        self._pass_gen = PasswordGenerator(debug=debug)
        self._debug = debug

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, new_value):
        self._debug = self._pass_gen.debug = new_value

    def add_password(self, account: str, username: str, password: str) -> None:
        iv = secrets.token_bytes(16)
        cipher = Cipher(algorithms.AES(self._key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        # Padding for AES block size
        padded_password = password + ' ' * (16 - len(password) % 16)
        ciphertext = encryptor.update(padded_password.encode()) + encryptor.finalize()

        self._passwords[account] = {'username': username, 'password': ciphertext, 'iv': iv}

    def get_password(self, account: str) -> str:
        if account not in self._passwords:
            raise ValueError("Account not found")

        data = self._passwords[account]
        cipher = Cipher(algorithms.AES(self._key), modes.CBC(data['iv']), backend=default_backend())
        decryptor = cipher.decryptor()

        decrypted_password = decryptor.update(data['password']) + decryptor.finalize()
        return decrypted_password.rstrip().decode()  # Removing padding

    def store_in_buffer(self, account: str, password_id: int) -> None:
        self._temp_buffer[password_id] = self.get_password(account)

    def use_from_buffer(self, password_id: int) -> str:
        if password_id not in self._temp_buffer:
            raise ValueError("Password ID not found in buffer")

        return self._temp_buffer[password_id]

    def generate_ratio_based_password_v2(self, length: int = 16, letters_ratio: float = 0.5, numbers_ratio: float = 0.3,
                                         punctuations_ratio: float = 0.2, unicode_ratio: float = 0,
                                         extra_chars: str = '', exclude_chars: str = '', exclude_similar: bool = False):
        return self._pass_gen.generate_ratio_password_v2(length, letters_ratio, numbers_ratio, punctuations_ratio,
                                                         unicode_ratio, extra_chars, exclude_chars, exclude_similar)

    def generate_sentence_based_password_v2(self, sentence: str, shuffle_words: bool = True,
                                            shuffle_characters: bool = True):
        return self._pass_gen.generate_words_password_v2(sentence, shuffle_words, shuffle_characters)

    def generate_custom_sentence_based_password_v2(self, sentence: str,
                                                   char_position: Union[Literal["random", "keep"], int] = 'random',
                                                   random_case: bool = False, extra_char: str = '', num_length: int = 0,
                                                   special_chars_length: int = 0):
        return self._pass_gen.generator_sentence_password_v2(sentence, char_position, random_case, extra_char,
                                                             num_length, special_chars_length)


if __name__ == "__main__":
    from aplustools.package.timid import TimidTimer

    QuickGeneratePasswords.debug = False
    password_filter = PasswordFilter(exclude_chars="abc", extra_chars="@", exclude_similar=True)

    timer = TimidTimer()
    print(QuickGeneratePasswords.generate_password(12, filter_=password_filter))
    print(QuickGeneratePasswords.generate_secure_password(12, filter_=password_filter))
    print(QuickGeneratePasswords.generate_passphrase(["Hello", "world", "abc"], 4, filter_=password_filter))
    print(QuickGeneratePasswords.generate_pattern_password("XXX-999-xxx", filter_=password_filter))
    print(QuickGeneratePasswords.generate_complex_password(12, filter_=password_filter))
    print(QuickGeneratePasswords.generate_mnemonic_password(filter_=password_filter))
    print(QuickGeneratePasswords.generate_ratio_based_password(12, letter_ratio=0.4, digit_ratio=0.3, symbol_ratio=0.3,
                                                               filter_=password_filter))
    print(QuickGeneratePasswords.generate_sentence_based_password("WwWn!"))
    print(timer.end())

    password_generator = PasswordGenerator()

    # Generate different types of passwords
    timer.start()
    print(password_generator.generate_password(12, filter_=password_filter))
    print(password_generator.generate_passphrase(["Hello", "Work", "abc"], 4, filter_=password_filter))
    print(password_generator.generate_pattern_password("XXX-999-xxx", filter_=password_filter))
    print(password_generator.generate_complex_password(12, filter_=password_filter))
    print(password_generator.generate_mnemonic_password(filter_=password_filter))
    print(timer.end())
    input()

    from matplotlib import pyplot

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
    password = manager.generate_ratio_based_password_v2(length=26, letters_ratio=0.5, numbers_ratio=0.3,
                                                        punctuations_ratio=0.2, exclude_similar=True)
    manager.add_password("example.com", "json-the-greatest", password)
    manager.store_in_buffer("example.com", 0)  # Stores unencrypted password in a buffer
    print(manager.get_password("example.com"), "|", manager.use_from_buffer(0))  # for faster access.

    print(GenerateWeakPasswords.generate_custom_sentence_based_password_v1(
        "Exploring the unknown -- discovering new horizons...", random_case=True, extra_char="_",
        char_position="keep", num_length=5, special_chars_length=2))


class CharSet(Enum):
    NUMERIC = "Numeric"
    ALPHA = "Alphabetic"
    ALPHANUMERIC = "Alphanumeric"
    ASCII = "ASCII"
    UNICODE = "Unicode"


class ComputerType(Enum):
    # Operations per second
    FASTEST_COMPUTER = 10**30 // 2  # One Quintillion (exascale), divided by 2 due to storage speed limits
    SUPERCOMPUTER = 1_102_000_000_000_000_000 // 2  # (Frontier), divided by 2 due to storage speed limits
    HIGH_END_PC = 1_000_000_000  # high-end desktop x86 processor
    NORMAL_PC = 50_000_000  # Example: A standard home computer
    OFFICE_PC = 1_000_000  # Example: An office PC
    OLD_XP_MACHINE = 10_000  # Example: An old Windows XP machine
    UNTHROTTLED_ONLINE = 10
    THROTTLED_ONLINE = 0.02777777777777778


class Efficiency(Enum):
    LOW = 0.5  # Low efficiency
    MEDIUM = 0.75  # Medium efficiency
    HIGH = 1.0  # High efficiency


class HashingAlgorithm(Enum):
    NTLM = 1_000_000_000  # NTLM (fast)
    MD5 = 500_000_000  # MD5 (medium speed)
    SHA1 = 200_000_000  # SHA1 (slow)
    BCRYPT = 1_000  # bcrypt (very slow)


class PasswordCrackEstimator:
    CHARSET_RANGES = {
        CharSet.NUMERIC: "0123456789",
        CharSet.ALPHA: "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
        CharSet.ALPHANUMERIC: "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        CharSet.ASCII: ''.join(chr(i) for i in range(128)),
        CharSet.UNICODE: ''.join(chr(i) for i in range(1114112))
    }

    CHARSET_SIZES = {
        CharSet.NUMERIC: 10,
        CharSet.ALPHA: 26 * 2,
        CharSet.ALPHANUMERIC: 10 + 26 * 2,
        CharSet.ASCII: 128,
        CharSet.UNICODE: 1114112
    }

    def __init__(self, charset, computer_type, efficiency, hashing_algorithm):
        self.charset = charset
        self.computer_type = computer_type
        self.efficiency = efficiency
        self.hashing_algorithm = hashing_algorithm

    def estimate_time_to_crack(self, password: str, length_range: Optional[Union[int, tuple]] = None,
                               personal_info: Optional[list] = None):
        cleaned_password = self._remove_common_patterns(password, personal_info)
        if not self._filter_by_charset(password):
            return cleaned_password, "Password not in charset"

        if isinstance(length_range, int):
            length_range = (length_range, length_range)
        else:
            length_range = length_range

        if length_range and (len(cleaned_password) < length_range[0] or len(cleaned_password) > length_range[1]):
            return cleaned_password, "Password length is outside the specified range"

        charset_size = self.CHARSET_SIZES[self.charset]
        if length_range:
            min_length, max_length = length_range
            total_combinations = sum(charset_size ** length for length in range(min_length, max_length + 1))
        else:
            total_combinations = charset_size ** len(cleaned_password)

        adjusted_ops_per_second = self.computer_type.value * self.efficiency.value * self.hashing_algorithm.value
        estimated_seconds = total_combinations / adjusted_ops_per_second
        return cleaned_password, self._format_time(estimated_seconds)

    def _remove_common_patterns(self, password, personal_info):
        common_patterns = self._generate_common_patterns()
        for pattern in common_patterns:
            if pattern in password:
                password = password.replace(pattern, "")

        if personal_info:
            personal_info.extend(self._generate_birthday_formats(personal_info))
            for info in personal_info:
                if info in password:
                    password = password.replace(info, "")
                if self._is_significant_match(info, password):
                    password = ''.join([c for c in password if c not in info])

        return password

    def _filter_by_charset(self, password):
        valid_chars = self.CHARSET_RANGES[self.charset]
        for char in password:
            if char in valid_chars:
                continue
            return False
        return True

    def _generate_common_patterns(self):
        patterns = []
        for i in range(10000):  # Generate number sequences from 0000 to 9999
            patterns.append(str(i).zfill(4))
            patterns.append(str(i).zfill(4)[::-1])  # Add reversed patterns
        return patterns

    @staticmethod
    def _generate_birthday_formats(personal_info):
        formats = []
        for info in personal_info:
            if len(info) == 8 and info.isdigit():  # YYYYMMDD
                year, month, day = info[:4], info[4:6], info[6:8]
                formats.extend([
                    f"{year}{month}{day}",
                    f"{day}{month}{year}",
                    f"{month}{day}{year}",
                    f"{year}-{month}-{day}",
                    f"{day}-{month}-{year}",
                    f"{month}-{day}-{year}",
                    f"{month}-{day}",
                    f"{month}{day}",
                    f"{day}-{month}",
                    f"{day}{month}",
                    f"{year}-{day}",
                    f"{year}{day}",
                    f"{day}-{year}",
                    f"{day}{year}"
                    f"{year}-{month}",
                    f"{year}{month}",
                    f"{month}-{year}",
                    f"{month}{year}"
                ])
        return formats

    def _is_significant_match(self, info, password):
        matches = sum(1 for char in info if char in password)
        return matches / len(info) >= 0.9

    def _format_time(self, seconds):
        if seconds < 60:
            return f"{seconds:.2f} seconds"
        elif seconds < 3600:
            return f"{seconds / 60:.2f} minutes"
        elif seconds < 86400:
            return f"{seconds / 3600:.2f} hours"
        elif seconds < 31536000:
            return f"{seconds / 86400:.2f} days"
        else:
            return f"{nice_number(int(seconds / 31536000))} years"


if __name__ == "__main__":
    charset = CharSet.ASCII
    computer_type = ComputerType.THROTTLED_ONLINE
    efficiency = Efficiency.HIGH
    hashing_algorithm = HashingAlgorithm.BCRYPT

    estimator = PasswordCrackEstimator(charset, computer_type, efficiency, hashing_algorithm)
    password = "HMBlw:_88008?@"
    personal_info = ["John", "19841201", "Doe"]
    actual_password, time_to_crack = estimator.estimate_time_to_crack(password, length_range=(1, 24), personal_info=personal_info)
    print(f"Estimated time to crack the password '{password}' [{actual_password}]: {time_to_crack}")
