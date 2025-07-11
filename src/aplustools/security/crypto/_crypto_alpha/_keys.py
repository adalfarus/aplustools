from cryptography.hazmat.primitives import hashes, hmac, cmac, padding as sym_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.constant_time import bytes_eq

from .._definitions import _AES_KEYTYPE, _AES_KEYLITERAL
from ..algos._sym import (Operation as SymOperation, Padding as SymPadding,
                          KeyEncoding as SymKeyEncoding, MessageAuthenticationCode as MAC)

import os

import collections.abc as _a
import typing as _ty
import types as _ts

# --------------- Utilities ---------------

_OPERATION_MAP = {
    SymOperation.ECB: lambda iv=None: modes.ECB(),
    SymOperation.CBC: lambda iv: modes.CBC(iv),
    SymOperation.CFB: lambda iv: modes.CFB(iv),
    SymOperation.OFB: lambda iv: modes.OFB(iv),
    SymOperation.CTR: lambda iv: modes.CTR(iv),
    SymOperation.GCM: lambda iv, tag=None: modes.GCM(iv, tag) if tag else modes.GCM(iv),
}

def _derive_key_from_password(password: str | bytes, length: int, salt: bytes) -> bytes:
    """Derive a key from a password using PBKDF2."""
    if isinstance(password, str):
        password = password.encode('utf-8')
    salt = salt
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        iterations=100_000,
        backend=default_backend()
    )
    key = kdf.derive(password)
    return key


# --------------- Keys ---------------

class _AES_KEY2(_AES_KEYTYPE):
    __concrete__ = True

    def __init__(self, key_size: _AES_KEYLITERAL, pwd: _ty.Optional[bytes | str]) -> None:
        self._key: bytes
        if pwd is None:
            self._key = os.urandom(key_size // 8)
        else:
            pwd8 = (pwd * ((8 // len(pwd)) + 1))[:8]
            if isinstance(pwd8, str):
                pwd8 = pwd8.encode("utf-8")
            self._key = _derive_key_from_password(pwd, key_size // 8, pwd8)

    def encrypt(self, plain_bytes: bytes, padding: SymPadding, mode: SymOperation, /, *, auto_pack: bool = True) -> dict[str, bytes]:
        iv = os.urandom(12)
        crypt_mode = _OPERATION_MAP[mode](iv)
        cipher = Cipher(algorithms.AES(self._key), crypt_mode)
        enc = cipher.encryptor()
        ct = enc.update(plain_bytes) + enc.finalize()
        return {"ciphertext": ct, "tag": enc.tag, "iv": iv}

    def decrypt(self, cipher_bytes_or_dict: bytes | dict[str, bytes], padding: SymPadding, mode: SymOperation, /, *, auto_pack: bool = True) -> bytes:
        iv = cipher_bytes_or_dict["iv"]
        tag = cipher_bytes_or_dict["tag"]
        ct = cipher_bytes_or_dict["ciphertext"]
        cipher = Cipher(algorithms.AES(self._pwd), modes.GCM(iv, tag), backend=self.backend)
        dec = cipher.decryptor()
        return dec.update(ct) + dec.finalize()

    def generate_mac(self, data: bytes, auth_type):
        raise _NotSupportedError("Switch to AEAD GCM for MAC with AES.")

    def verify_mac(self, data: bytes, mac: bytes, auth_type) -> bool:
        raise _NotSupportedError("Switch to AEAD GCM for MAC with AES.")
