"""Provides all enums for symmetric cryptography operations"""
import enum

from . import _cipher as Cipher

import typing as _ty

__all__ = ["Cipher", "Operation", "Padding", "KeyEncoding"]


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
    HEX = (None, "")
    RAW = (None, "")
    ASCII = (None, "")
    BASE16 = (None, "")
    BASE32 = (None, "")
    BASE64 = (None, "")
