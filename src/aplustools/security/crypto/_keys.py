from typing import NewType, IO, Union, Literal, Optional
from pathlib import Path
from tempfile import mkdtemp
import os

from ...io.environment import safe_remove
from .algorithms import Sym, ASym


try:
    from quantcrypt.kem import Kyber
    from quantcrypt.cipher import KryptonKEM
    from quantcrypt.dss import Dilithium
    from quantcrypt.kdf import Argon2, KKDF
    from quantcrypt import errors
except ImportError:
    Kyber = KryptonKEM = Dilithium = Argon2 = errors = None


class _BASIC_KEY:
    cipher_type = Sym
    cipher = None
    backend = None

    def __init__(self, key: bytes, original_key):
        self._key = key
        self._original_key = original_key

    def get_key(self) -> bytes:
        """Get the key"""
        return self._key

    def get_original_key(self) -> str:
        """Get the original key used to generate the key"""
        return self._original_key

    def __bytes__(self):
        return self._key

    def __str__(self):
        return self._key.hex()

    def __repr__(self):
        return str(self)


class _BASIC_KEYPAIR:
    cipher_type = ASym
    cipher = None
    backend = None

    def __init__(self, private_key, public_key):
        self._private_key = private_key
        self._public_key = public_key

    @staticmethod
    def _load_pem_private_key(key_to_load: bytes | str):
        raise NotImplementedError()

    def get_private_key(self):
        """Returns the private key"""
        return self._private_key

    def get_public_key(self):
        """Returns the public key"""
        return self._public_key

    def get_private_bytes(self) -> bytes:
        """Returns the private key in a byte format"""
        raise NotImplementedError()

    def get_public_bytes(self) -> bytes:
        """Returns the public key in a byte format"""
        raise NotImplementedError()

    def __bytes__(self):
        return self.get_public_bytes()

    def __str__(self):
        return bytes(self).decode()

    def __repr__(self):
        return str(self)


_BASIC_KEY_TYPE = NewType("_BASIC_KEY_TYPE", _BASIC_KEY)
_BASIC_KEYPAIR_TYPE = NewType("_BASIC_KEYPAIR_TYPE", _BASIC_KEYPAIR)


class _KYBER_KEYPAIR(_BASIC_KEYPAIR):
    cipher = ASym.Cipher.KYBER

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
        krypton.decrypt_to_file(self._private_key, ciphertext_file, plaintext_file)

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


class _DILITHIUM_KEYPAIR(_BASIC_KEYPAIR):
    cipher = ASym.Cipher.DILITHIUM

    def __init__(self):
        if Dilithium is None:
            raise EnvironmentError("Module QuantCrypt is not installed.")
        _public_key, _private_key = Dilithium().keygen()
        super().__init__(_private_key, _public_key)

    def sign(self, message: bytes) -> Optional[bytes]:
        if Dilithium is None:
            raise EnvironmentError("Module QuantCrypt is not installed.")
        try:
            return Dilithium().sign(self._private_key, message)
        except errors.DSSSignFailedError:
            return None

    def verify(self, message: bytes, signature: bytes) -> bool:
        if Dilithium is None:
            raise EnvironmentError("Module QuantCrypt is not installed.")
        try:
            return Dilithium().verify(self._public_key, message, signature)
        except errors.DSSVerifyFailedError:
            return False

    def __str__(self):
        return self.get_public_bytes().hex()
