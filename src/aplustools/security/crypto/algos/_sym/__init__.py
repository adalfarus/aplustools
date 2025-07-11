"""Provides all enums for symmetric cryptography operations"""
import enum

from . import _cipher as Cipher

import typing as _ty

__all__ = ["Cipher", "Operation", "Padding", "KeyEncoding", "MessageAuthenticationCode"]


class Operation(enum.Enum):
    """Different modes of operation"""
    ECB = (None, "Electronic Codebook")
    CBC = (None, "Cipher Block Chaining")
    CFB = (None, "Cipher Feedback")
    OFB = (None, "Output Feedback")
    CTR = (None, "Counter")
    GCM = (None, "Galois/Counter Mode")

class Padding(enum.Enum):
    """Padding Schemes"""
    PKCS7 = (None, "")
    ANSIX923 = (None, "")

class KeyEncoding(enum.Enum):
    RAW = "raw"             # Pure bytes (e.g. from os.urandom)
    BASE64 = "base64"       # Base64 string
    HEX = "hex"             # Hex string (optional)
    BASE32 = "base32"       # Less common, useful for TOTP

class MessageAuthenticationCode(enum.Enum):
    """Authentication Codes"""
    HMAC = None  # Hash-based Message Authentication Code
    CMAC = None  # Cipher-based Message Authentication Code
    KMAC128 = None
    KMAC256 = None
    Poly1305 = None
