"""TBA"""
from .. import EAN as _EAN


class _SHA2:
    """SHA2"""
    SHA224 = _EAN(5, "")
    SHA256 = _EAN(6, "")
    SHA384 = _EAN(7, "")
    SHA512 = _EAN(8, "")
    SHA512_244 = _EAN(9, "")
    SHA512_256 = _EAN(10, "")


class _SHA3:
    """SHA3"""
    SHA224 = _EAN(11, "")
    SHA256 = _EAN(12, "")
    SHA384 = _EAN(13, "")
    SHA512 = _EAN(14, "")
    SHAKE128 = _EAN(15, "")
    SHAKE256 = _EAN(16, "")
    TurboSHAKE128 = _EAN(17, "")
    TurboSHAKE256 = _EAN(18, "")
    KangarooTwelve = _EAN(19, "")
    TupleHash128 = _EAN(20, "")
    TupleHash256 = _EAN(21, "")
    keccak = _EAN(22, "")


class _BLAKE2:
    """BLAKE2"""
    BLAKE2b = _EAN(23, "")
    BLAKE2s = _EAN(24, "")


class HashAlgorithm:
    """Provides an easy way for the user to specify a hash algorithm."""
    SHA1 = _EAN(4, "")
    SHA2 = _SHA2
    SHA3 = _SHA3
    BLAKE2 = _BLAKE2
    MD2 = _EAN(25, "")
    MD4 = _EAN(26, "")
    MD5 = _EAN(27, "")
    SM3 = _EAN(28, "")
    RIPEMD160 = _EAN(29, "")
    BCRYPT = _EAN(30, "")
    ARGON2 = _EAN(31, "")


def _extract_algorithm_names() -> dict[str, int]:
    ids = {}
    for name, value in HashAlgorithm.__dict__.items():
        if not name.startswith('__'):
            if isinstance(value, int):
                ids[name] = value
            else:
                for name2, value2 in value.__dict__.items():
                    if not name2.startswith('__'):
                        ids[name + name2] = value2
    return ids


algorithm_ids: dict[str, int] = _extract_algorithm_names()
algorithm_names: dict[int, str] = {v: k for k, v in algorithm_ids.items()}
