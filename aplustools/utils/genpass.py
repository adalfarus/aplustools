from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
from aplustools.io.environment import strict, auto_repr
from aplustools.data import nice_number
import json
import os
import base64
import time
import struct
import datetime
from typing import Tuple, List, Literal, Optional, Union, Dict, Any, Callable
import threading
import re
import errno
import socket
import unicodedata
import secrets
import string
import random
from enum import Enum
import math


class PortUtils:
    @staticmethod
    def find_available_port():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))  # Bind to an available port provided by the OS
            return s.getsockname()[1]  # Return the allocated port

    @staticmethod
    def find_available_port_range(start_port, end_port):
        for port in range(start_port, end_port + 1):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
                    return port  # Port is available
            except OSError as e:
                if e.errno == errno.EADDRINUSE:  # Port is already in use
                    continue
                raise  # Reraise unexpected errors
        raise RuntimeError("No available ports in the specified range")

    @staticmethod
    def test_port(port, retries=5, delay=1):
        while retries > 0:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
                    return port
            except OSError as e:
                if e.errno == errno.EADDRINUSE:
                    retries -= 1
                    time.sleep(delay)
                else:
                    raise
        raise RuntimeError("Port is still in use after several retries")


class CryptUtils:
    @staticmethod
    def pbkdf2(password: str, salt: bytes, length: int, cycles: int) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA512(),
            length=length,
            salt=salt,
            iterations=cycles,
            backend=default_backend()
        )
        key = kdf.derive(password.encode())
        return key

    @staticmethod
    def generate_salt(length: int) -> bytes:
        # Generate a cryptographically secure salt
        return os.urandom(length)

    @staticmethod
    def generate_aes_key(length: Literal[128, 192, 256]) -> bytes:
        return os.urandom(length // 8)

    @staticmethod
    def pack_ae_data(iv: bytes, encrypted_data: bytes, tag: bytes) -> bytes:
        iv_len_encoded = len(iv).to_bytes(1, "big")  # Maximum length of 128
        tag_len_encoded = len(tag).to_bytes(1, "big")  # Maximum length of 128
        return iv_len_encoded + iv + tag_len_encoded + tag + encrypted_data

    @staticmethod
    def unpack_ae_data(data: bytes):
        iv_len = int.from_bytes(data[:1])

        iv_start = 1
        iv_end = iv_start + iv_len
        iv = data[iv_start:iv_end]

        tag_len = int.from_bytes(data[iv_end:iv_end+1])
        tag_start = iv_end+1
        tag_end = tag_start + tag_len
        tag = data[tag_start:tag_end]

        encrypted_data = data[tag_end:]
        return iv, encrypted_data, tag

    @staticmethod
    def aes_encrypt(data: bytes, key: bytes) -> Tuple[bytes, bytes, bytes]:
        iv = os.urandom(12)  # Generate IV securely
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        return iv, ciphertext, encryptor.tag

    @staticmethod
    def aes_decrypt(iv: bytes, encrypted_data: bytes, tag: bytes, key: bytes) -> Optional[bytes]:
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        try:
            return decryptor.update(encrypted_data) + decryptor.finalize()
        except ValueError:
            print("AES Decryption Error: MAC check failed")
            return None

    @staticmethod
    def generate_des_key(length: Literal[64, 128, 192]) -> bytes:
        return os.urandom(length // 8)

    @staticmethod
    def des_encrypt(data: bytes, key: bytes) -> tuple:
        iv = os.urandom(8)
        cipher = Cipher(algorithms.TripleDES(key), modes.CFB(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        return iv, ciphertext, b''  # DES doesn't use a tag in this mode

    @staticmethod
    def des_decrypt(iv: bytes, ciphertext: bytes, tag: bytes, key: bytes) -> bytes:
        cipher = Cipher(algorithms.TripleDES(key), modes.CFB(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()

    @staticmethod
    def generate_rsa_key(length: Literal[1024, 2048, 4096]) -> Tuple[bytes, bytes]:
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=length,
            backend=default_backend()
        )
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption())
        return private_bytes, private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo)

    @staticmethod
    def load_private_key(private_bytes: bytes) -> rsa.RSAPrivateKey:
        return serialization.load_pem_private_key(
            private_bytes,
            password=None,
            backend=default_backend()
        )

    @staticmethod
    def load_public_key(public_bytes: bytes) -> rsa.RSAPublicKey:
        return serialization.load_pem_public_key(
            public_bytes,
            backend=default_backend()
        )

    @staticmethod
    def rsa_encrypt(data: bytes, public_key: rsa.RSAPublicKey) -> bytes:
        try:
            return public_key.encrypt(
                data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
        except ValueError:
            print("ValueError, remember that RSA can only encrypt something shorter than it's key. Otherwise you should"
                  "use hybrid encryption, so encrypt with e.g. AES and then encrypt the aes key with rsa.")

    @staticmethod
    def rsa_decrypt(encrypted_data: bytes, private_key: rsa.RSAPrivateKey) -> bytes:
        return private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    @staticmethod
    def generate_hash(message: str) -> str:
        digest = hashes.Hash(hashes.SHA512(), backend=default_backend())
        digest.update(message.encode())
        return digest.finalize().hex()

    @staticmethod
    def caesar_cipher(data: str, shift: int) -> str:
        output = ""
        for i in range(len(data)):
            temp = ord(data[i]) + shift
            if temp > 122:
                temp_diff = temp - 122
                temp = 96 + temp_diff
            elif temp < 97:
                temp_diff = 97 - temp
                temp = 123 - temp_diff
            output += chr(temp)
        return output


class DummyProtocol:
    @staticmethod
    def get_exec_code_delimiters(self) -> tuple:
        return "", ""

    @staticmethod
    def get_control_code(self, control_code: str, add_in: Optional[str] = None) -> str:
        return control_code + add_in

    @staticmethod
    def validate_control_code(self, exec_code: str) -> str:
        return exec_code


@strict
class ControlCodeProtocol:
    def __init__(self, comm_code: Optional[str] = None, exec_code_delimiter: str = "::", exec_code_start: str = "[",
                 exec_code_end: str = "]", control_codes: Optional[dict] = None):
        self._comm_code = comm_code
        if not self._comm_code:
            self._comm_code = self._generate_random_string(50)
        self._exec_code_delimiter = exec_code_delimiter
        self._exec_code_start = exec_code_start
        self._exec_code_end = exec_code_end
        self._control_codes = control_codes if control_codes is not None else {
            "end": "NEWLINE", "shutdown": "SHUTDOWN 0xC000013A", "input": "IN"
        }

    def get_exec_code_delimiters(self) -> tuple:
        return self._exec_code_start, self._exec_code_end

    @staticmethod
    def _generate_random_string(length):
        # Calculate how many bytes are needed to get the desired string length after Base64 encoding
        bytes_length = (length * 3) // 4
        random_bytes = os.urandom(bytes_length)

        # Encode these bytes into a Base64 string
        random_string_base64 = base64.urlsafe_b64encode(random_bytes).decode('utf-8')

        # Return the required length
        return random_string_base64[:length]

    def get_control_code(self, control_code: str, add_in: Optional[str] = None) -> str:
        add_in_str = f"{self._exec_code_delimiter}{add_in}" if add_in else ""
        return (f"{self._exec_code_start}"
                f"{self._comm_code}{self._exec_code_delimiter}{self._control_codes.get(control_code.lower())}"
                f"{add_in_str}{self._exec_code_end}")

    def validate_control_code(self, exec_code: str) -> Tuple[str, Optional[str]]:
        if exec_code.startswith(self._exec_code_start) and exec_code.endswith(self._exec_code_end):
            # Remove the start and end markers
            plain_code = exec_code[len(self._exec_code_start):-len(self._exec_code_end)]

            shipped_code = plain_code[:len(self._comm_code)]
            if shipped_code == self._comm_code:
                rest = plain_code[len(self._comm_code) + len(self._exec_code_delimiter):].split(
                    self._exec_code_delimiter, 1) + [None]
                control_code, add_in = rest[:2]
                for key, value in self._control_codes.items():
                    if control_code == value:
                        return key, add_in
                return "Invalid control code", None
            return "Invalid key", None
        else:
            # Raise an error if the string does not have the required start and end markers
            raise ValueError("String does not start and end with required markers")

    def serialize(self):
        return json.dumps({
            "comm_code": self._comm_code,
            "exec_delimiter": self._exec_code_delimiter,
            "exc_code_start": self._exec_code_start,
            "exc_code_end": self._exec_code_end,
            "status_codes": self._control_codes
        })

    @staticmethod
    def deserialize(serialized_data):
        data = json.loads(serialized_data)
        return ControlCodeProtocol(data["comm_code"], data["exec_delimiter"], data["exc_code_start"], data["exc_code_end"], data["status_codes"])


class _ControlCode:
    def __init__(self, control_code: str, add_in: str):
        self.code = control_code
        self.add = add_in

    def __repr__(self):
        return f"ControlCode(code={self.code}, add={self.add})"


@auto_repr
class UndefinedSocket:
    """Is either an uninitialized socket or an already connected one."""
    def __init__(self, conn: Union[Tuple[str, int], socket.socket]):
        self.conn = conn


@strict
class SecureSocketServer:
    def __init__(self, connection: UndefinedSocket, protocol: ControlCodeProtocol, _chunk_size=1024, private_key_bytes_overwrite=None):
        self._last_timestamp = datetime.datetime.now()
        self.rate_limit = 10  # Allow 10 messages per second

        self._connection = None
        self._undef_socket = connection.conn

        if isinstance(self._undef_socket, socket.socket):
            self._connection = self._undef_socket
            self._undef_socket = self._connection.getpeername()

        self._decoder = MessageDecoder(protocol, _chunk_size, private_key_bytes_overwrite)
        self._encoder = None
        self._protocol = protocol
        self._chunk_size = _chunk_size

        self._key_exchange_done = False
        self._comm_thread = None

    def is_setup(self):
        return self._connection is not None

    def is_fully_setup(self):
        return self._key_exchange_done

    def is_shutdown(self):
        return self._connection is None

    def get_host(self):
        return self._undef_socket[0]

    def get_port(self):
        return self._undef_socket[1]

    def get_socket(self):
        return UndefinedSocket(self._undef_socket)

    def get_connected_socket(self):
        if self._connection is not None:
            return UndefinedSocket(self._connection)
        raise ValueError("Server unconnected")

    def _setup_connection(self):
        while not isinstance(self._connection, socket.socket):
            try:
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.bind(self._undef_socket)
                server_socket.listen(1)

                self._connection, addr = server_socket.accept()
            except Exception as e:
                print(f"Error setting up connection: {e}. Retrying in 5 seconds ...")
                self._connection = None  # Making sure no faulty socket gets trough
                time.sleep(5)

    def _send_public_key(self):
        while True:
            try:
                self._connection.sendall(self._decoder.get_public_key_bytes())
            except Exception as e:
                print(f"Error sending public key: {e}")
            else:
                break

    def _receive_public_key(self):
        while not self._key_exchange_done and not self._encoder:
            try:
                # Receive client's public key here
                encrypted_client_public_key_bytes = self._connection.recv(739)
                encrypted_aes_key_length = int.from_bytes(encrypted_client_public_key_bytes[:2], "big")
                encrypted_aes_key = encrypted_client_public_key_bytes[2:encrypted_aes_key_length+2]
                aes_key = CryptUtils.rsa_decrypt(encrypted_aes_key, self._decoder.get_private_key())

                rest_data = encrypted_client_public_key_bytes[encrypted_aes_key_length+2:]
                client_public_key_bytes = CryptUtils.aes_decrypt(*CryptUtils.unpack_ae_data(rest_data), key=aes_key)

                self._encoder = MessageEncoder(self._protocol, client_public_key_bytes, self._chunk_size)
                self._key_exchange_done = True
            except Exception as e:
                print(f"Error receiving public key: {e}")
                self._key_exchange_done = False
                self._encoder = None

    def _check_rate_limit(self):
        current_time = datetime.datetime.now()
        if (current_time - self._last_timestamp).total_seconds() > self.rate_limit:
            return False
        self._last_timestamp = current_time
        return True

    def _listen_for_messages(self):
        while self._connection is not None:
            try:
                try:
                    encrypted_chunk = self._connection.recv(self._chunk_size)
                except socket.error as e:
                    if e.errno == 10054:
                        print("Connection was forcibly closed by the remote host")
                        self.close_connection()
                        break
                    else:
                        raise e

                if not encrypted_chunk:
                    break

                # Check rate limiting
                if not self._check_rate_limit():
                    raise Exception("Rate limit exceeded")

                self._decoder.add_chunk(encrypted_chunk)
                chunks = self._decoder.get_complete()

                for chunk in chunks:
                    if type(chunk) is str:
                        print(chunk, end="")
                    elif chunk.code == "end":
                        print("\n", end="")
                    elif chunk.code == "shutdown":
                        print("Shutting down server")
                        self._cleanup = True
                        break
                    elif chunk.code == "input":
                        inp = input(chunk.add)
                        self._connection.sendall(inp.encode("utf-8"))
            except Exception as e:
                if not self._cleanup:
                    print(f"Error in SSS._listen_for_messages: {e}")
                    self.close_connection()

    def _receive_public_key_and_start_communication(self):
        try:
            self._receive_public_key()
            self._listen_for_messages()
        except Exception as e:
            print(f"Error in _receive_public_key_and_start_communication: {e}")

    def startup(self, start_in_new_thread: bool = True):
        self._setup_connection()
        self._send_public_key()

        if start_in_new_thread:
            self._comm_thread = threading.Thread(target=self._receive_public_key_and_start_communication)
            self._comm_thread.start()
        else:
            self._receive_public_key_and_start_communication()

    def shutdown_client(self):
        while not self._encoder or not self._key_exchange_done:
            time.sleep(0.1)

        self._encoder.add_control_message("shutdown")
        chunks = self._encoder.flush()

        for chunk in chunks:
            self._connection.send(chunk)

    def close_connection(self):
        if self._connection:
            self._connection.close()
            self._connection = None
            print("Server connection closed.")

    def cleanup(self):
        self.close_connection()
        if self._comm_thread is not None:
            self._comm_thread.join()

    def __del__(self):
        self.cleanup()


@strict
class SecureSocketClient:
    def __init__(self, protocol, forced_host="127.0.0.1", forced_port=None, _chunk_size=1024, private_key_bytes_overwrite=None):
        self._host = forced_host
        self._port = PortUtils.find_available_port() if not forced_port else forced_port
        self._connection = None
        self._key_exchange_done = False

        self._decoder = MessageDecoder(protocol, _chunk_size, private_key_bytes_overwrite)
        self._encoder = None
        self._protocol = protocol
        self._chunk_size = _chunk_size
        self._comm_thread = None

    def is_setup(self):
        return self._connection is not None

    def is_fully_setup(self):
        return self._key_exchange_done

    def is_shutdown(self):
        return self._connection is None

    def get_host(self):
        return self._host

    def get_port(self):
        return self._port

    def get_socket(self):
        return UndefinedSocket((self._host, self._port))

    def get_connected_socket(self):
        if self._connection is not None:
            return UndefinedSocket(self._connection)
        raise ValueError("Server unconnected")

    def _connect_to_server(self):
        while not isinstance(self._connection, socket.socket):
            try:
                self._connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._connection.connect((self._host, self._port))
            except ConnectionError as e:
                print(f"Connection error: {e}. Retrying in 5 seconds ...")
                self._connection = None  # Making sure no faulty socket gets trough
                time.sleep(5)  # Wait before retrying

    def _receive_public_key(self):
        while not self._encoder:
            try:
                # Receive initial message from the server
                public_key_bytes = self._connection.recv(self._chunk_size)
                self._encoder = MessageEncoder(self._protocol, public_key_bytes, self._chunk_size)
            except Exception as e:
                print(f"Error in _receive_public_key: {e}")
                self._encoder = None

    def _send_public_key(self):
        while not self._key_exchange_done:
            try:
                aes_key = CryptUtils.generate_aes_key(128)
                encrypted_public_key_bytes = CryptUtils.pack_ae_data(*CryptUtils.aes_encrypt(self._decoder.get_public_key_bytes(), aes_key))
                encrypted_aes_key = CryptUtils.rsa_encrypt(aes_key, self._encoder.get_public_key())
                self._connection.send(len(encrypted_aes_key).to_bytes(2, "big") + encrypted_aes_key + encrypted_public_key_bytes)
                self._key_exchange_done = True
            except Exception as e:
                print(f"Error in _send_public_key: {e}")
                self._key_exchange_done = False

    def _listen_for_messages(self):
        while self._connection is not None:
            try:
                if self._connection is None:
                    break

                encrypted_chunk = self._connection.recv(self._chunk_size)
                if not encrypted_chunk:
                    break

                self._decoder.add_chunk(encrypted_chunk)
                chunks = self._decoder.get_complete()

                for chunk in chunks:
                    if type(chunk) is not str and chunk.code == "shutdown":
                        print("Shutting down client")
                        self.close_connection()
                        break  # breaking is equal to a shutdown
            except socket.error as e:
                if e.errno == 10054:
                    print("Connection was forcibly closed by the remote host")
                elif e.errno == 10038:
                    print("Socket is not valid anymore")
                else:
                    print(f"Socket error in SSC._listen_for_messages: {e}")
                self.close_connection()
            except Exception as e:
                print(f"Error in SSC._listen_for_messages: {e}")
                self.close_connection()

    def _connect_and_exchange_keys(self):
        try:
            self._connect_to_server()
            self._receive_public_key()
            self._send_public_key()
            self._listen_for_messages()
        except Exception as e:
            print(f"Error in _connect_and_exchange_keys: {e}.")

    def startup(self, start_in_new_thread: bool = True):
        if start_in_new_thread:
            self._comm_thread = threading.Thread(target=self._connect_and_exchange_keys)
            self._comm_thread.start()
        else:
            self._connect_and_exchange_keys()

    def add_message(self, message):
        while self._encoder is None:
            time.sleep(0.01)
        self._encoder.add_message(message)

    def add_control_code(self, code):
        while self._encoder is None:
            time.sleep(0.01)
        self._encoder.add_control_message(code)

    def sendall(self):
        # Wait until the connection is established
        while self._connection is None or not self._key_exchange_done:
            time.sleep(0.01)  # Wait briefly and check again

        encoded_blocks = self._encoder.flush()
        for block in encoded_blocks:
            self._connection.send(block)

    def close_connection(self):
        if self._connection:
            self._connection.close()
            self._connection = None
            print("Client connection closed.")

    def cleanup(self):
        self.close_connection()
        if self._comm_thread is not None:
            self._comm_thread.join()

    def __del__(self):
        self.cleanup()


@strict
class MessageEncoder:
    def __init__(self, protocol, public_key_bytes, chunk_size=1024):
        self._public_key = serialization.load_pem_public_key(public_key_bytes, backend=default_backend())
        self._protocol = protocol
        self._chunk_size = chunk_size
        self._buffer = b""
        self._block_size = 128  # Block size for padding, in bits
        self._key_size = int(32 * 1.5)  # Estimated size of the encrypted AES key
        self._nonce_size = 12  # Size of nonce for AES-GCM
        self._timestamp_size = struct.calcsize("d")
        self._length_indicator_size = 2  # Size for the length indicator
        self._metadata_size = self._key_size + self._length_indicator_size

    def get_public_key(self):
        return self._public_key

    def _encrypt_aes_key(self, aes_key):
        # Encrypt AES Key with server's public RSA key
        return self._public_key.encrypt(
            aes_key, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))

    def _encrypt_with_aes_gcm(self, message):
        aes_key = AESGCM.generate_key(bit_length=128)
        aesgcm = AESGCM(aes_key)
        nonce = os.urandom(self._nonce_size)
        encrypted_message = aesgcm.encrypt(nonce, message, None)
        return nonce + encrypted_message, aes_key

    def _pad_message(self, message):
        # Pad the message with the timestamp
        timestamp = struct.pack("d", time.time())

        padder = sym_padding.PKCS7(self._block_size).padder()
        padded_data = padder.update(message + b"\x00" * self._timestamp_size) + padder.finalize()

        finalized_data = padded_data[:-self._timestamp_size] + timestamp

        return finalized_data

    def _adjust_and_encrypt_message(self, message):
        max_message_size = self._chunk_size - self._nonce_size - self._timestamp_size - self._metadata_size
        while True:
            padded_message = self._pad_message(message)
            encrypted_message, aes_key = self._encrypt_with_aes_gcm(padded_message)

            if len(encrypted_message) <= max_message_size:
                break

            # Reduce message size and retry
            message = message[:int(len(message) * 0.9)]

        return encrypted_message, aes_key, message

    def flush(self):
        encoded_blocks = []
        while len(self._buffer) > 0:
            # Get a chunk of the buffer up to the estimated max message size
            message_chunk_length = int((self._chunk_size - self._metadata_size - self._timestamp_size) * 0.75)
            message_chunk = self._buffer[:message_chunk_length]

            readied_chunk = message_chunk.ljust(message_chunk_length, b'\x00')

            encrypted_chunk, aes_key, message = self._adjust_and_encrypt_message(readied_chunk)
            encrypted_key = self._encrypt_aes_key(aes_key)
            self._buffer = self._buffer[len(message):]

            final_chunk = encrypted_chunk.ljust(self._chunk_size - len(encrypted_key) - self._length_indicator_size,
                                                b'\x00')
            final_chunk += encrypted_key
            final_chunk += struct.pack("H", len(encrypted_chunk))

            encoded_blocks.append(final_chunk)

        return encoded_blocks

    def add_message(self, message):
        message_bytes = message.encode() if isinstance(message, str) else message
        self._buffer += message_bytes + self._protocol.get_control_code("end").encode()

    def add_control_message(self, control_type, add_in=None):
        control_code = self._protocol.get_control_code(control_type, add_in).encode()
        self._buffer += control_code


@strict
class MessageDecoder:
    def __init__(self, protocol: ControlCodeProtocol, chunk_size=1024, private_key_bytes_overwrite=None):
        # Generate RSA key pair
        self._private_key = self._load_private_key(private_key_bytes_overwrite) if private_key_bytes_overwrite else (
            rsa.generate_private_key(public_exponent=65537, key_size=2048))
        self._public_key = self._private_key.public_key()

        # Serialize public key to send to clients
        self._public_key_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo)

        self._last_sequence_number = -1
        self.time_window = datetime.timedelta(minutes=5)  # Time window for valid timestamps
        self._chunk_size = chunk_size
        self._protocol = protocol

        self._buffer = ""
        self._complete_buffer: List[Union[str, _ControlCode]] = [""]

    def get_private_key(self):
        return self._private_key

    def get_public_key_bytes(self):
        return self._public_key_bytes

    @staticmethod
    def _load_private_key(pem_data):
        return serialization.load_pem_private_key(
            pem_data,
            password=None,  # Provide a password here if the key is encrypted
            backend=default_backend()
        )

    def _decrypt_aes_key(self, encrypted_key):
        return self._private_key.decrypt(
            encrypted_key,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))

    @staticmethod
    def _decrypt_message_aes_gcm(encrypted_message, key):
        iv, ciphertext, tag = encrypted_message[:12], encrypted_message[12:-16], encrypted_message[-16:]
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()

    def _decrypt_message(self, encrypted_message, encrypted_aes_key):
        aes_key = self._decrypt_aes_key(encrypted_aes_key)
        return self._decrypt_message_aes_gcm(encrypted_message, aes_key)

    def _parse_message(self, plainbytes):
        # Assuming the timestamp is at the end of the decrypted message
        timestamp_size = struct.calcsize("d")

        # Extract the timestamp from the end of the decrypted data
        timestamp_bytes = plainbytes[-timestamp_size:]
        decrypted_message = plainbytes[:-timestamp_size]
        finalized_message = decrypted_message.rstrip(b"\x00")

        # Convert the timestamp back to a float
        timestamp = struct.unpack("d", timestamp_bytes)[0]
        return timestamp, self._last_sequence_number+1, finalized_message,

    def _validate_timestamp(self, timestamp):
        current_time = datetime.datetime.now(datetime.timezone.utc)
        timestamp_datetime = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)

        if current_time - timestamp_datetime > self.time_window or (timestamp_datetime - current_time).total_seconds() > 0.01:
            return False
        return True

    def _validate_sequence_number(self, sequence_number):
        if sequence_number <= self._last_sequence_number:
            return False
        self._last_sequence_number = sequence_number
        return True

    def _unpack_chunk(self, chunk):
        # Decrypt message
        rsa_encrypted_data_size = 256

        # Extract the length of the encrypted message
        encrypted_message_length = struct.unpack("H", chunk[-2:])[0]

        # Calculate the starting position of the RSA encrypted AES key
        start_of_key = self._chunk_size - rsa_encrypted_data_size - 2

        # Extract the encrypted AES key
        encrypted_key = chunk[start_of_key:-2]
        encrypted_message = chunk[:encrypted_message_length]
        return encrypted_key, encrypted_message

    def _decrypt_and_validate_chunk(self, chunk):
        encrypted_key, encrypted_message = self._unpack_chunk(chunk)

        plainbytes = self._decrypt_message(encrypted_message, encrypted_key)

        # Extract timestamp and sequence number from the plaintext
        timestamp, sequence_number, actual_message = self._parse_message(plainbytes)

        # Validate timestamp and sequence number
        if not self._validate_timestamp(timestamp) or not self._validate_sequence_number(sequence_number):
            raise Exception("Invalid message: timestamp or sequence number is not valid.")

        return actual_message

    def add_chunk(self, encrypted_chunk):
        # Decrypt and validate the chunk
        try:
            decrypted_chunk = self._decrypt_and_validate_chunk(encrypted_chunk).decode('utf-8')
        except Exception as e:
            print(f"Error in decryption/validation: {e}")
            return
        self._buffer += decrypted_chunk

        # Process complete and partial messages in buffer
        exec_start, exec_end = self._protocol.get_exec_code_delimiters()
        pattern = fr'(\{exec_start}{exec_start}^\{exec_end}{exec_end}+\{exec_end})|({exec_start}^\{exec_start}\{exec_end}{exec_end}+)'
        matches = re.findall(pattern, self._buffer)

        if not matches:
            return

        # Flatten the tuple results and filter out empty matches
        parsed_parts = [part for match in matches for part in match if part]
        validations = []

        last_end = 0
        for i, expression in enumerate(parsed_parts):
            try:
                validation_result, add_in = self._protocol.validate_control_code(expression)
            except ValueError:
                continue
            if validation_result == "end":
                # Consider message as complete
                self._complete_buffer[-1] += ''.join(parsed_parts[last_end:i])
                len_to_remove = len(self._complete_buffer[-1]) + len(parsed_parts[i])
                self._buffer = self._buffer[len_to_remove:]
                last_end = i
                self._complete_buffer.extend([_ControlCode(validation_result, add_in)] + validations + [""])
                validations.clear()
            elif validation_result in ["Invalid control code", "Invalid key"]:
                # Malformed or invalid expression, add to buffer
                self._complete_buffer[-1] += expression
            else:
                validations.append(_ControlCode(validation_result, add_in))
                parsed_parts[i] = ""
                start_index = self._buffer.find(expression)
                end_index = start_index + len(expression)
                self._buffer = self._buffer[:start_index] + self._buffer[end_index:]
        if self._complete_buffer[-1] == "":
            self._complete_buffer = self._complete_buffer[:-1]
        self._complete_buffer.extend(validations)
        self._complete_buffer.append("")
        validations.clear()

    def get_complete(self):
        return_lst = self._complete_buffer[:-1] if self._complete_buffer[-1] == "" else self._complete_buffer
        self._complete_buffer = [""]
        return return_lst

    def get_all(self):
        return_lst = self._complete_buffer[:-1] if self._complete_buffer[-1] == "" else self._complete_buffer
        return_lst.append(self._buffer)
        self._complete_buffer = [""]
        self._buffer = ""
        return return_lst


