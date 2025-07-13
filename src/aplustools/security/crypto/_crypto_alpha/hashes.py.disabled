from cryptography.hazmat.primitives import hashes

from .._hashes import HashAlgorithm, algorithm_names
from ..exceptions import NotSupportedError

from typing import Optional


# Function to create a hash object with special handling for SHAKE algorithms
def _create_digest(algorithm, digest_size: Optional[int] = None):
    if algorithm in (hashes.SHAKE128, hashes.SHAKE256, hashes.BLAKE2b):
        if digest_size is None:
            digest_size = 32  # default size in bytes (256 bits)
        digest = hashes.Hash(algorithm(digest_size))
    elif algorithm == hashes.BLAKE2s:
        digest = hashes.Hash(algorithm(32))
    else:
        digest = hashes.Hash(algorithm())
    return digest


def hash(to_hash: bytes, algo: int, hash_check: bytes = None):
    """Hashes a specific hash using cryptography"""
    _hash_algorithm_map: dict[int, type] = {
        HashAlgorithm.SHA1: hashes.SHA1,
        HashAlgorithm.SHA2.SHA224: hashes.SHA224,
        HashAlgorithm.SHA2.SHA256: hashes.SHA256,
        HashAlgorithm.SHA2.SHA384: hashes.SHA384,
        HashAlgorithm.SHA2.SHA512: hashes.SHA512,
        HashAlgorithm.SHA2.SHA512_244: hashes.SHA512_224,
        HashAlgorithm.SHA2.SHA512_256: hashes.SHA512_256,
        HashAlgorithm.SHA3.SHA224: hashes.SHA3_224,
        HashAlgorithm.SHA3.SHA256: hashes.SHA3_256,
        HashAlgorithm.SHA3.SHA384: hashes.SHA3_384,
        HashAlgorithm.SHA3.SHA512: hashes.SHA3_512,
        HashAlgorithm.SHA3.SHAKE128: hashes.SHAKE128,
        HashAlgorithm.SHA3.SHAKE256: hashes.SHAKE256,
        HashAlgorithm.BLAKE2.BLAKE2s: hashes.BLAKE2s,
        HashAlgorithm.BLAKE2.BLAKE2b: hashes.BLAKE2b,
        HashAlgorithm.MD5: hashes.MD5,
        HashAlgorithm.SM3: hashes.SM3
    }
    algorithm = _hash_algorithm_map.get(algo, None)
    if algorithm is not None:
        digest = _create_digest(algorithm, 64)
        digest.update(to_hash)
        return digest.finalize()
    raise NotSupportedError(f"Algorithm '{algorithm_names[algo]}' is not supported by this backend")
