from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
from aplustools.io.environment import strict
import json
import os
import base64
import time
import struct
import datetime
from typing import Tuple, List, Literal, Optional, Union, Dict
import threading
import re
import errno
import socket
import unicodedata
import secrets
import string
import random


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


class ControlCode:
    def __init__(self, control_code: str, add_in: str):
        self.code = control_code
        self.add = add_in

    def __repr__(self):
        return f"ControlCode(code={self.code}, add={self.add})"


class UndefinedSocket:
    """Is either an uninitialized socket or an already connected one."""
    def __init__(self, conn: Union[Tuple[str, int], socket.socket]):
        self.conn = conn


@strict
class SecureSocketServer:
    def __init__(self, connection: UndefinedSocket, protocol: ControlCodeProtocol, _chunk_size=1024, private_key_bytes_overwrite=None):
        self._last_timestamp = datetime.datetime.now()
        self.rate_limit = 10  # Allow 10 messages per second

        self._connection = connection
        self._host = None
        self._port = None

        self._decoder = MessageDecoder(protocol, _chunk_size, private_key_bytes_overwrite)
        self._encoder = None
        self._protocol = protocol
        self._chunk_size = _chunk_size

        if type(self._connection.conn) is not socket.socket:
            self._host, self._port = self._connection.conn
            self._connection = None
        else:
            self._connection = self._connection.conn

    def start_and_exchange_keys(self):
        self._setup_connection()
        self._send_public_key()
        threading.Thread(target=self._receive_public_key_and_start_communication).start()

    def _setup_connection(self):
        if self._connection is not None:
            return

        while not isinstance(self._connection, socket.socket):
            try:
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.bind((self._host, self._port))
                server_socket.listen(1)
                print(f"Server listening on {self._host}:{self._port}...")
                self._connection, addr = server_socket.accept()
                print(f"Connection established with {addr}")
            except Exception as e:
                print(f"Error setting up connection: {e}. Retrying in 5 seconds ...")
                time.sleep(5)

    def _send_public_key(self):
        send = False
        while not send:
            try:
                self._connection.sendall(self._decoder.get_public_key_bytes())
                print("Sent public key to client")
                send = True
            except Exception as e:
                print(f"Error sending public key: {e}")
                send = False

    def _receive_public_key_and_start_communication(self):
        try:
            self._receive_public_key()
            self._listen_for_messages()
        except Exception as e:
            print(f"Error in _receive_public_key_and_start_communication: {e}")

    def _receive_public_key(self):
        client_public_key_bytes = ""
        while not client_public_key_bytes and not self._encoder:
            try:
                # Receive client's public key here
                encrypted_client_public_key_bytes = self._connection.recv(739)
                encrypted_aes_key_length = int.from_bytes(encrypted_client_public_key_bytes[:2], "big")
                encrypted_aes_key = encrypted_client_public_key_bytes[2:encrypted_aes_key_length+2]
                aes_key = CryptUtils.rsa_decrypt(encrypted_aes_key, self._decoder.get_private_key())

                rest_data = encrypted_client_public_key_bytes[encrypted_aes_key_length+2:]
                client_public_key_bytes = CryptUtils.aes_decrypt(*CryptUtils.unpack_ae_data(rest_data), key=aes_key)

                self._encoder = MessageEncoder(self._protocol, client_public_key_bytes, self._chunk_size)
                print(f"Received key from client: {client_public_key_bytes}")
            except Exception as e:
                print(f"Error receiving public key: {e}")

    def _check_rate_limit(self):
        current_time = datetime.datetime.now()
        if (current_time - self._last_timestamp).total_seconds() > self.rate_limit:
            return False
        self._last_timestamp = current_time
        return True

    def _listen_for_messages(self):
        while self._connection is not None:
            try:
                while True:
                    encrypted_chunk = self._connection.recv(self._chunk_size)
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
                            self._connection.close()
                            self._connection = None
                            break  # Break is equal to a shutdown
                        elif chunk.code == "input":
                            inp = input(chunk.add)
                            self._connection.sendall(inp.encode("utf-8"))
            except Exception as e:
                print(f"Error in listen_for_messages: {e}")

    def shutdown_client(self):
        while not self._encoder:
            time.sleep(0.1)
        self._encoder.add_message(self._protocol.get_control_code("shutdown"))  # Bad practice, this will result in
        chunks = self._encoder.flush()              # an empty string, followed by an end cc and then the cc you want.
        for chunk in chunks:
            self._connection.send(chunk)

    def close_connection(self):
        if self._connection:
            self._connection.close()
            self._connection = None
            print("Server connection closed.")

    def __del__(self):
        self.close_connection()