if __name__ == "__main__":
    protocol = ControlCodeProtocol()
    client = SecureSocketClient(protocol)
    server = SecureSocketServer(client.get_socket(), protocol)

    client.startup()
    server.startup()

    client.add_message("Hello, server!")
    client.sendall()

    server.shutdown_client()
    client.cleanup()
    server.cleanup()
    print(client.get_socket())
    print("----------------------- Two-Way SecureSocket Comm test done -----------------------")


@strict  # Strict decorator makes any private attributes truly private
class ServerMessageHandler:
    def __init__(self, connection: UndefinedSocket, protocol: ControlCodeProtocol, _chunk_size=1024, private_key_bytes_overwrite=None):
        # Generate RSA key pair
        self._private_key = self._load_private_key(private_key_bytes_overwrite) if private_key_bytes_overwrite else (
            rsa.generate_private_key(public_exponent=65537, key_size=2048))
        self._public_key = self._private_key.public_key()

        # Serialize public key to send to clients
        self._public_key_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo)
        self._last_timestamp = datetime.datetime.now()
        self.rate_limit = 10  # Allow 10 messages per second

        self._connection = connection
        self._host = None
        self._port = None

        self._last_sequence_number = -1
        self.time_window = datetime.timedelta(minutes=5)  # Time window for valid timestamps
        self._chunk_size = _chunk_size
        self._protocol = protocol

        self._connection_established = False
        if type(self._connection.conn) is not socket.socket:
            self._host, self._port = self._connection.conn
            self._connection = None
        else:
            self._connection = self._connection.conn
            self._connection_established = True

    def get_public_key_bytes(self):
        return self._public_key_bytes

    @staticmethod
    def _load_private_key(pem_data):
        return serialization.load_pem_private_key(
            pem_data,
            password=None,  # Provide a password here if the key should be encrypted
            backend=default_backend()
        )

    def _decrypt_aes_key(self, encrypted_key):
        return self._private_key.decrypt(
            encrypted_key,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))

    @staticmethod
    def _decrypt_message_aes_gcm(encrypted_message, key):
        iv, ciphertext, tag = encrypted_message[:12], encrypted_message[12:-16], encrypted_message[-16:]
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()

    def _check_rate_limit(self):
        current_time = datetime.datetime.now()
        if (current_time - self._last_timestamp).total_seconds() > self.rate_limit:
            return False
        self._last_timestamp = current_time
        return True

    def _decrypt_message(self, encrypted_message, encrypted_aes_key):
        # Check rate limiting
        if not self._check_rate_limit():
            raise Exception("Rate limit exceeded")

        aes_key = self._decrypt_aes_key(encrypted_aes_key)
        return self._decrypt_message_aes_gcm(encrypted_message, aes_key)

    def _parse_message(self, plainbytes):
        # Assuming the timestamp is at the end of the decrypted message
        timestamp_size = struct.calcsize("d")

        # Extract the timestamp from the end of the decrypted data
        timestamp_bytes = plainbytes[-timestamp_size:]
        decrypted_message = plainbytes[:-timestamp_size]
        finalized_message = decrypted_message.rstrip(b"\x00")

        # Convert the timestamp back to a float
        timestamp = struct.unpack("d", timestamp_bytes)[0]
        return timestamp, self._last_sequence_number+1, finalized_message,

    def _validate_timestamp(self, timestamp):
        current_time = datetime.datetime.now(datetime.timezone.utc)
        timestamp_datetime = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)

        if current_time - timestamp_datetime > self.time_window or timestamp_datetime > current_time:
            return False
        return True

    def _validate_sequence_number(self, sequence_number):
        if sequence_number <= self._last_sequence_number:
            return False
        self._last_sequence_number = sequence_number
        return True

    def _unpack_chunk(self, chunk):
        # Decrypt message
        rsa_encrypted_data_size = 256

        # Extract the length of the encrypted message
        encrypted_message_length = struct.unpack("H", chunk[-2:])[0]

        # Calculate the starting position of the RSA encrypted AES key
        start_of_key = self._chunk_size - rsa_encrypted_data_size - 2

        # Extract the encrypted AES key
        encrypted_key = chunk[start_of_key:-2]
        encrypted_message = chunk[:encrypted_message_length]
        return encrypted_key, encrypted_message

    def _decrypt_and_validate_chunk(self, chunk):
        encrypted_key, encrypted_message = self._unpack_chunk(chunk)

        plainbytes = self._decrypt_message(encrypted_message, encrypted_key)

        # Extract timestamp and sequence number from the plaintext
        timestamp, sequence_number, actual_message = self._parse_message(plainbytes)

        # Validate timestamp and sequence number
        if not self._validate_timestamp(timestamp) or not self._validate_sequence_number(sequence_number):
            raise Exception("Invalid message: timestamp or sequence number is not valid.")

        return actual_message

    def _reply_public_key(self):
        self._connection.send(self._public_key_bytes)

    def _setup_connection(self):
        if not getattr(self, "_connection"):
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind((self._host, self._port))
            server_socket.listen(1)
            print(f"Server listening on {self._host}:{self._port}...")
            self._connection, addr = server_socket.accept()
            print(f"Connection established with {addr}")
            self._reply_public_key()

    def listen_for_messages(self):
        buffer = ""
        complete_buffer = ""

        if not self._connection:
            self._setup_connection()
        while self._connection is not None:
            try:
                while True:
                    if self._connection is None:
                        break

                    encrypted_chunk = self._connection.recv(self._chunk_size)
                    if not encrypted_chunk:
                        break

                    # Decrypt and validate the chunk
                    try:
                        decrypted_chunk = self._decrypt_and_validate_chunk(encrypted_chunk).decode('utf-8')
                    except Exception as e:
                        print(f"Error in decryption/validation: {e}")
                        continue
                    buffer += decrypted_chunk

                    # Process complete and partial messages in buffer
                    exec_start, exec_end = self._protocol.get_exec_code_delimiters()
                    pattern = fr'(\{exec_start}{exec_start}^\{exec_end}{exec_end}+\{exec_end})|({exec_start}^\{exec_start}\{exec_end}{exec_end}+)'
                    matches = re.findall(pattern, buffer)

                    if not matches:
                        break

                    # Flatten the tuple results and filter out empty matches
                    parsed_parts = [part for match in matches for part in match if part]
                    completed_parts = []

                    last_end = 0
                    for i, expression in enumerate(parsed_parts):
                        try:
                            validation_result, add_in = self._protocol.validate_control_code(expression)
                        except ValueError:
                            continue
                        if validation_result == "end":
                            # Consider message as complete
                            completed_parts.append(parsed_parts[last_end:i+1])
                            last_end = i
                        elif validation_result in ["Invalid control code", "Invalid key"]:
                            # Malformed or invalid expression, add to buffer
                            complete_buffer += expression
                        elif validation_result == "shutdown":
                            return  # Returning is equal to a shutdown
                        else:
                            # There are no other expressions at the moment
                            pass

                    len_to_remove = 0
                    for completed_part in completed_parts:
                        message = ''.join(completed_part[:-1])
                        len_to_remove += len(message) + len(completed_part[-1])
                        complete_buffer += message
                    buffer = buffer[len_to_remove:]
                    print(complete_buffer)  # , end="")
                    complete_buffer = ""
            except socket.error as e:
                if e.errno == 10054:
                    print("Connection was forcibly closed by the remote host")
                elif e.errno == 10038:
                    print("Socket is not valid anymore")
                else:
                    print(f"Socket error in _listen_for_messages: {e}")
                self.close_connection()
            except Exception as e:
                print(f"Error in _listen_for_messages: {e}")
                self.close_connection()

    def close_connection(self):
        if self._connection:
            self._connection.close()
            self._connection = None
            print("Server connection closed.")

    def __del__(self):
        self.close_connection()


