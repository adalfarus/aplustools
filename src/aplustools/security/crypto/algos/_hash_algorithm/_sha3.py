"""SHA3"""
from ..._definitions import _HASHER_BACKEND, _HASHER_WITH_LEN_BACKEND, _BASIC_HASHER
from ...exceptions import NotSupportedError as _NotSupportedError

import collections.abc as _a
import typing as _ty

SHA224: _HASHER_BACKEND = _HASHER_BACKEND("sha3_224")
SHA256: _HASHER_BACKEND = _HASHER_BACKEND("sha3_256")
SHA384: _HASHER_BACKEND = _HASHER_BACKEND("sha3_384")
SHA512: _HASHER_BACKEND = _HASHER_BACKEND("sha3_512")
SHAKE128: _HASHER_WITH_LEN_BACKEND = _HASHER_WITH_LEN_BACKEND("sha3_shake_128")
SHAKE256: _HASHER_WITH_LEN_BACKEND = _HASHER_WITH_LEN_BACKEND("sha3_shake_256")
TurboSHAKE128: _HASHER_BACKEND = _HASHER_BACKEND("sha3_turbo_shake_128")
TurboSHAKE256: _HASHER_BACKEND = _HASHER_BACKEND("sha3_turbo_shake_256")
KangarooTwelve: _HASHER_BACKEND = _HASHER_BACKEND("sha3_kangaroo_twelve")
TupleHash128: _HASHER_BACKEND = _HASHER_BACKEND("sha3_tuple_hash_128")
TupleHash256: _HASHER_BACKEND = _HASHER_BACKEND("sha3_tuple_hash_256")
keccak: _HASHER_BACKEND = _HASHER_BACKEND("sha3_keccak")


class CSHAKE128(_BASIC_HASHER):
    _IMPLS: tuple[_a.Callable[[bytes, int, bytes, bytes], bytes], _a.Callable[[bytes, bytes, int, bytes, bytes], bool]]
    algorithm: str = "sha3_cshake_128"

    @classmethod
    def hash(cls, data: bytes, length: int = 32, *, custom: bytes = b"", function_name: bytes = b"") -> bytes:
        impl = cls._IMPLS
        if impl is None:
            raise _NotSupportedError(f"The {cls()} hash is not supported by this backend")
        return impl[0](data, length, custom, function_name)

    @classmethod
    def verify(cls, to_verify: bytes, original_hash: bytes, length: int, custom: bytes = b"", function_name: bytes = b"") -> bool:
        impl = cls._IMPLS
        if impl is None:
            raise _NotSupportedError(f"The {cls()} hash is not supported by this backend")
        return impl[1](to_verify, original_hash, length, custom, function_name)

    def __str__(self) -> str:
        return self.algorithm


class CSHAKE256(_BASIC_HASHER):
    _IMPLS: tuple[_a.Callable[[bytes, int, bytes, bytes], bytes], _a.Callable[[bytes, bytes, int, bytes, bytes], bool]]
    algorithm: str = "sha3_cshake_256"

    @classmethod
    def hash(cls, data: bytes, length: int = 32, *, custom: bytes = b"", function_name: bytes = b"") -> bytes:
        impl = cls._IMPLS
        if impl is None:
            raise _NotSupportedError(f"The {cls()} hash is not supported by this backend")
        return impl[0](data, length, custom, function_name)

    @classmethod
    def verify(cls, to_verify: bytes, original_hash: bytes, length: int, custom: bytes = b"", function_name: bytes = b"") -> bool:
        impl = cls._IMPLS
        if impl is None:
            raise _NotSupportedError(f"The {cls()} hash is not supported by this backend")
        return impl[1](to_verify, original_hash, length, custom, function_name)

    def __str__(self) -> str:
        return self.algorithm
