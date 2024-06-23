from cryptography.hazmat.primitives.asymmetric import rsa, dsa, ec, ed25519, ed448, x25519, x448
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend

from typing import NewType, IO, Union, Literal, Optional
from tempfile import mkdtemp
from pathlib import Path
import secrets
import os

from aplustools.io.environment import safe_remove
from aplustools.data import enum_auto

try:
    from quantcrypt.kem import Kyber
    from quantcrypt.cipher import KryptonKEM
    from quantcrypt.kdf import Argon2
except ImportError:
    Kyber = KryptonKEM = Argon2 = None


class _BASIC_KEY:
    cipher_type = "SymCipher"
    cipher = "Unknown"

    def __init__(self, key: bytes, original_key):
        self._key = key
        self._original_key = original_key

    def get_key(self) -> bytes:
        """Get the key"""
        return self._key

    def get_original_key(self) -> str:
        """Get the original key used to generate the key"""
        return self._original_key

    def encrypt(self, to_encrypt: bytes) -> bytes:
        """Encrypts to_encrypt and returns it."""
        raise NotImplementedError()

    def decrypt(self, to_decrypt: bytes) -> bytes:
        """Decrypts to_decrypt and returns it."""
        raise NotImplementedError()

    def __bytes__(self):
        return self._key

    def __str__(self):
        return self._key.hex()

    def __repr__(self):
        return str(self)


class _BASIC_KEYPAIR:
    cipher_type = "ASymCipher"
    cipher = "Unknown"

    def __init__(self, private_key, public_key):
        self._private_key = private_key
        self._public_key = public_key

    @staticmethod
    def _load_pem_private_key(key_to_load: bytes | str):
        if isinstance(key_to_load, (bytes, str)):
            if isinstance(key_to_load, str):
                key_to_load = bytes(key_to_load, "utf-8")
            key_to_load = serialization.load_pem_private_key(key_to_load, None, default_backend())
        return key_to_load

    def get_private_key(self):
        """Returns the private key"""
        return self._private_key

    def get_public_key(self):
        """Returns the public key"""
        return self._public_key

    def get_private_bytes(self) -> bytes:
        """Returns the private key in a byte format"""
        return self._private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

    def get_public_bytes(self) -> bytes:
        """Returns the public key in a byte format"""
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def encrypt(self, to_encrypt: bytes) -> bytes:
        """Encrypts to_encrypt and returns it."""
        raise NotImplementedError()

    def decrypt(self, to_decrypt: bytes) -> bytes:
        """Decrypts to_decrypt and returns it."""
        raise NotImplementedError()

    def sign(self, to_sign: bytes) -> bytes:
        """Signs to_sign and returns it."""
        raise NotImplementedError()

    def sign_verify(self, to_verify: bytes, signature: bytes) -> bool:
        """Verifies the signature with to_verify and returns a bool."""
        raise NotImplementedError()

    def __bytes__(self):
        return self.get_public_bytes()

    def __str__(self):
        return bytes(self).decode()

    def __repr__(self):
        return str(self)


_BASIC_KEY_TYPE = NewType("_BASIC_KEY_TYPE", _BASIC_KEY)
_BASIC_KEYPAIR_TYPE = NewType("_BASIC_KEYPAIR_TYPE", _BASIC_KEYPAIR)


