from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from typing import Union, Literal, Dict, Optional
from aplustools.io.environment import strict
from aplustools.data import nice_number
from enum import Enum
import unicodedata
import secrets
import string
import random


class GenerateWeakPasswords:
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
        char_types = [string.ascii_letters, string.digits, string.punctuation, [chr(i) for i in range(0x110000) if
                                                                                unicodedata.category(chr(i)).startswith('P')]]
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

    @staticmethod
    def generate_sentence_based_password_v1(sentence: str, debug: bool = False, shuffle_words: bool = True,
                                            shuffle_characters: bool = True, repeat_words: bool = False):
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
        used_words = set()
        for word in words:
            if not repeat_words and word in used_words:
                debug_print("Ignoring repeated word")
                continue
            if shuffle_characters:
                debug_print("Word before shuffling", list(word))
                word_chars = list(word)
                random.shuffle(word_chars)
                word = "".join(word_chars)
                debug_print("Word after shuffling", word)
            password += word
            used_words.add(word)
            debug_print("Used Words", used_words)
            debug_print("Words", words)
        return password

    @staticmethod
    def generate_custom_sentence_based_password_v1(sentence: str, debug: bool = False,
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
        num_string = ''.join(random.choices(string.digits, k=num_length))
        debug_print("Numeric string after generation:", num_string)
        special_chars_string = ''.join(random.choices(string.punctuation, k=special_chars_length))
        debug_print("Special characters string after generation:", special_chars_string)
        password = ''.join(word_chars) + extra_char + num_string + special_chars_string
        debug_print("Final password:", password)
        return password


@strict
class SecurePasswordManager:
    def __init__(self, key: bytes = secrets.token_bytes(32), debug: bool = False):
        # The key should be securely generated and stored.
        self._key = key
        self._passwords: Dict[str, str] = {}
        self._temp_buffer: Dict[int, str] = {}

        self.debug = debug

    def debug_print(self, *args):
        if self.debug:
            print(*args)

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
                                         extra_chars: str = '', exclude_chars: str = '', exclude_similar: bool = False,
                                         _recur=False):
        ratios = [letters_ratio, numbers_ratio, punctuations_ratio, unicode_ratio]
        if sum(ratios) != 1:
            raise ValueError("The sum of the ratios must be 1.")
        char_types = [string.ascii_letters, string.digits, string.punctuation,
                      [chr(i) for i in range(0x110000) if unicodedata.category(chr(i)).startswith('P')]]
        char_lengths = [int(length * ratio) for ratio in ratios]
        self.debug_print("Character lengths before adjustment:", char_lengths)
        difference = length - sum(char_lengths)
        for i in range(difference):
            char_lengths[i % len(char_lengths)] += 1
        self.debug_print("Character lengths after adjustment:", char_lengths)
        all_chars = ''
        for i in range(len(char_types)):
            self.debug_print(f"Processing character type {i}: {char_types[i][:50]}"
                             + "..." if len(char_types) > 50 else "")
            if isinstance(char_types[i], str):
                char_type = char_types[i].translate(str.maketrans('', '', exclude_chars))
            else:
                char_type = ''.join([c for c in char_types[i] if c not in exclude_chars])
            self.debug_print(f"Character type {i} after excluding characters: {char_type[:50]}"
                             + "..." if len(char_types) > 50 else "")
            if char_lengths[i] > 0:
                generated_chars = ''.join(secrets.choice(char_type) for _ in range(char_lengths[i]))
                self.debug_print(f"Generated characters for character type {i}: {generated_chars}")
                all_chars += generated_chars
        self.debug_print("All characters before adding extra characters:", all_chars)
        all_chars += extra_chars
        all_chars_lst = list(all_chars)
        if exclude_similar:
            similar_chars = 'Il1O0'  # Add more similar characters if needed
            all_chars_lst = [c for c in all_chars_lst if c not in similar_chars]
            while len(all_chars_lst) < length and not _recur:
                all_chars_lst.extend(self.generate_ratio_based_password_v2(length, letters_ratio, numbers_ratio,
                                                                           punctuations_ratio, unicode_ratio,
                                                                           extra_chars, exclude_chars, exclude_similar,
                                                                           _recur=True))
        secrets.SystemRandom().shuffle(all_chars_lst)
        self.debug_print("All characters after processing:", all_chars_lst)
        if length > len(all_chars_lst) and not _recur:
            raise ValueError("Password length is greater than the number of available characters.")
        password = ''.join(all_chars_lst[:length])
        return password

    def generate_sentence_based_password_v2(self, sentence: str, shuffle_words: bool = True,
                                            shuffle_characters: bool = True, repeat_words: bool = False):
        words = sentence.split(' ')
        sys_random = secrets.SystemRandom()
        if len(words) < 2:
            print("Error: Input must have more than one word.")
            return None
        password = ""
        if shuffle_words:
            self.debug_print("Words before shuffling", words)
            sys_random.shuffle(words)
            self.debug_print("Words after shuffling", words)
        used_words = set()
        for word in words:
            if not repeat_words and word in used_words:
                self.debug_print("Ignoring repeated word")
                continue
            if shuffle_characters:
                self.debug_print("Word before shuffling", list(word))
                word_chars = list(word)
                sys_random.shuffle(word_chars)
                word = "".join(word_chars)
                self.debug_print("Word after shuffling", word)
            password += word
            used_words.add(word)
            self.debug_print("Used Words", used_words)
            self.debug_print("Words", words)
        return password

    def generate_custom_sentence_based_password_v2(self, sentence: str,
                                                   char_position: Union[Literal["random", "keep"], int] = 'random',
                                                   random_case: bool = False, extra_char: str = '', num_length: int = 0,
                                                   special_chars_length: int = 0):
        words = sentence.split(' ')
        word_chars = []
        sys_random = secrets.SystemRandom()
        for word in words:
            if char_position == 'random':
                index = sys_random.randint(0, len(word) - 1)
            elif char_position == 'keep':
                index = 0
            elif type(char_position) is int:
                index = min(char_position, len(word) - 1)
            else:
                return "Invalid char_position."
            char = word[index]
            if random_case:
                char = char.lower() if sys_random.random() < 0.5 else char.upper()
            word_chars.append(char)
            self.debug_print("Word characters after processing:", word_chars)
        num_string = ''.join(sys_random.choices(string.digits, k=num_length))
        self.debug_print("Numeric string after generation:", num_string)
        special_chars_string = ''.join(sys_random.choices(string.punctuation, k=special_chars_length))
        self.debug_print("Special characters string after generation:", special_chars_string)
        password = ''.join(word_chars) + extra_char + num_string + special_chars_string
        self.debug_print("Final password:", password)
        return password


if __name__ == "__main__":
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