@strict
class SecureSocketClient:
    def __init__(self, protocol, forced_host="127.0.0.1", forced_port=None, _chunk_size=1024, private_key_bytes_overwrite=None):
        self._host = forced_host
        self._port = PortUtils.find_available_port() if not forced_port else forced_port
        self._connection = None
        self._connection_established = False

        self._decoder = MessageDecoder(protocol, _chunk_size, private_key_bytes_overwrite)
        self._encoder = None
        self._protocol = protocol
        self._chunk_size = _chunk_size

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

    def start_and_exchange_keys(self):
        threading.Thread(target=self._connect_and_exchange_keys).start()

    def _connect_and_exchange_keys(self):
        try:
            self._connect_to_server()
            self._receive_public_key()
            self._send_public_key()
            self._listen_for_messages()
        except Exception as e:
            print(f"Error in _connect_and_exchange_keys: {e}.")

    def _receive_public_key(self):
        public_key_bytes = ""
        while not public_key_bytes or not self._encoder:
            try:
                # Receive initial message from the server
                public_key_bytes = self._connection.recv(self._chunk_size)
                self._encoder = MessageEncoder(self._protocol, public_key_bytes, self._chunk_size)
                print(f"Received key from server: {public_key_bytes}")
            except Exception as e:
                print(f"Error in _receive_public_key: {e}")

    def _connect_to_server(self):
        while not self._connection_established:
            try:
                self._connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._connection.connect((self._host, self._port))
                print(f"Connected to server at {self._host}:{self._port}")
                self._connection_established = True
            except ConnectionError as e:
                print(f"Connection error: {e}. Retrying in 5 seconds ...")
                self._connection_established = False
                time.sleep(5)  # Wait before retrying

    def _send_public_key(self):
        send = False
        while not send:
            try:
                aes_key = CryptUtils.generate_aes_key(128)
                encrypted_public_key_bytes = CryptUtils.pack_ae_data(*CryptUtils.aes_encrypt(self._decoder.get_public_key_bytes(), aes_key))
                encrypted_aes_key = CryptUtils.rsa_encrypt(aes_key, self._encoder.get_public_key())
                self._connection.send(len(encrypted_aes_key).to_bytes(2, "big") + encrypted_aes_key + encrypted_public_key_bytes)
                send = True
            except Exception as e:
                print(f"Error in _send_public_key: {e}")
                send = False

    def _listen_for_messages(self):
        while self._connection_established:
            try:
                while True:
                    encrypted_chunk = self._connection.recv(self._chunk_size)
                    if not encrypted_chunk:
                        break

                    self._decoder.add_chunk(encrypted_chunk)
                    chunks = self._decoder.get_complete()

                    for chunk in chunks:
                        if type(chunk) is not str and chunk.code == "shutdown":
                            print("Shutting down client")
                            self._connection_established = False
                            break  # breaking is equal to a shutdown
            except Exception as e:
                print(f"Error in _listen_for_messages: {e}")

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
        while not self._connection_established:
            time.sleep(0.01)  # Wait briefly and check again

        if hasattr(self, '_connection'):
            encoded_blocks = self._encoder.flush()
            for block in encoded_blocks:
                self._connection.send(block)

    def close_connection(self):
        if self._connection:
            self._connection.close()
            self._connection = None
            print("Client connection closed.")

    def __del__(self):
        self.close_connection()


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
        self._complete_buffer: List[Union[str, ControlCode]] = [""]

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
                self._complete_buffer.extend([ControlCode(validation_result, add_in)] + validations + [""])
                validations.clear()
            elif validation_result in ["Invalid control code", "Invalid key"]:
                # Malformed or invalid expression, add to buffer
                self._complete_buffer[-1] += expression
            else:
                validations.append(ControlCode(validation_result, add_in))
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

    client.start_and_exchange_keys()
    server.start_and_exchange_keys()

    client.add_message("Hello, server!")
    client.sendall()

    server.shutdown_client()


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

        if type(self._connection.conn) is not socket.socket:
            self._host, self._port = self._connection.conn
            self._connection = None
        else:
            self._connection = self._connection.conn

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

        while True:
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


if __name__ == "__main__":
    os.system("cls")
    protocol = ControlCodeProtocol()
    client = ClientMessageHandler(protocol)
    server = ServerMessageHandler(client.get_socket(), protocol)
    threading.Thread(target=server.listen_for_messages).start()
    print("Starting client ...")
    client.connect_to_server()
    client.add_message("HELL")
    client.flush()
    client.send_control_message("shutdown")
    client.flush()


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


class Database:
    def __init__(self):
        raise NotImplementedError("This class isn't fully implemented yet, check back in version 1.5")

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
        db = None
        try:
            db = sqlite3.connect(database_file)
        except Exception as e:
            print("SQLite3 Error:", e)
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
    local_test()