class _AES_KEY(_BASIC_KEY):
    cipher = "AES"

    def __init__(self, key_size: Literal[128, 192, 256], key: Optional[bytes | str]):
        _original_key = key if key is not None else secrets.token_hex(key_size // 8)
        if isinstance(_original_key, bytes):
            if len(_original_key) * 8 != float(key_size):
                raise ValueError(f"Key size of given key ({len(_original_key) * 8}) "
                                 f"doesn't match the specified key size ({key_size})")
            _key = _original_key
        else:
            _key = PBKDF2HMAC(algorithm=hashes.SHA3_512(), length=32, salt=os.urandom(64), iterations=800_000,
                              backend=default_backend()).derive(_original_key.encode())
        super().__init__(_key, _original_key)

    def get_key(self) -> bytes:
        """Get the AES key"""
        return self._key

    def get_original_key(self) -> str:
        """Get the original key used to generate the AES key"""
        return self._original_key

    def __bytes__(self):
        return self._key

    def __str__(self):
        return self._key.hex()

    def __repr__(self):
        return str(self)


class _RSA_KEYPAIR(_BASIC_KEYPAIR):
    """You need to give a pem private key if it's in bytes"""
    public_exponent = 65537
    cipher = "RSA"

    def __init__(self, key_size: Literal[512, 768, 1024, 2048, 3072, 4096, 8192, 15360],
                 private_key: Optional[bytes | str | rsa.RSAPrivateKey] = None):
        _private_key = self._load_pem_private_key(private_key) \
            if private_key is not None else rsa.generate_private_key(public_exponent=self.public_exponent,
                                                                     key_size=key_size)
        if _private_key.key_size != key_size:
            raise ValueError(f"Key size of given private key ({_private_key.key_size}) "
                             f"doesn't match the specified key size ({key_size})")
        _public_key = _private_key.public_key()
        super().__init__(_private_key, _public_key)


class _DSA_KEYPAIR(_BASIC_KEYPAIR):
    cipher = "DSA"

    def __init__(self, key_size: Literal[1024, 2048, 3072],
                 private_key: Optional[bytes | str | dsa.DSAPrivateKey] = None):
        _private_key = self._load_pem_private_key(private_key) \
            if private_key is not None else dsa.generate_private_key(key_size=key_size)

        if _private_key.key_size != key_size:
            raise ValueError(f"Key size of given private key ({_private_key.key_size}) "
                             f"doesn't match the specified key size ({key_size})")
        _public_key = _private_key.public_key()
        super().__init__(_private_key, _public_key)


class ECC_CURVE:
    """Elliptic key functions"""
    SECP192R1 = ec.SECP192R1
    SECP224R1 = ec.SECP224R1
    SECP256K1 = ec.SECP256K1
    SECP256R1 = ec.SECP256R1  # Default
    SECP384R1 = ec.SECP384R1
    SECP521R1 = ec.SECP521R1
    SECT163K1 = ec.SECT163K1
    SECT163R2 = ec.SECT163R2
    SECT233K1 = ec.SECT233K1
    SECT233R1 = ec.SECT233R1
    SECT283K1 = ec.SECT283K1
    SECT283R1 = ec.SECT283R1
    SECT409K1 = ec.SECT409K1
    SECT409R1 = ec.SECT409R1
    SECT571K1 = ec.SECT571K1
    SECT571R1 = ec.SECT571R1


class ECC_TYPE:
    """How the signing is done, heavily affects the performance, key generation and what you can do with it"""
    ECDSA = enum_auto()  # Elliptic Curve Digital Signature Algorithm
    Ed25519 = ed25519.Ed25519PrivateKey
    Ed448 = ed448.Ed448PrivateKey
    X25519 = x25519.X25519PrivateKey
    X448 = x448.X448PrivateKey


class _ECC_KEYPAIR(_BASIC_KEYPAIR):
    cipher = "ECC"

    def __init__(self, ecc_type: Union[ECC_TYPE.ECDSA, ECC_TYPE.Ed25519] | ECC_TYPE.Ed448 | ECC_TYPE.X25519 | ECC_TYPE.X448 = ECC_TYPE.ECDSA,
                 ecc_curve: Optional[ec.SECP192R1 | ec.SECP224R1 | ec.SECP256K1 | ec.SECP256R1 |
                                     ec.SECP384R1 | ec.SECP521R1 | ec.SECT163K1 | ec.SECT163R2 |
                                     ec.SECT233K1 | ec.SECT233R1 | ec.SECT283K1 | ec.SECT283R1 |
                                     ec.SECT409K1 | ec.SECT409R1 | ec.SECT571K1 | ec.SECT571R1] = ECC_CURVE.SECP256R1,
                 private_key: Optional[bytes | str] = None):
        if private_key is None:
            if ecc_type == ECC_TYPE.ECDSA:
                _private_key = ec.generate_private_key(ecc_curve())
            else:
                if ecc_curve is not None:
                    raise ValueError("You can't use an ECC curve when you aren't using the ECC Type ECDSA. "
                                     "Please set it to None instead.")
                _private_key = ecc_type.generate()
        else:
            _private_key = self._load_pem_private_key(private_key)

        _public_key = _private_key.public_key()
        super().__init__(_private_key, _public_key)


class _KYBER_KEYPAIR(_BASIC_KEYPAIR):
    cipher = "KYBER"

    def __init__(self):
        if Kyber is None:
            raise EnvironmentError("Module QuantCrypt is not installed.")
        _public_key, _private_key = Kyber().keygen()
        super().__init__(_private_key, _public_key)

    def get_private_bytes(self) -> bytes:
        """Returns the private key in a byte format"""
        return self._private_key

    def get_public_bytes(self) -> bytes:
        """Returns the public key in a byte format"""
        return self._public_key

    def encrypt(self, plaintext_path_or_file: Union[bytes, IO, Path],
                      get: Literal["content", "path", "file"] = "content") -> Union[bytes, Path, IO]:
        """
        Encrypts a file using the Kyber public key.
        """
        if Kyber is None:
            raise EnvironmentError("Module QuantCrypt is not installed.")
        krypton = KryptonKEM(Kyber)
        temp_dir = mkdtemp()
        if isinstance(plaintext_path_or_file, (bytes, IO)):
            plaintext_file = Path(os.path.join(temp_dir, "kyper_inp"))

            if isinstance(plaintext_path_or_file, IO):
                with plaintext_path_or_file as f:
                    plaintext_path_or_file = f.read()

            with open(plaintext_file, "wb") as f:
                f.write(plaintext_path_or_file)
        elif isinstance(plaintext_path_or_file, Path):
            plaintext_file = plaintext_path_or_file
        else:
            raise ValueError("Please only input accepted types as plaintext.")
        ciphertext_file = Path(os.path.join(temp_dir, "kyper_out"))
        krypton.encrypt(self._public_key, plaintext_file, ciphertext_file)

        if not isinstance(plaintext_path_or_file, Path):
            safe_remove(plaintext_file)
        if get == "path":
            return ciphertext_file
        elif get == "file":
            return open(ciphertext_file, "rb")
        with open(ciphertext_file, "rb") as f:
            content = f.read()
        safe_remove(temp_dir)
        return content

    def decrypt(self, ciphertext_path_or_file: Union[bytes, IO, Path],
                      get: Literal["content", "path", "file"] = "content") -> Union[bytes, Path, IO]:
        """
        Decrypts a file to memory using the Kyber secret key.
        """
        if Kyber is None:
            raise EnvironmentError("Module QuantCrypt is not installed.")
        krypton = KryptonKEM(Kyber)
        temp_dir = mkdtemp()
        if isinstance(ciphertext_path_or_file, (bytes, IO)):
            ciphertext_file = Path(os.path.join(temp_dir, "kyper_inp"))

            if isinstance(ciphertext_path_or_file, IO):
                with ciphertext_path_or_file as f:
                    ciphertext_path_or_file = f.read()

            with open(ciphertext_file, "wb") as f:
                f.write(ciphertext_path_or_file)
        elif isinstance(ciphertext_path_or_file, Path):
            ciphertext_file = ciphertext_path_or_file
        else:
            raise ValueError("Please only input accepted types as ciphertext.")
        plaintext_file = Path(os.path.join(temp_dir, "kyper_out"))
        krypton.decrypt_to_file(self._secret_key, ciphertext_file, plaintext_file)

        if not isinstance(ciphertext_path_or_file, Path):
            safe_remove(ciphertext_file)
        if get == "path":
            return plaintext_file
        elif get == "file":
            return open(plaintext_file, "rb")
        with open(plaintext_file, "rb") as f:
            content = f.read()
        safe_remove(temp_dir)
        return content

    def __str__(self):
        return self.get_public_bytes().hex()