@strict
class ClientMessageHandler:
    def __init__(self, protocol, forced_host="127.0.0.1", forced_port=None, chunk_size=1024):
        self._public_key = None
        self._protocol = protocol
        self._chunk_size = chunk_size
        self._buffer = b""
        self._block_size = 128  # Block size for padding, in bits
        self._key_size = int(32 * 1.5)  # Estimated size of the encrypted AES key
        self._nonce_size = 12  # Size of nonce for AES-GCM
        self._timestamp_size = struct.calcsize("d")
        self._length_indicator_size = 2  # Size for the length indicator
        self._metadata_size = self._key_size + self._length_indicator_size

        self._host = forced_host
        self._port = PortUtils.find_available_port() if not forced_port else forced_port
        self._connection = None
        self._connection_established = False

    def get_host(self):
        return self._host

    def get_port(self):
        return self._port

    def get_socket(self):
        return UndefinedSocket((self._host, self._port))

    def get_connected_socket(self):
        return UndefinedSocket(self._connection)

    def start_in_thread(self):
        threading.Thread(target=self.connect_to_server).start()

    def connect_to_server(self):
        retry_attempts = 5
        for attempt in range(retry_attempts):
            try:
                self._connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._connection.connect((self._host, self._port))
                print(f"Connected to server at {self._host}:{self._port}")

                # Receive initial message from the server
                public_key_bytes = self._connection.recv(self._chunk_size)
                self._public_key = serialization.load_pem_public_key(public_key_bytes, backend=default_backend())
                print(f"Received key from server: {public_key_bytes}")

                self._connection_established = True
                break
            except ConnectionError as e:
                print(f"Connection attempt {attempt + 1} failed: {e}")
                time.sleep(5)  # Wait before retrying
        else:
            print("Failed to connect to the server after several attempts.")

    def _encrypt_aes_key(self, aes_key):
        while self._public_key is None:
            time.sleep(0.1)

        # Encrypt AES Key with server's public RSA key
        return self._public_key.encrypt(
            aes_key, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))

    def _encrypt_with_aes_gcm(self, message):
        aes_key = AESGCM.generate_key(bit_length=128)
        aesgcm = AESGCM(aes_key)
        nonce = os.urandom(self._nonce_size)
        encrypted_message = aesgcm.encrypt(nonce, message, None)
        return nonce + encrypted_message, aes_key

    def _pad_message(self, message):
        # Pad the message with the timestamp
        timestamp = struct.pack("d", time.time())

        padder = sym_padding.PKCS7(self._block_size).padder()
        padded_data = padder.update(message + b"\x00" * self._timestamp_size) + padder.finalize()

        finalized_data = padded_data[:-self._timestamp_size] + timestamp

        return finalized_data

    def _adjust_and_encrypt_message(self, message):
        max_message_size = self._chunk_size - self._nonce_size - self._timestamp_size - self._metadata_size
        while True:
            padded_message = self._pad_message(message)
            encrypted_message, aes_key = self._encrypt_with_aes_gcm(padded_message)

            if len(encrypted_message) <= max_message_size:
                break

            # Reduce message size and retry
            message = message[:int(len(message) * 0.9)]

        return encrypted_message, aes_key, message

    def flush(self):
        while not self._connection_established or self._public_key is None:
            time.sleep(0.01)

        encoded_blocks = []
        while len(self._buffer) > 0:
            # Get a chunk of the buffer up to the estimated max message size
            message_chunk_length = int((self._chunk_size - self._metadata_size - self._timestamp_size) * 0.75)
            message_chunk = self._buffer[:message_chunk_length]

            readied_chunk = message_chunk.ljust(message_chunk_length, b'\x00')

            encrypted_chunk, aes_key, message = self._adjust_and_encrypt_message(readied_chunk)
            encrypted_key = self._encrypt_aes_key(aes_key)
            self._buffer = self._buffer[len(message):]

            final_chunk = encrypted_chunk.ljust(self._chunk_size - len(encrypted_key) - self._length_indicator_size,
                                                b'\x00')
            final_chunk += encrypted_key
            final_chunk += struct.pack("H", len(encrypted_chunk))

            encoded_blocks.append(final_chunk)

        # Wait until the connection is established
        while not self._connection_established:
            time.sleep(0.1)  # Wait briefly and check again

        if hasattr(self, '_connection'):
            for block in encoded_blocks:
                self._connection.send(block)

    def add_message(self, message):
        while not self._connection_established or self._public_key is None:
            time.sleep(0.01)
        message_bytes = message.encode() if isinstance(message, str) else message
        self._buffer += message_bytes + self._protocol.get_control_code("end").encode()

    def send_control_message(self, control_type, add_in=None):
        control_code = self._protocol.get_control_code(control_type, add_in).encode()
        self._buffer += control_code

    def close_connection(self):
        self._connection_established = False
        if self._connection:
            self._connection.close()
            self._connection = None
            print("Client connection closed.")

    def __del__(self):
        self.close_connection()


