from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from typing import Literal, Tuple, Optional
import os


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
    def generate_aes_key(bit_length: Literal[128, 192, 256]) -> bytes:
        return os.urandom(bit_length // 8)

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
    def generate_des_key(bit_length: Literal[64, 128, 192]) -> bytes:
        return os.urandom(bit_length // 8)

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
    def generate_rsa_key(bit_length: Literal[1024, 2048, 4096]) -> Tuple[bytes, bytes]:
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=bit_length,
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
