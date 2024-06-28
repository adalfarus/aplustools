from ...data import enum_auto


class Backend:
    """One of the cryptography backends"""
    cryptography = enum_auto()
    pycryptodomex = enum_auto()