if __name__ == "__main__":
    os.system("cls")
    protocol = ControlCodeProtocol()
    client = ClientMessageHandler(protocol)
    server = ServerMessageHandler(client.get_socket(), protocol)
    message_thread = threading.Thread(target=server.listen_for_messages)
    message_thread.start()
    print("Starting client ...")
    client.connect_to_server()
    client.add_message("HELL")
    client.flush()
    client.send_control_message("shutdown")
    client.flush()
    server.close_connection()
    client.close_connection()
    message_thread.join()
    print("----------------------- One-Way MessageHandler Comm test done -----------------------")


class ServerStream:
    def __init__(self, host: str, port: Optional[int] = None, key_length: Literal[1024, 2048, 4096] = 2048):
        self._host = host
        self._port = port or PortUtils.find_available_port()
        self._key_length = key_length
        private_key_bytes, public_key_bytes = CryptUtils.generate_rsa_key(key_length)
        self.public_key_bytes = public_key_bytes
        self._private_key = CryptUtils.load_private_key(private_key_bytes)
        self._public_key = CryptUtils.load_public_key(public_key_bytes)
        self._server_socket = self._connection = self._address = None

    def get_port(self):
        return self._port

    def connect(self):
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind((self._host, self._port))
        self._server_socket.listen(5)
        self._connection, self._address = self._server_socket.accept()
        print(f"Connection established with {self._address}")

    def receive_and_decrypt(self) -> Optional[bytes]:
        complete_message = b""
        try:
            while True:
                chunk = self._connection.recv(self._key_length // 8)  # Receive encrypted chunks
                if not chunk:
                    break
                decrypted_chunk = CryptUtils.rsa_decrypt(chunk, self._private_key)
                complete_message += decrypted_chunk
            return complete_message
        except Exception as e:
            print(f"Error in receive_and_decrypt: {e}")
            return None

    def close_connection(self):
        self._connection.close()
        self._server_socket.close()


class ClientStream:
    def __init__(self, host: str, port: int, public_key_bytes):
        self._host = host
        self._port = port
        self._public_key = CryptUtils.load_public_key(public_key_bytes)
        self._client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._client_socket.connect((self._host, self._port))
        print(f"Connected to server at {self._host}:{self._port}")

    def encrypt_and_send(self, message: bytes):
        max_chunk_size = (self._public_key.key_size // 8) - 2 * 256 // 8 - 2  # Maximum chunk size for RSA encryption with padding
        for i in range(0, len(message), max_chunk_size):
            chunk = message[i:i + max_chunk_size]
            encrypted_chunk = CryptUtils.rsa_encrypt(chunk, self._public_key)
            self._client_socket.send(encrypted_chunk)

    def close_connection(self):
        self._client_socket.close()


# if __name__ == "__main__":
#     server = ServerStream('127.0.0.1')
#     print("public bytes", server.public_key_bytes, "\nport", server.get_port())
#     server.connect()  # Blocking till connect
#     message = server.receive_and_decrypt()  # Blocking till message
#     if message:
#         print(f"Received message: {message.decode()}")
#     server.close_connection()
#
#     public_key_bytes = input("Public key bytes: ").encode('utf-8').decode('unicode_escape').encode('latin1')
#     port = int(input("Port: "))
#     client = ClientStream('127.0.0.1', port, public_key_bytes)  # Blocking till connect
#     message = b"Hello, this is a long message that will be split into chunks and sent encrypted."
#     client.encrypt_and_send(message)
#     client.close_connection()


class SecureDatabase:
    def __init__(self, db_connection):
        self.conn = db_connection

    def _get_all_tables(self) -> tuple:
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        return tuple(table[0] for table in tables)

    def _get_all_columns(self, table_name) -> tuple:
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()
        column_names = [info[1] for info in columns_info]
        return tuple(column_names)

    def _add_encrypted_column(self, table_name):
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()
        column_names = [info[1] for info in columns_info]

        if "encrypted" not in column_names:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN encrypted TEXT;")
            self.conn.commit()

    @staticmethod
    def _step_through(dic):
        curr_dict = dic
        while True:
            try:
                key, value = next(iter(curr_dict.items()))
                yield key
                curr_dict = value
            except StopIteration:
                 break

    def _get_all(self, levels):
        curr_config = []
        for level in levels:
            curr_config.append(level[0])

        all_getter = [self._get_all_tables, self._get_all_columns, lambda *args: "*"][len(curr_config)]
        return all_getter(*curr_config)

    def _encrypt_data(self, data: str, password: str) -> bytes:
        key = CryptUtils.generate_aes_key(256)
        iv, encrypted_data, tag = CryptUtils.aes_encrypt(data.encode(), key)
        return CryptUtils.pack_ae_data(iv, encrypted_data, tag)

    def encrypt(self, encryption_config: Dict[str, Any], password: str):
        cursor = self.conn.cursor()

        levels = []
        for config in self._step_through(encryption_config):
            if isinstance(config, tuple):
                levels.append(config)
            else:
                levels.append((config,) if config != "ALL" else (self._get_all(levels)))

        print(levels)

        for level in levels:
            if len(level) == 1:
                table_name = level[0]
                self._add_encrypted_column(table_name)
                columns = self._get_all_columns(table_name)
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()

                for row in rows:
                    primary_key_value = row[0]
                    encrypted_row = []
                    encryption_bits = ""

                    for i, value in enumerate(row):
                        if i == 0:
                            encrypted_row.append(value)
                            encryption_bits += "0"
                        else:
                            encrypted_value = self._encrypt_data(str(value), password)
                            encrypted_row.append(encrypted_value)
                            encryption_bits += "1"

                    encrypted_row.append(encryption_bits)
                    placeholders = ', '.join(['?' for _ in encrypted_row])
                    cursor.execute(f"INSERT OR REPLACE INTO {table_name} VALUES ({placeholders})", encrypted_row)
            elif len(level) == 2:
                table_name, column_name = level
                self._add_encrypted_column(table_name)
                cursor.execute(f"SELECT {column_name} FROM {table_name}")
                rows = cursor.fetchall()

                for row in rows:
                    value = row[0]
                    encrypted_value = self._encrypt_data(str(value), password)
                    cursor.execute(f"UPDATE {table_name} SET {column_name} = ? WHERE {column_name} = ?", (encrypted_value, value))

        self.conn.commit()

    def decrypt(self, encryption_config: Dict[str, Any]):
        pass


class GeneratePasswords:
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


class OSRandomGenerator:
    @staticmethod
    def random() -> float:
        return int.from_bytes(os.urandom(7), "big") / (1 << 56)

    @classmethod
    def uniform(cls, a: float, b: float) -> float:
        return a + (b - a) * cls.random()

    @classmethod
    def randint(cls, a: int, b: int) -> int:
        return math.floor(cls.uniform(a, b + 1))

    @classmethod
    def randbelow(cls, b: int) -> int:
        return cls.randint(0, b)

    @classmethod
    def choice(cls, seq: Union[tuple, list, dict]) -> Any:
        if not isinstance(seq, dict):
            return seq[cls.randint(0, len(seq) - 1)]
        return seq[tuple(seq.keys())[cls.randint(0, len(seq) - 1)]]

    @classmethod
    def gauss(cls, mu: float, sigma: float) -> float:
        # Using Box-Muller transform for generating Gaussian distribution
        u1 = cls.random()
        u2 = cls.random()
        z0 = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
        return mu + z0 * sigma

    @classmethod
    def expovariate(cls, lambd: float) -> float:
        u = cls.random()
        return -math.log(1 - u) / lambd

    @classmethod
    def gammavariate(cls, alpha: float, beta: float) -> float:
        # Uses Marsaglia and Tsang’s method for generating Gamma variables
        if alpha > 1:
            d = alpha - 1/3
            c = 1/math.sqrt(9*d)
            while True:
                x = cls.gauss(0, 1)
                v = (1 + c*x)**3
                u = cls.random()
                if u < 1 - 0.0331*(x**2)**2:
                    return d*v / beta
                if math.log(u) < 0.5*x**2 + d*(1 - v + math.log(v)):
                    return d*v / beta
        elif alpha == 1.0:
            return -math.log(cls.random()) / beta
        else:
            while True:
                u = cls.random()
                b = (math.e + alpha)/math.e
                p = b*u
                if p <= 1:
                    x = p**(1/alpha)
                else:
                    x = -math.log((b-p)/alpha)
                u1 = cls.random()
                if p > 1:
                    if u1 <= x**(alpha - 1):
                        return x / beta
                elif u1 <= math.exp(-x):
                    return x / beta

    @classmethod
    def betavariate(cls, alpha: float, beta: float) -> float:
        """
        Generate a random number based on the Beta distribution with parameters alpha and beta.

        :param alpha: Alpha parameter of the Beta distribution.
        :param beta: Beta parameter of the Beta distribution.
        :return: Random number from the Beta distribution.
        """
        y1 = cls.gammavariate(alpha, 1.0)
        y2 = cls.gammavariate(beta, 1.0)
        return y1 / (y1 + y2)

    @classmethod
    def lognormvariate(cls, mean: float, sigma: float) -> float:
        """
        Generate a random number based on the log-normal distribution with specified mean and sigma.

        :param mean: Mean of the underlying normal distribution.
        :param sigma: Standard deviation of the underlying normal distribution.
        :return: Random number from the log-normal distribution.
        """
        normal_value = cls.gauss(mean, sigma)
        return math.exp(normal_value)


class SecretsRandomGenerator:
    @staticmethod
    def random() -> float:
        return secrets.randbits(56) / (1 << 56)

    @classmethod
    def uniform(cls, a: float, b: float) -> float:
        return a + (b - a) * cls.random()

    @classmethod
    def randint(cls, a: int, b: int) -> int:
        return math.floor(cls.uniform(a, b + 1))

    @classmethod
    def randbelow(cls, b: int) -> int:
        return cls.randint(0, b)

    @classmethod
    def choice(cls, seq: Union[tuple, list, dict]) -> Any:
        if not isinstance(seq, dict):
            return seq[cls.randint(0, len(seq) - 1)]
        return seq[tuple(seq.keys())[cls.randint(0, len(seq) - 1)]]

    @classmethod
    def gauss(cls, mu: float, sigma: float) -> float:
        # Using Box-Muller transform for generating Gaussian distribution
        u1 = cls.random()
        u2 = cls.random()
        z0 = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
        return mu + z0 * sigma

    @classmethod
    def expovariate(cls, lambd: float) -> float:
        u = cls.random()
        return -math.log(1 - u) / lambd

    @classmethod
    def gammavariate(cls, alpha: float, beta: float) -> float:
        # Uses Marsaglia and Tsang’s method for generating Gamma variables
        if alpha > 1:
            d = alpha - 1/3
            c = 1/math.sqrt(9*d)
            while True:
                x = cls.gauss(0, 1)
                v = (1 + c*x)**3
                u = cls.random()
                if u < 1 - 0.0331*(x**2)**2:
                    return d*v / beta
                if math.log(u) < 0.5*x**2 + d*(1 - v + math.log(v)):
                    return d*v / beta
        elif alpha == 1.0:
            return -math.log(cls.random()) / beta
        else:
            while True:
                u = cls.random()
                b = (math.e + alpha)/math.e
                p = b*u
                if p <= 1:
                    x = p**(1/alpha)
                else:
                    x = -math.log((b-p)/alpha)
                u1 = cls.random()
                if p > 1:
                    if u1 <= x**(alpha - 1):
                        return x / beta
                elif u1 <= math.exp(-x):
                    return x / beta

    @classmethod
    def betavariate(cls, alpha: float, beta: float) -> float:
        """
        Generate a random number based on the Beta distribution with parameters alpha and beta.

        :param alpha: Alpha parameter of the Beta distribution.
        :param beta: Beta parameter of the Beta distribution.
        :return: Random number from the Beta distribution.
        """
        y1 = cls.gammavariate(alpha, 1.0)
        y2 = cls.gammavariate(beta, 1.0)
        return y1 / (y1 + y2)

    @classmethod
    def lognormvariate(cls, mean: float, sigma: float) -> float:
        """
        Generate a random number based on the log-normal distribution with specified mean and sigma.

        :param mean: Mean of the underlying normal distribution.
        :param sigma: Standard deviation of the underlying normal distribution.
        :return: Random number from the log-normal distribution.
        """
        normal_value = cls.gauss(mean, sigma)
        return math.exp(normal_value)


class WeightedRandom:
    def __init__(self, generator: Literal["weak", "os", "strong", "secrets"] = "strong"):
        self._generator = {"weak": random, "os": OSRandomGenerator, "strong": secrets.SystemRandom(),
                           "secrets": SecretsRandomGenerator}[generator]

    @staticmethod
    def _transform_and_scale(x: float, transform_func: Callable[[float], float], lower_bound: Union[float, int],
                             upper_bound: Union[float, int]) -> float:
        """
        Apply the transformation function to the random value and scale it within the given bounds.

        :param x: The initial random value (between 0 and 1).
        :param transform_func: The function to transform the value.
        :param lower_bound: The lower bound of the output range.
        :param upper_bound: The upper bound of the output range.
        :return: Transformed and scaled value.
        """
        transformed_value = transform_func(x)
        scaled_value = lower_bound + (upper_bound - lower_bound) * transformed_value
        return scaled_value

    def gaussian(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1,
                 mu: Union[float, int] = 0, sigma: Union[float, int] = 1) -> float:
        """
        Generate a random number based on the normal (Gaussian) distribution and scale it within the specified bounds.

        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :param mu: Mean of the distribution.
        :param sigma: Standard deviation of the distribution.
        :return: Scaled random number from the normal distribution.
        """
        return self._transform_and_scale(self._generator.random(), lambda x: self._generator.gauss(mu, sigma),
                                         lower_bound, upper_bound)

    def quadratic(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1) -> float:
        """
        Generate a random number based on a quadratic distribution and scale it within the specified bounds.

        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :return: Scaled random number from the quadratic distribution.
        """
        return self._transform_and_scale(self._generator.random(), lambda x: x ** 2, lower_bound, upper_bound)

    def cubic(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1) -> float:
        """
        Generate a random number based on a cubic distribution and scale it within the specified bounds.

        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :return: Scaled random number from the cubic distribution.
        """
        return self._transform_and_scale(self._generator.random(), lambda x: x ** 3, lower_bound, upper_bound)

    def exponential(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1, lambd: float = 1.0
                    ) -> float:
        """
        Generate a random number based on the exponential distribution and scale it within the specified bounds.

        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :param lambd: Lambda parameter (1/mean) of the distribution.
        :return: Scaled random number from the exponential distribution.
        """
        return self._transform_and_scale(self._generator.random(), lambda x: self._generator.expovariate(lambd),
                                         lower_bound, upper_bound)

    def falling(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1) -> float:
        """
        Generate a random number based on a falling distribution and scale it within the specified bounds.
        """
        return self._transform_and_scale(self._generator.random(), lambda x: 1 - x, lower_bound, upper_bound)

    def sloping(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1) -> float:
        """
        Generate a random number based on a sloping distribution and scale it within the specified bounds.
        """
        return self._transform_and_scale(self._generator.random(), lambda x: x ** 2, lower_bound, upper_bound)

    def exponential_falling(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1,
                            lambd: float = 1.0) -> float:
        """
        Generate a random number based on a falling exponential distribution and scale it within the specified bounds.
        """
        return self._transform_and_scale(self._generator.random(), lambda x: 1 - self._generator.expovariate(lambd), lower_bound, upper_bound)

    def quadratic_falling(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1) -> float:
        """
        Generate a random number based on a quadratic distribution and scale it within the specified bounds.

        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :return: Scaled random number from the quadratic distribution.
        """
        return self._transform_and_scale(self._generator.random(), lambda x: 1 - x ** 2, lower_bound, upper_bound)

    def cubic_falling(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1) -> float:
        """
        Generate a random number based on a falling cubic distribution and scale it within the specified bounds.
        """
        return self._transform_and_scale(self._generator.random(), lambda x: 1 - x ** 3, lower_bound, upper_bound)

    def functional(self, math_func: Callable, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1
                   ) -> float:
        """
        Generate a random number based on a user-defined mathematical function and scale it within the specified bounds.

        :param math_func: Callable mathematical function that takes a random number between 0 and 1 and transforms it.
        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :return: Scaled transformed random number.
        """
        return self._transform_and_scale(self._generator.random(), math_func, lower_bound, upper_bound)

    def uniform(self, lower_bound: Union[float, int] = 0.0, upper_bound: Union[float, int] = 1.0) -> float:
        """
        Generate a random number based on the uniform distribution.

        :param lower_bound: Lower bound of the uniform distribution.
        :param upper_bound: Upper bound of the uniform distribution.
        :return: Random number from the uniform distribution.
        """
        return self._generator.uniform(lower_bound, upper_bound)

    def randint(self, lower_bound: int, upper_bound: int) -> int:
        """
        Generate a random integer between lower_bound and upper_bound (inclusive).

        :param lower_bound: Lower bound of the range.
        :param upper_bound: Upper bound of the range.
        :return: Random integer between lower_bound and upper_bound.
        """
        return self._generator.randint(lower_bound, upper_bound)

    def choice(self, seq) -> Any:
        """
        Choose a random element from a non-empty sequence.

        :param seq: Sequence to choose from.
        :return: Randomly selected element from the sequence.
        """
        return self._generator.choice(seq)

    def linear_transform(self, slope: float, intercept: float, lower_bound: Union[float, int] = 0,
                         upper_bound: Union[float, int] = 1) -> float:
        """
        Generate a random number based on a linear transformation and scale it within the specified bounds.

        :param slope: Slope of the linear transformation.
        :param intercept: Intercept of the linear transformation.
        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :return: Scaled random number from the linear transformation.
        """
        return self._transform_and_scale(self._generator.random(), lambda x: slope * x + intercept, lower_bound, upper_bound)

    def triangular(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1, mode: float = 0.5
                   ) -> float:
        """
        Generate a random number based on a triangular distribution and scale it within the specified bounds.

        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :param mode: The value where the peak of the distribution occurs.
        :return: Scaled random number from the triangular distribution.
        """
        return self._transform_and_scale(self._generator.random(), lambda x: self._generator.uniform(lower_bound, mode) if x < 0.5 else self._generator.uniform(mode, upper_bound), lower_bound, upper_bound)

    def beta(self, alpha: float, beta: float, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1
             ) -> float:
        """
        Generate a random number based on a beta distribution and scale it within the specified bounds.

        :param alpha: Alpha parameter of the beta distribution.
        :param beta: Beta parameter of the beta distribution.
        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :return: Scaled random number from the beta distribution.
        """
        return self._transform_and_scale(self._generator.random(), lambda x: self._generator.betavariate(alpha, beta), lower_bound, upper_bound)

    def log_normal(self, mean: float, sigma: float, lower_bound: Union[float, int] = 0,
                   upper_bound: Union[float, int] = 1) -> float:
        """
        Generate a random number based on a log-normal distribution and scale it within the specified bounds.

        :param mean: Mean of the underlying normal distribution.
        :param sigma: Standard deviation of the underlying normal distribution.
        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :return: Scaled random number from the log-normal distribution.
        """
        return self._transform_and_scale(self._generator.random(), lambda x: self._generator.lognormvariate(mean, sigma), lower_bound, upper_bound)

    def sinusoidal(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1) -> float:
        """
        Generate a random number based on a sinusoidal distribution and scale it within the specified bounds.

        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :return: Scaled random number from the sinusoidal distribution.
        """
        return self._transform_and_scale(self._generator.random(), lambda x: 0.5 * (1 + math.sin(2 * math.pi * x - math.pi / 2)), lower_bound, upper_bound)

    def piecewise_linear(self, breakpoints: List[float], slopes: List[float], lower_bound: Union[float, int] = 0,
                         upper_bound: Union[float, int] = 1) -> float:
        """
        Generate a random number based on a piecewise linear function and scale it within the specified bounds.

        :param breakpoints: List of breakpoints for the piecewise linear function.
        :param slopes: List of slopes for each segment of the piecewise linear function.
        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :return: Scaled random number from the piecewise linear function.
        """
        def piecewise(x):
            for i, breakpoint in enumerate(breakpoints):
                if x < breakpoint:
                    return slopes[i] * (x - (breakpoints[i-1] if i > 0 else 0))
            return slopes[-1] * (x - breakpoints[-1])

        return self._transform_and_scale(self._generator.random(), piecewise, lower_bound, upper_bound)


if __name__ == "__main__":
    for generator in ("weak", "os", "strong", "secrets"):
        # Test generator
        print(f"Testing with {generator} generator:")
        rng = WeightedRandom(generator)
        print("Gaussian:", rng.gaussian(0, 1, 0, 1))
        print("Cubic:", rng.cubic(0, 1))
        print("Exponential:", rng.exponential(0, 1, 1.0))
        print("Falling:", rng.falling(0, 1))
        print("Sloping:", rng.sloping(0, 1))
        print("Exponential Falling:", rng.exponential_falling(0, 1, 1.0))
        print("Cubic Falling:", rng.cubic_falling(0, 1))
        print("Functional (x^2):", rng.functional(lambda x: x ** 2, 0, 1))
        print("Uniform:", rng.uniform(1, 10))
        print("RandInt:", rng.randint(1, 10))
        print("Choice:", rng.choice([1, 2, 3, 4, 5]))
        print("Linear Transform:", rng.linear_transform(2, 1, 0, 1))
        print("Triangular:", rng.triangular(0, 1, 0.5))
        print("Beta:", rng.beta(2, 5, 0, 1))
        print("Log Normal:", rng.log_normal(0, 1, 0, 1))
        print("Sinusoidal:", rng.sinusoidal(0, 1))
        print("Piecewise Linear:", rng.piecewise_linear([0.3, 0.7], [1, -1], 0, 1))
        print("\n")

    print("Custom exponent: ", round(rng.exponential(0.1, 10, 5.0), 1))


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


def local_test():
    try:
        manager = SecurePasswordManager()
        password = manager.generate_ratio_based_password_v2(length=26, letters_ratio=0.5, numbers_ratio=0.3,
                                                            punctuations_ratio=0.2, exclude_similar=True)
        manager.add_password("example.com", "json-the-greatest", password)
        manager.store_in_buffer("example.com", 0)  # Stores unencrypted password in a buffer
        print(manager.get_password("example.com"), "|", manager.use_from_buffer(0))  # for faster access.

        print(GeneratePasswords.generate_custom_sentence_based_password_v1(
            "Exploring the unknown -- discovering new horizons...", random_case=True, extra_char="_",
            char_position="keep", num_length=5, special_chars_length=2))
    except Exception as e:
        print(f"Exception occurred {e}.")
        return False
    print("Test completed successfully.")
    return True


if __name__ == "__main__":
    from aplustools.io import diagnose_shutdown_blockers

    print(diagnose_shutdown_blockers())
    local_test()
