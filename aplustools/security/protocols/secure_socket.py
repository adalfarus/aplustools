from aplustools.security.protocols import MessageEncoder, MessageDecoder, ControlCodeProtocol
from aplustools.io.environment import strict, auto_repr
from aplustools.security.crypto import CryptUtils
from aplustools.utils import PortUtils
from typing import Union, Tuple
import threading
import datetime
import socket
import time


@auto_repr
class UndefinedSocket:
    """Is either an uninitialized socket or an already connected one."""
    def __init__(self, conn: Union[Tuple[str, int], socket.socket]):
        self.conn = conn


@strict
class SecureSocketServer:
    def __init__(self, connection: UndefinedSocket, protocol: ControlCodeProtocol, _chunk_size=1024,
                 private_key_bytes_overwrite=None):
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
                        break
                    elif chunk.code == "input":
                        inp = input(chunk.add)
                        self._encoder.add_message(inp)

                        encoded_blocks = self._encoder.flush()
                        for block in encoded_blocks:
                            self._connection.send(block)
            except Exception as e:
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
        self._input_buffer = ("", "")

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
        raise ValueError("Client unconnected")

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
                    if type(chunk) is str:
                        curr_buffer_chunk = self._input_buffer[1]
                        self._input_buffer = (self._input_buffer[0], curr_buffer_chunk + chunk)
                    elif chunk.code == "end":
                        curr_buffer_chunk = self._input_buffer[1]
                        self._input_buffer = (self._input_buffer[0] + curr_buffer_chunk + "\n", "")
                    elif type(chunk) is not str and chunk.code == "shutdown":
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

    def add_control_code(self, code, add_in: str = None):
        while self._encoder is None:
            time.sleep(0.01)
        self._encoder.add_control_message(code, add_in)

    def sendall(self):
        # Wait until the connection is established
        while self._connection is None or not self._key_exchange_done:
            time.sleep(0.01)  # Wait briefly and check again

        encoded_blocks = self._encoder.flush()
        for block in encoded_blocks:
            self._connection.send(block)

    def get_input_buffer(self):
        returns = self._input_buffer[0]
        self._input_buffer = ("", self._input_buffer[1])
        return returns

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

    from aplustools.io import diagnose_shutdown_blockers

    print(diagnose_shutdown_blockers())
