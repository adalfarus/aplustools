import unicodedata
import secrets
import sqlite3
import random
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA512
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes
from Crypto.Random.random import sample
import base64
import string
from rich.console import Console
from rich import print
import os

console = Console()
error_console = Console(stderr=True, style="bold red")

class CryptUtils:
    @staticmethod
    def pbkdf2(password, salt, length, cycles):
        key = PBKDF2(password.encode(), salt.encode(), length, count=cycles, hmac_hash_module=SHA512)
        return key

    @staticmethod
    def generate_salt(length):
        salt = ''.join(sample(string.ascii_lowercase + string.digits, k=length))
        return salt

    @staticmethod
    def aes_encrypt(data, key):
        iv = get_random_bytes(12)
        cipher = AES.new(key, AES.MODE_GCM, iv)
        ciphertext, tag = cipher.encrypt_and_digest(data.encode())
        return iv, ciphertext, tag

    @staticmethod
    def aes_decrypt(iv, ciphertext, tag, key):
        cipher = AES.new(key, AES.MODE_GCM, iv)
        try:
            plaintext = cipher.decrypt_and_verify(ciphertext, tag)
            return plaintext.decode()
        except ValueError:
            print("AES Decryption Error: MAC check failed")
            return None

    @staticmethod
    def generate_hash(message):
        hashed_message = SHA256.new(data=message.encode()).hexdigest()
        return hashed_message

    @staticmethod
    def caesar_cipher(intext, shift):
        outtext = ""
        for i in range(len(intext)):
            temp = ord(intext[i]) + shift
            if temp > 122:
                temp_diff = temp - 122
                temp = 96 + temp_diff
            elif temp < 97:
                temp_diff = 97 - temp
                temp = 123 - temp_diff
            outtext += chr(temp)
        return outtext

    @staticmethod
    def vigenere_cipher(text, keyword, encrypt=True):
        key = list(keyword)
        if len(text) == len(key):
            key = key
        else:
            for i in range(len(text) - len(key)):
                key.append(key[i % len(key)])
        key = "".join(key)
        if encrypt=="True":
            outtext = []
            for i in range(len(text)):
                x = (ord(text[i]) + ord(key[i])) % 26
                x += ord('A')
                outtext.append(chr(x))
            outtext = "".join(outtext)
        elif encrypt=="False":
            outtext = []
            for i in range(len(text)):
                x = (ord(text[i]) - ord(key[i]) + 26) % 26
                x += ord('A')
                outtext.append(chr(x))
            outtext = "".join(outtext)
        else:
            outtext = ""
            print("Encrypt can only be True or False")
        return outtext

