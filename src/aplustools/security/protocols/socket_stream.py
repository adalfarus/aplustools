from aplustools.security.crypto import CryptUtils
from aplustools.utils import PortUtils
from typing import Optional, Literal
import socket


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


if __name__ == "__main__":
    server = ServerStream('127.0.0.1')
    print("public bytes", server.public_key_bytes, "\nport", server.get_port())
    server.connect()  # Blocking till connect
    message = server.receive_and_decrypt()  # Blocking till message
    if message:
        print(f"Received message: {message.decode()}")
    server.close_connection()

    public_key_bytes = input("Public key bytes: ").encode('utf-8').decode('unicode_escape').encode('latin1')
    port = int(input("Port: "))
    client = ClientStream('127.0.0.1', port, public_key_bytes)  # Blocking till connect
    message = b"Hello, this is a long message that will be split into chunks and sent encrypted."
    client.encrypt_and_send(message)
    client.close_connection()
