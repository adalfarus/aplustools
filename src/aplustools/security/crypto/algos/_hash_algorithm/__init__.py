"""Provides an easy way for the user to specify a hash algorithm."""
from . import _sha2 as SHA2, _sha3 as SHA3, _blake2 as BLAKE2

SHA1: int = 4
MD2: int = 25
MD4: int = 26
MD5: int = 27
SM3: int = 28
RIPEMD160: int = 29
BCRYPT: int = 30
ARGON2: int = 31

def _extract_algorithm_names() -> dict[str, int]:
    ids = {}
    for name, value in globals().items():
        if not name.startswith('__'):
            if isinstance(value, int):
                ids[name] = value
            else:
                for name2, value2 in {x: getattr(value, x) for x in dir(value)}.items():
                    if not name2.startswith('__'):
                        ids[name + name2] = value2
    return ids

algorithm_ids: dict[str, int] = _extract_algorithm_names()
algorithm_names: dict[int, str] = {v: k for k, v in algorithm_ids.items()}
