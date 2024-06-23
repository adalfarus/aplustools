from aplustools.data import enum_auto


class _SHA2:
    """SHA2"""
    SHA224 = enum_auto()
    SHA256 = enum_auto()
    SHA384 = enum_auto()
    SHA512 = enum_auto()
    SHA512_244 = enum_auto()
    SHA512_256 = enum_auto()


class _SHA3:
    """SHA3"""
    SHA224 = enum_auto()
    SHA256 = enum_auto()
    SHA384 = enum_auto()
    SHA512 = enum_auto()
    SHAKE128 = enum_auto()
    SHAKE256 = enum_auto()


class _BLAKE2:
    """BLAKE2"""
    BLAKE2b = enum_auto()
    BLAKE2s = enum_auto()


class HashAlgorithm:
    """Provides an easy way for the user to specify a hash algorithm."""
    SHA1 = enum_auto()
    SHA2 = _SHA2
    SHA3 = _SHA3
    BLAKE2 = _BLAKE2
    MD5 = enum_auto()
    SM3 = enum_auto()
    BCRYPT = enum_auto()
    ARGON2 = enum_auto()
