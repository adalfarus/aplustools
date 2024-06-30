from ...data import enum_auto as _enum_auto


class Backend:
    """One of the cryptography backends"""
    cryptography = _enum_auto()
    pycryptodomex = _enum_auto()
