from ...data import enum_auto


class MainBackend:
    """One of the cryptography backends"""
    cryptography = enum_auto()
    PyCryptodom = enum_auto()