class Database:
    def __init__(self):
        pass

    def database_config(self, db_file, config):
        h_mp = config['default_mp']
        salt = config['default_salt']
        keys = list(config.keys())
        values = list(config.values())
        db = self.connect_to_database(db_file)
        c = db.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS secrets (masterkey_hash TEXT NOT NULL, salt TEXT NOT NULL)')
        c.execute('CREATE TABLE IF NOT EXISTS passwords (ID INTEGER PRIMARY KEY AUTOINCREMENT, ACCOUNT TEXT NOT NULL, USERNAME TEXT NOT NULL, PASSWORD TEXT NOT NULL, IV_ACCOUNT BLOB NOT NULL, IV_USERNAME BLOB NOT NULL, IV_PASSWORD BLOB NOT NULL, TAG_ACCOUNT BLOB NOT NULL, TAG_USERNAME BLOB NOT NULL, TAG_PASSWORD BLOB NOT NULL)')
        c.execute('CREATE TABLE IF NOT EXISTS settings (setting_id TEXT PRIMARY KEY, setting_value TEXT NOT NULL)')
        c.execute('INSERT INTO secrets (masterkey_hash, salt) values (?, ?)', (h_mp, salt))
        for key, value in zip(keys, values):
            c.execute('INSERT INTO settings (setting_id, setting_value) values (?, ?)', (key, value))
        db.commit()
        db.close()

    @staticmethod
    def connect_to_database(database_file):
        try:
            db = sqlite3.connect(database_file)
        except Exception as e:
            print("SQLite3 Error:", e)
            console.print_exception(show_locals=True)
        return db

    def encrypt_all_data(self, database_file, key):
        x = '1'
        try:
            with self.connect_to_database(database_file) as db:
                db.row_factory = sqlite3.Row
                cursor = db.cursor()
                cursor.execute('SELECT * FROM passwords')
                rows = cursor.fetchall()
                for row in rows:
                    id = row['ID']
                    account = row['ACCOUNT']
                    username = row['USERNAME']
                    password = row['PASSWORD']
                    iv_account, encrypted_account, tag_account = CryptUtils.aes_encrypt(account, key)
                    iv_username, encrypted_username, tag_username = CryptUtils.aes_encrypt(username, key)
                    iv_password, encrypted_password, tag_password = CryptUtils.aes_encrypt(password, key)
                    cursor.execute('UPDATE passwords SET ACCOUNT = ?, USERNAME = ?, PASSWORD = ?, IV_ACCOUNT = ?, IV_USERNAME = ?, IV_PASSWORD = ?, TAG_ACCOUNT = ?, TAG_USERNAME = ?, TAG_PASSWORD = ? WHERE ID = ?', (encrypted_account, encrypted_username, encrypted_password, iv_account, iv_username, iv_password, tag_account, tag_username, tag_password, id))
                db.commit()
        except Exception as e:
            print("SQLite3 Error:", e)
            console.print_exception(show_locals=True)
            x = 'a'
        return x.isnumeric()

    def decrypt_all_data(self, database_file, key):
        x = 'a'
        try:
            with self.connect_to_database(database_file) as db:
                db.row_factory = sqlite3.Row
                cursor = db.cursor()
                cursor.execute('SELECT * FROM passwords')
                rows = cursor.fetchall()
                for row in rows:
                    id = row['ID']
                    encrypted_account = row['ACCOUNT']
                    encrypted_username = row['USERNAME']
                    encrypted_password = row['PASSWORD']
                    iv_account = row['IV_ACCOUNT']
                    iv_username = row['IV_USERNAME']
                    iv_password = row['IV_PASSWORD']
                    tag_account = row['TAG_ACCOUNT']
                    tag_username = row['TAG_USERNAME']
                    tag_password = row['TAG_PASSWORD']
                    decrypted_account = CryptUtils.aes_decrypt(iv_account, encrypted_account, tag_account, key)
                    decrypted_username = CryptUtils.aes_decrypt(iv_username, encrypted_username, tag_username, key)
                    decrypted_password = CryptUtils.aes_decrypt(iv_password, encrypted_password, tag_password, key)
                    cursor.execute('UPDATE passwords SET ACCOUNT = ?, USERNAME = ?, PASSWORD = ? WHERE ID = ?', (decrypted_account, decrypted_username, decrypted_password, id))
                db.commit()
        except Exception as e:
            print("SQLite3 Error:", e)
            console.print_exception(show_locals=True)
            x = '1'
        return x.isnumeric()

    def is_database_encrypted(self, database_file):
        try:
            db = self.connect_to_database(database_file)
            cursor = db.cursor()
            cursor.execute('SELECT COUNT(*) FROM sqlite_master')
            cursor.close()
            db.close()
            return False
        except sqlite3.DatabaseError:
            return True

    def is_data_encrypted(self, database_file):
        try:
            db = self.connect_to_database(database_file)
            cursor = db.cursor()
            cursor.execute('SELECT ACCOUNT FROM passwords LIMIT 1')
            account = cursor.fetchone()
            cursor.close()
            db.close()

            if account:
                # Check if the data appears to be encrypted (e.g., contains non-printable characters)
                return not all(char in string.printable for char in account[0])
            else:
                # The table is empty, so it's unclear if the data is encrypted or not
                return False
        except sqlite3.DatabaseError:
            return False

    def check_database_simple(self, database_file):
        if os.path.exists(database_file):
            try:
                db = self.connect_to_database(database_file)
                db.close()
                return True
            except sqlite3.Error:
                return False
        else:
            return False

    def check_database_simple_out(self, database_file):
        if os.path.exists(database_file):
            try:
                db = self.connect_to_database(database_file)
                db.close()
                print("Database", database_file, "exists.")
            except sqlite3.Error:
                print("SQLite3 Error: Unable to connect to database", database_file,".")
        else:
            print("Database", database_file, "does not exist.")
        return ""

    @staticmethod
    def check_database_integrity(database_file):
        try:
            conn = sqlite3.connect(database_file)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            conn.close()

            if result[0] == "ok":
                print("Database", database_file, "is not corrupted.")
            else:
                print("Database", database_file, "is corrupted.")
        except Exception as e:
            print("SQLite3 Error:", e)
            console.print_exception(show_locals=True)
        return ""

    @staticmethod
    def check_database_complex_output(database_file):
        if os.path.exists(database_file):
            try:
                conn = sqlite3.connect(database_file)
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()
                conn.close()

                if result[0] == "ok":
                    print("Database", database_file, "exists and is not corrupted.")
                else:
                    print("Database", database_file, "exists but is corrupted.")
            except Exception as e:
                print("SQLite3 Error:", e)
        else:
            print("Database", database_file, "does not exist.")

