import os

from Cryptodome.Hash import MD2, MD4, MD5, SHA1, SHA224, SHA256, SHA384, SHA512
from Cryptodome.Hash import SHA3_224, SHA3_256, SHA3_384, SHA3_512
from Cryptodome.Hash import SHAKE128, SHAKE256
from Cryptodome.Hash import BLAKE2s, BLAKE2b
from Cryptodome.Hash import RIPEMD160
from Cryptodome.Hash import TurboSHAKE128, TurboSHAKE256
from Cryptodome.Hash import TupleHash128, TupleHash256
from Cryptodome.Hash import KangarooTwelve
from Cryptodome.Hash import keccak
from Cryptodome.Protocol.KDF import bcrypt, bcrypt_check


from .._hashes import HashAlgorithm, algorithm_names
from ..exceptions import NotSupportedError

from typing import Optional


# Function to create a hash object with special handling for SHAKE algorithms
def _create_hash(algorithm, data: bytes, digest_size: Optional[int] = None, hash_check: bytes = None):
    if algorithm in (SHAKE128, SHAKE256, TurboSHAKE128, TurboSHAKE256, KangarooTwelve):
        if digest_size is None:
            digest_size = 32  # default size in bytes (256 bits)
        h = algorithm.new()
        h.update(data)
        hash = h.read(digest_size)
    elif algorithm in (keccak, TupleHash128, TupleHash256):
        if digest_size is None:
            digest_size = 32  # default size in bytes (256 bits)
        h = algorithm.new(digest_bytes=digest_size)
        h.update(data)
        hash = h.digest()
    elif algorithm == bcrypt:
        if hash_check:
            try:
                bcrypt_check(data, hash_check)
            except ValueError:
                return False
            return True
        return bcrypt(data, 12, os.urandom(16))
    else:
        h = algorithm.new()
        h.update(data)
        hash = h.digest()
    return hash


def hash(to_hash: bytes, algo: int, hash_check: bytes = None):
    """Hashes a specific hash using pycryptodomex"""
    _hash_algorithm_map: dict[int, type] = {
        HashAlgorithm.SHA1: SHA1,
        HashAlgorithm.SHA2.SHA224: SHA224,
        HashAlgorithm.SHA2.SHA256: SHA256,
        HashAlgorithm.SHA2.SHA384: SHA384,
        HashAlgorithm.SHA2.SHA512: SHA512,
        HashAlgorithm.SHA3.SHA224: SHA3_224,
        HashAlgorithm.SHA3.SHA256: SHA3_256,
        HashAlgorithm.SHA3.SHA384: SHA3_384,
        HashAlgorithm.SHA3.SHA512: SHA3_512,
        HashAlgorithm.SHA3.SHAKE128: SHAKE128,
        HashAlgorithm.SHA3.SHAKE256: SHAKE256,
        HashAlgorithm.BLAKE2.BLAKE2s: BLAKE2s,
        HashAlgorithm.BLAKE2.BLAKE2b: BLAKE2b,
        HashAlgorithm.MD2: MD2,
        HashAlgorithm.MD4: MD4,
        HashAlgorithm.MD5: MD5,
        HashAlgorithm.RIPEMD160: RIPEMD160,
        HashAlgorithm.SHA3.TurboSHAKE128: TurboSHAKE128,
        HashAlgorithm.SHA3.TurboSHAKE256: TurboSHAKE256,
        HashAlgorithm.SHA3.TupleHash128: TupleHash128,
        HashAlgorithm.SHA3.TupleHash256: TupleHash256,
        HashAlgorithm.SHA3.KangarooTwelve: KangarooTwelve,
        HashAlgorithm.SHA3.keccak: keccak,
        HashAlgorithm.BCRYPT: bcrypt
    }
    algorithm = _hash_algorithm_map.get(algo, None)
    if algorithm is not None:
        return _create_hash(algorithm, to_hash, 64, hash_check)
    raise NotSupportedError(f"Algorithm '{algorithm_names[algo]}' is not supported by this backend")
