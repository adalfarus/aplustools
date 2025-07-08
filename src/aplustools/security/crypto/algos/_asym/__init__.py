"""Provides all enums for asymmetric cryptography operations"""
import enum

from . import _cipher as Cipher

import typing as _ty

__all__ = ["Cipher", "Padding", "KeyEncoding"]


class Padding(enum.Enum):
    """Asymmetric Encryption Padding Schemes"""
    PKCShash1v15 = (0, "")
    OAEP = (1, "")
    PSS = (2, "")

class KeyEncoding(enum.Enum):
    PEM = (3, "")
    PKCS8 = (4, "")
    ASN1_DER = (5, "")
    OPENSSH = (6, "")
