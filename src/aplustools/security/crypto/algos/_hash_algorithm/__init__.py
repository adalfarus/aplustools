"""Provides an easy way for the user to specify a hash algorithm."""
from . import _sha2 as SHA2, _sha3 as SHA3, _blake2 as BLAKE2
from ..._definitions import _HASHER_BACKEND, _BASIC_HASHER
from ...exceptions import NotSupportedError as _NotSupportedError

import collections.abc as _a
import typing as _ty


SHA1: _HASHER_BACKEND = _HASHER_BACKEND("sha1")
MD2: _HASHER_BACKEND = _HASHER_BACKEND("md2")
MD4: _HASHER_BACKEND = _HASHER_BACKEND("md4")
MD5: _HASHER_BACKEND = _HASHER_BACKEND("md5")
SM3: _HASHER_BACKEND = _HASHER_BACKEND("sm3")
RIPEMD160: _HASHER_BACKEND = _HASHER_BACKEND("ripemd160")
BCRYPT: _HASHER_BACKEND = _HASHER_BACKEND("bcrypt")

class ARGON2(_BASIC_HASHER):
    _IMPLS: tuple[_a.Callable[[bytes, bytes, int, int, int, int, _ty.Literal["i", "d", "id"]], bytes], _a.Callable[[bytes, bytes, _ty.Literal["i", "d", "id"]], bool]]
    algorithm: str = "argon2"

    @classmethod
    def hash(cls, secret: bytes, salt: bytes, time_cost: int = 2,
             memory_cost: int = 65536, parallelism: int = 2,
             hash_len: int = 32, variant: _ty.Literal["i", "d", "id"] = "id") -> bytes:
        impl = cls._IMPLS
        if impl is None:
            raise _NotSupportedError(f"The {cls()} hash is not supported by this backend")
        return impl[0](secret, salt, time_cost, memory_cost, parallelism, hash_len, variant)

    @classmethod
    def verify(cls, to_verify: bytes, original_hash: bytes,
               variant: _ty.Literal["i", "d", "id"] = "id") -> bool:
        impl = cls._IMPLS
        if impl is None:
            raise _NotSupportedError(f"The {cls()} hash is not supported by this backend")
        return impl[1](to_verify, original_hash, variant)

    def __str__(self) -> str:
        return self.algorithm

# ARGON2: _HASHER_BACKEND = _HASHER_BACKEND(31)

def std_verify(to_verify: bytes, original_hash: bytes, /, fallback_algorithm: str = "sha256", text_ids: bool = True) -> bool:
    return _HASHER_BACKEND.verify_unknown(to_verify, original_hash, fallback_algorithm=fallback_algorithm, text_ids=text_ids)

# def _extract_algorithm_names() -> dict[str, int]:
#     ids = {}
#     for name, value in globals().items():
#         if not name.startswith('__'):
#             if isinstance(value, int):
#                 ids[name] = value
#             else:
#                 for name2, value2 in {x: getattr(value, x) for x in dir(value)}.items():
#                     if not name2.startswith('__'):
#                         ids[name + name2] = value2
#     return ids
#
# algorithm_ids: dict[str, int] = _extract_algorithm_names()
# algorithm_names: dict[int, str] = {v: k for k, v in algorithm_ids.items()}
