from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from aplustools.security.protocols.control_code_protocol import _ControlCode
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from aplustools.security.protocols import ControlCodeProtocol
from cryptography.hazmat.backends import default_backend
from aplustools.io.environment import strict
from typing import List, Union
import datetime
import struct
import time
import os
import re


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

    decoder = MessageDecoder(protocol=protocol)
    encoder = MessageEncoder(protocol=protocol, public_key_bytes=decoder.get_public_key_bytes())

    encoder.add_message("HEllo")
    message = encoder.flush()

    for chunk in message:
        decoder.add_chunk(chunk)

    print(decoder.get_complete())