class GeneratePasswords:
    def __init__(self, debug=False):
        self.debug = debug

    def debug_print(self, *args):
        if self.debug:
            print(*args)

    @staticmethod
    def generate_ratio_based_password_v1(length=16, debug=False, letters_ratio=0.5, numbers_ratio=0.3, punctuations_ratio=0.2, unicode_ratio=0, extra_chars='', exclude_chars=''):
        def debug_print(*args):
            if debug:
                print(*args)
        ratios = [letters_ratio, numbers_ratio, punctuations_ratio, unicode_ratio]
        if sum(ratios) != 1:
            raise ValueError("The sum of the ratios must be 1.")
        char_types = [string.ascii_letters, string.digits, string.punctuation, [chr(i) for i in range(0x110000) if unicodedata.category(chr(i)).startswith('P')]]
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

    def generate_ratio_based_password_v2(self, length=16, letters_ratio=0.5, numbers_ratio=0.3, punctuations_ratio=0.2, unicode_ratio=0, extra_chars='', exclude_chars='', secure_random=False, exclude_similar=False):
        ratios = [letters_ratio, numbers_ratio, punctuations_ratio, unicode_ratio]
        if sum(ratios) != 1:
            raise ValueError("The sum of the ratios must be 1.")
        char_types = [string.ascii_letters, string.digits, string.punctuation, [chr(i) for i in range(0x110000) if unicodedata.category(chr(i)).startswith('P')]]
        char_lengths = [int(length * ratio) for ratio in ratios]
        self.debug_print("Character lengths before adjustment:", char_lengths)
        difference = length - sum(char_lengths)
        for i in range(difference):
            char_lengths[i % len(char_lengths)] += 1
        self.debug_print("Character lengths after adjustment:", char_lengths)
        all_chars = ''
        for i in range(len(char_types)):
            self.debug_print(f"Processing character type {i}: {char_types[i][:50]}...")
            if isinstance(char_types[i], str):
                char_type = char_types[i].translate(str.maketrans('', '', exclude_chars))
            else:
                char_type = ''.join([c for c in char_types[i] if c not in exclude_chars])
            self.debug_print(f"Character type {i} after excluding characters: {char_type[:50]}...")
            if char_lengths[i] > 0:
                if secure_random:
                    generated_chars = ''.join(secrets.choice(char_type) for _ in range(char_lengths[i]))  # Use secrets.choice for secure random
                else:
                    generated_chars = ''.join(random.choices(char_type, k=char_lengths[i]))
                self.debug_print(f"Generated characters for character type {i}: {generated_chars}")
                all_chars += generated_chars
        self.debug_print("All characters before adding extra characters:", all_chars)
        all_chars += extra_chars
        all_chars = list(all_chars)
        if exclude_similar:
            similar_chars = 'Il1O0'  # Add more similar characters if needed
            all_chars = [c for c in all_chars if c not in similar_chars]
        random.shuffle(all_chars)
        self.debug_print("All characters after processing:", all_chars)
        if length > len(all_chars):
            raise ValueError("Password length is greater than the number of available characters.")
        password = ''.join(all_chars[:length])
        return password

    @staticmethod
    def generate_sentence_based_password_v1(sentence, debug=False, shuffle_words=True, shuffle_characters=True, repeat_words=False):
        def debug_print(*args):
            if debug:
                print(*args)
        words = sentence.split(' ')
        if len(words) < 2:
            print("Error: Input must have more than one word.")
            return None
        password = ""
        if shuffle_words:
            debug_print("Words before shuffeling", words)
            random.shuffle(words)
            debug_print("Words after shuffeling", words)
        used_words = set()
        for word in words:
            if not repeat_words and word in used_words:
                debug_print("Ignoring repeated word")
                continue
            if shuffle_characters:
                debug_print("Word before shuffeling", list(word))
                word_chars = list(word)
                random.shuffle(word_chars)
                word = "".join(word_chars)
                debug_print("Word after shuffeling", word)
            password += word
            used_words.add(word)
            debug_print("Used Words", used_words)
            debug_print("Words", words)
        return password

    def generate_sentence_based_password_v2(self, sentence, shuffle_words=True, shuffle_characters=True, repeat_words=False):
        words = sentence.split(' ')
        if len(words) < 2:
            print("Error: Input must have more than one word.")
            return None
        password = ""
        if shuffle_words:
            self.debug_print("Words before shuffling", words)
            random.shuffle(words)
            self.debug_print("Words after shuffling", words)
        used_words = set()
        for word in words:
            if not repeat_words and word in used_words:
                self.debug_print("Ignoring repeated word")
                continue
            if shuffle_characters:
                self.debug_print("Word before shuffling", list(word))
                word_chars = list(word)
                random.shuffle(word_chars)
                word = "".join(word_chars)
                self.debug_print("Word after shuffling", word)
            password += word
            used_words.add(word)
            self.debug_print("Used Words", used_words)
            self.debug_print("Words", words)
        return password

    @staticmethod
    def generate_custom_sentence_based_password_v1(sentence, debug=False, char_position='random', random_case=False, extra_char='', num_length=0, special_chars_length=0):
        def debug_print(*args):
            if debug:
                print(*args)
        words = sentence.split(' ')
        word_chars = []
        for word in words:
            if char_position == 'random':
                index = random.randint(0, len(word) - 1)
            else:
                index = min(char_position, len(word) - 1)
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

    def generate_custom_sentence_based_password_v2(self, sentence, char_position='random', random_case=False, extra_char='', num_length=0, special_chars_length=0):
        words = sentence.split(' ')
        word_chars = []
        for word in words:
            if char_position == 'random':
                index = random.randint(0, len(word) - 1)
            else:
                index = min(char_position, len(word) - 1)
            char = word[index]
            if random_case:
                char = char.lower() if random.random() < 0.5 else char.upper()
            word_chars.append(char)
            self.debug_print("Word characters after processing:", word_chars)
        num_string = ''.join(random.choices(string.digits, k=num_length))
        self.debug_print("Numeric string after generation:", num_string)
        special_chars_string = ''.join(random.choices(string.punctuation, k=special_chars_length))
        self.debug_print("Special characters string after generation:", special_chars_string)
        password = ''.join(word_chars) + extra_char + num_string + special_chars_string
        self.debug_print("Final password:", password)
        return password

