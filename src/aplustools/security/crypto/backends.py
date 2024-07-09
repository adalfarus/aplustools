from ...data import EANEnum as _EANEnum


class Backend(_EANEnum):
    """One of the cryptography backends"""
    cryptography = "Cryptography backend"
    pycryptodomex = "PyCryptodomeX backend"
