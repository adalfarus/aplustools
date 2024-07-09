from ...data import EANEnum


class _SHA2(EANEnum):
    """SHA2"""
    SHA224 = 5, ""
    SHA256 = 6, ""
    SHA384 = 7, ""
    SHA512 = 8, ""
    SHA512_244 = 9, ""
    SHA512_256 = 10, ""


class _SHA3(EANEnum):
    """SHA3"""
    SHA224 = 11, ""
    SHA256 = 12, ""
    SHA384 = 13, ""
    SHA512 = 14, ""
    SHAKE128 = 15, ""
    SHAKE256 = 16, ""
    TurboSHAKE128 = 17, ""
    TurboSHAKE256 = 18, ""
    KangarooTwelve = 19, ""
    TupleHash128 = 20, ""
    TupleHash256 = 21, ""
    keccak = 22, ""


class _BLAKE2(EANEnum):
    """BLAKE2"""
    BLAKE2b = 23, ""
    BLAKE2s = 24, ""


class HashAlgorithm(EANEnum):
    """Provides an easy way for the user to specify a hash algorithm."""
    SHA1 = 4, ""
    SHA2 = _SHA2
    SHA3 = _SHA3
    BLAKE2 = _BLAKE2
    MD2 = 25, ""
    MD4 = 26, ""
    MD5 = 27, ""
    SM3 = 28, ""
    RIPEMD160 = 29, ""
    BCRYPT = 30, ""
    ARGON2 = 31, ""


def _extract_algorithm_names():
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