class PasswordManager:
    def __init__(self, db):
        self.db = db

    def add_password(self):
        account = input("Enter account name: ")
        username = input("Enter username: ")
        password = input("Enter password: ")
        placeholder_iv = b''
        placeholder_tag = b''
        self.db.execute("INSERT INTO passwords (ACCOUNT, USERNAME, PASSWORD, IV_ACCOUNT, IV_USERNAME, IV_PASSWORD, TAG_ACCOUNT, TAG_USERNAME, TAG_PASSWORD) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (account, username, password, placeholder_iv, placeholder_iv, placeholder_iv, placeholder_tag, placeholder_tag, placeholder_tag))
        self.db.commit()
        print("Password added successfully!")

    def view_passwords(self):
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM passwords")
        rows = cursor.fetchall()
        columns = ["ID", "Account", "Username", "Password"]
        decoded_rows = [[r.decode('raw_unicode_escape') if isinstance(r, bytes) else str(r) for r in row] for row in rows]
        width = [max(len(c), max(len(str(r[i])) for r in decoded_rows)) for i, c in enumerate(columns)]
        print("ID".ljust(width[0]), "Account".ljust(width[1]), "Username".ljust(width[2]), "Password".ljust(width[3]), sep="   ")
        print("=" * sum(width))# + 4))
        for row in decoded_rows:
            print(str(row[0]).ljust(width[0]), str(row[1]).ljust(width[1]), str(row[2]).ljust(width[2]), str(row[3]).ljust(width[3]), sep="   ")
        print("=" * sum(width))# + 4))
    '''    print("=" * (width[0]-1), "|", "=" * (width[1]-1), "|", "=" * (width[2]-1), "|", "=" * width[3])'''

    def update_password(self):
        password_id = input("Enter password ID to update: ")
        account = input("Enter new account name: ")
        username = input("Enter new username: ")
        password = input("Enter new password: ")
        self.db.execute('UPDATE passwords SET ACCOUNT=?, USERNAME=?, PASSWORD=? WHERE ID=?', (account, username, password, password_id))
        self.db.commit()
        print("Password updated successfully!")

    def delete_password(self):
        password_id = input("Enter password ID to delete: ")
        self.db.execute('DELETE from passwords WHERE ID=?', (password_id,))
        self.db.commit()
        print("Password deleted successfully!")

### GeneratePasswords Class Documentation
##
##The `GeneratePasswords` class provides several methods for generating passwords. The class is initialized with an optional `debug` parameter that, when set to `True`, enables debug print statements in the methods.
##
#### Methods
##
##### generate_ratio_based_password_v1
##
##This method generates a password based on specified ratios of different character types. The password is composed of letters, numbers, punctuation, and unicode characters. The ratios of these character types in the password are determined by the parameters. This method has its own debug print statements that are independent of the `debug` attribute of the class.
##
##Parameters:
##
##- `length`: The length of the password to generate.
##- `letters_ratio`: The ratio of letters in the password.
##- `numbers_ratio`: The ratio of numbers in the password.
##- `punctuations_ratio`: The ratio of punctuation characters in the password.
##- `unicode_ratio`: The ratio of unicode characters in the password.
##- `extra_chars`: Additional characters to include in the password.
##- `exclude_chars`: Characters to exclude from the password.
##
##### generate_ratio_based_password_v2
##
##This method is similar to `generate_ratio_based_password_v1`, but it includes additional parameters for secure random generation and excluding similar characters. This method uses the `debug_print` method of the class for debug print statements.
##
##Parameters:
##
##- `length`: The length of the password to generate.
##- `letters_ratio`: The ratio of letters in the password.
##- `numbers_ratio`: The ratio of numbers in the password.
##- `punctuations_ratio`: The ratio of punctuation characters in the password.
##- `unicode_ratio`: The ratio of unicode characters in the password.
##- `extra_chars`: Additional characters to include in the password.
##- `exclude_chars`: Characters to exclude from the password.
##- `secure_random`: Whether to use a secure method for random generation.
##- `exclude_similar`: Whether to exclude similar characters.
##
##### generate_sentence_based_password_v1
##
##This method generates a password based on a sentence, with options to shuffle the words and characters. The password is composed of words from the sentence, and the words and characters can be shuffled to increase randomness. This method has its own debug print statements that are independent of the `debug` attribute of the class.
##
##Parameters:
##
##- `sentence`: The sentence to use for password generation.
##- `shuffle_words`: Whether to shuffle the words in the sentence.
##- `shuffle_characters`: Whether to shuffle the characters in each word.
##- `repeat_words`: Whether to allow repeated words in the password.
##
##### generate_sentence_based_password_v2
##
##This method is similar to `generate_sentence_based_password_v1`, but it uses the `debug_print` method of the class for debug print statements.
##
##Parameters:
##
##- `sentence`: The sentence to use for password generation.
##- `shuffle_words`: Whether to shuffle the words in the sentence.
##- `shuffle_characters`: Whether to shuffle the characters in each word.
##- `repeat_words`: Whether to allow repeated words in the password.
##
##### generate_custom_sentence_based_password_v1
##
##This method generates a password based on a sentence, with options to choose a character from each word and add extra characters. The password is composed of chosen characters from each word in the sentence, and additional numeric and special characters can be added to the password. This method has its own debug print statements that are independent of the `debug` attribute of the class.
##
##Parameters:
##
##- `sentence`: The sentence to use for password generation.
##- `char_position`: The position of the character to choose from each word.
##- `random_case`: Whether to randomize the case of the chosen characters.
##- `extra_char`: An extra character to add to the password.
##- `num_length`: The number of numeric characters to add to the password
##
##### generate_custom_sentence_based_password_v2
##
##This method is similar to `generate_custom_sentence_based_password_v1`, but it uses the `debug_print` method of the class for debug print statements.
##
##Parameters:
##
##- `sentence`: The sentence to use for password generation.
##- `char_position`: The position of the character to choose from each word.
##- `random_case`: Whether to randomize the case of the chosen characters.
##- `extra_char`: An extra character to add to the password.
##- `num_length`: The number of numeric characters to add to the password.
##- `special_chars_length`: The number of special characters to add to the password.
##
#### Example Usage
##
##```python
##gen = GeneratePasswords(debug=True)
##
### Generate a ratio-based password
##password = gen.generate_ratio_based_password_v1(length=10, letters_ratio=0.5, numbers_ratio=0.3, punctuations_ratio=0.2, debug=True)
##print(password)
##
### Generate a sentence-based password
##password = gen.generate_sentence_based_password_v1(sentence="This is a test sentence", shuffle_words=True, shuffle_characters=True, repeat_words=False)
##print(password)
##
### Generate a custom sentence-based password
##password = gen.generate_custom_sentence_based_password_v1(sentence="This is a test sentence", char_position='random', random_case=True, extra_char='!', num_length=2, special_chars_length=2)
##print(password)
##```
##
##In the example, `debug=True` is passed to `generate_ratio_based_password_v1`, so this method prints debug information even though `debug=False` is set when initializing the `GeneratePasswords` class. The other methods do not print debug information because the `debug` attribute of the class is `False`.

def local_test():
    try:
        gen = GeneratePasswords(debug=True) # Exclude similar makes generated char length potentially smaller than pass length as it removes after generating
        password = gen.generate_ratio_based_password_v2(length=10, letters_ratio=0.5, numbers_ratio=0.3, punctuations_ratio=0.2, secure_random=True)#, exclude_similar=True)
        print(password) # Make the ... if based
    except Exception as e:
        print(f"Exception occurred {e}.")
        return False
    else:
        print("Test completed successfully.")
        return True

if __name__ == "__main__":
    local_test()
