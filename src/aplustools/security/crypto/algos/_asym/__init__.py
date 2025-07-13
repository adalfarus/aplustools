"""Provides all enums for asymmetric cryptography operations"""

import enum

from . import _cipher as Cipher

import typing as _ty

__all__ = ["Cipher", "Padding", "KeyFormat", "KeyEncoding"]


class Padding(enum.Enum):
    """Asymmetric Encryption Padding Schemes"""

    PKCShash1v15 = (0, "")
    OAEP = (1, "")
    PSS = (2, "")


class KeyFormat(enum.Enum):
    """TBA"""

    PKCS8 = "pkcs8"  # Private key container format (can be PEM or DER)
    PKCS1 = "pkcs1"  # for older RSA-only format
    SEC1 = "sec1"  # for EC keys
    OPENSSH = (6, "SSH public key format (e.g., ~/.ssh/id_rsa.pub)")


class KeyEncoding(enum.Enum):
    """TBA"""

    PEM = (3, "Base64 with headers, the most human-readable")
    DER = (5, "Raw binary (DER)")
    RAW = (7, "unwrapped key data (rarely used directly)")
