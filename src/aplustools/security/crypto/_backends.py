"""TBA"""
from .. import GenericLabeledEnum as _GenericLabeledEnum


class Backend(_GenericLabeledEnum):
    """One of the cryptography backends"""
    cryptography = ("aplustools.security.crypto._crypto", "Cryptography backend")
    pycryptodomex = ("aplustools.security.crypto._pycrypto", "PyCryptodomeX backend")
