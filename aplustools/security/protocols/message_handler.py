from aplustools.security.protocols import UndefinedSocket, ControlCodeProtocol
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
from aplustools.io.environment import strict
from aplustools.utils import PortUtils
import threading
import datetime
import socket
import struct
import time
import re
import os


@strict  # Strict decorator makes any private attributes truly private
class ServerMessageHandler:
    def __init__(self, connection: UndefinedSocket, protocol: ControlCodeProtocol, _chunk_size=1024,
                 private_key_bytes_overwrite=None):
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
