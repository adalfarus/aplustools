"""TBA"""
import shutil
from pathlib import Path as PLPath
from tempfile import mkdtemp
import os

from ._algorithms import Sym, ASym, _BASIC_KEYTYPE, _BASIC_KEYPAIRTYPE

# Standard typing imports for aps
import typing_extensions as _te
import collections.abc as _a
import typing as _ty
if _ty.TYPE_CHECKING:
    import _typeshed as _tsh
import types as _ts

try:
    from quantcrypt.kem import Kyber
    from quantcrypt.cipher import KryptonKEM
    from quantcrypt.dss import Dilithium
    from quantcrypt.kdf import Argon2, KKDF
    from quantcrypt import errors
except ImportError:
    Kyber = KryptonKEM = Dilithium = Argon2 = KKDF = errors = None


# TODO: Move to _fallbacks
class _KYBER_KEYPAIR(_BASIC_KEYPAIRTYPE):
    cipher = ASym.Cipher.KYBER  # type: ignore

    def __init__(self):
        if Kyber is None:
            raise EnvironmentError("Module QuantCrypt is not installed.")
        self._public_key, self._private_key = Kyber().keygen()

    def get_private_key(self):
        """Returns the private key"""
        return self._private_key

    def get_public_key(self):
        """Returns the public key"""
        return self._public_key

    def get_private_bytes(self) -> bytes:
        """Returns the private key in a byte format"""
        return self._private_key

    def get_public_bytes(self) -> bytes:
        """Returns the public key in a byte format"""
        return self._public_key

    def encrypt(self, plaintext_path_or_file: bytes | _ty.IO[bytes] | PLPath,
                get: _ty.Literal["content", "path", "file"] = "content") -> bytes | PLPath | _ty.IO[bytes]:
        """
        Encrypts a file using the Kyber public key.
        """
        if Kyber is None:
            raise EnvironmentError("Module QuantCrypt is not installed.")
        krypton = KryptonKEM(Kyber)
        temp_dir = mkdtemp()
        if isinstance(plaintext_path_or_file, (bytes, _ty.IO)):
            plaintext_file = PLPath(os.path.join(temp_dir, "kyper_inp"))

            content: bytes
            if isinstance(plaintext_path_or_file, _ty.IO):
                with plaintext_path_or_file as f:
                    content = f.read()
            else:
                content = plaintext_path_or_file

            with open(plaintext_file, "wb") as f:
                f.write(content)
        elif isinstance(plaintext_path_or_file, PLPath):
            plaintext_file = plaintext_path_or_file
        else:
            raise ValueError("Please only input accepted types as plaintext.")
        ciphertext_file = PLPath(os.path.join(temp_dir, "kyper_out"))
        krypton.encrypt(self._public_key, plaintext_file, ciphertext_file)

        if not isinstance(plaintext_path_or_file, PLPath):
            os.remove(plaintext_file)
        if get == "path":
            return ciphertext_file
        elif get == "file":
            return open(ciphertext_file, "rb")
        with open(ciphertext_file, "rb") as f:
            content = f.read()
        shutil.rmtree(temp_dir)
        return content

    def decrypt(self, ciphertext_path_or_file: bytes | _ty.IO[bytes] | PLPath,
                get: _ty.Literal["content", "path", "file"] = "content") -> bytes | _ty.IO[bytes] | PLPath:
        """
        Decrypts a file to memory using the Kyber secret key.
        """
        if Kyber is None:
            raise EnvironmentError("Module QuantCrypt is not installed.")
        krypton = KryptonKEM(Kyber)
        temp_dir = mkdtemp()
        if isinstance(ciphertext_path_or_file, (bytes, _ty.IO)):
            ciphertext_file = PLPath(os.path.join(temp_dir, "kyper_inp"))

            content: bytes
            if isinstance(ciphertext_path_or_file, _ty.IO):
                with ciphertext_path_or_file as f:
                    content = f.read()
            else:
                content = ciphertext_path_or_file

            with open(ciphertext_file, "wb") as f:
                f.write(content)
        elif isinstance(ciphertext_path_or_file, PLPath):
            ciphertext_file = ciphertext_path_or_file
        else:
            raise ValueError("Please only input accepted types as ciphertext.")
        plaintext_file = PLPath(os.path.join(temp_dir, "kyper_out"))
        krypton.decrypt_to_file(self._private_key, ciphertext_file, plaintext_file)

        if not isinstance(ciphertext_path_or_file, PLPath):
            os.remove(ciphertext_file)
        if get == "path":
            return plaintext_file
        elif get == "file":
            return open(plaintext_file, "rb")
        with open(plaintext_file, "rb") as f:
            content = f.read()
        shutil.rmtree(temp_dir)
        return content

    def __bytes__(self) -> bytes:
        return self.get_public_bytes()

    def __str__(self):
        return self.get_public_bytes().hex()

    def __repr__(self) -> str:
        return str(self)


class _DILITHIUM_KEYPAIR(_BASIC_KEYPAIRTYPE):
    cipher = ASym.Cipher.DILITHIUM  # type: ignore

    def __init__(self) -> None:
        if Dilithium is None:
            raise EnvironmentError("Module QuantCrypt is not installed.")
        self._public_key, self._private_key = Dilithium().keygen()

    def get_private_key(self):
        """Returns the private key"""
        return self._private_key

    def get_public_key(self):
        """Returns the public key"""
        return self._public_key

    def get_private_bytes(self) -> bytes:
        """Returns the private key in a byte format"""
        return self._private_key

    def get_public_bytes(self) -> bytes:
        """Returns the public key in a byte format"""
        return self._public_key

    def sign(self, message: bytes) -> bytes | None:
        if Dilithium is None:
            raise EnvironmentError("Module QuantCrypt is not installed.")
        try:
            return Dilithium().sign(self._private_key, message)  # type: ignore
        except errors.DSSSignFailedError:
            return None

    def verify(self, message: bytes, signature: bytes) -> bool:
        if Dilithium is None:
            raise EnvironmentError("Module QuantCrypt is not installed.")
        try:
            return Dilithium().verify(self._public_key, message, signature)  # type: ignore
        except errors.DSSVerifyFailedError:
            return False

    def __bytes__(self) -> bytes:
        return self.get_public_bytes()

    def __str__(self) -> str:
        return self.get_public_bytes().hex()

    def __repr__(self) -> str:
        return str(self)

