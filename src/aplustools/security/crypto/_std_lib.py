"""Fallback implementations"""
import hashlib
import hmac


def _hash_digest(data: bytes, algorithm: str) -> bytes:
    try:
        return hashlib.new(algorithm, data).digest()
    except ValueError as e:
        raise ValueError(f"Unsupported or unavailable hash algorithm: '{algorithm}'") from e

def hash_sha1(data: bytes) -> bytes:
    return _hash_digest(data, "sha1")
def hash_sha224(data: bytes) -> bytes:
    return _hash_digest(data, "sha224")
def hash_sha256(data: bytes) -> bytes:
    return _hash_digest(data, "sha256")
def hash_sha384(data: bytes) -> bytes:
    return _hash_digest(data, "sha384")
def hash_sha512(data: bytes) -> bytes:
    return _hash_digest(data, "sha512")
def hash_sha3_224(data: bytes) -> bytes:
    return _hash_digest(data, "sha3_224")
def hash_sha3_256(data: bytes) -> bytes:
    return _hash_digest(data, "sha3_256")
def hash_sha3_384(data: bytes) -> bytes:
    return _hash_digest(data, "sha3_384")
def hash_sha3_512(data: bytes) -> bytes:
    return _hash_digest(data, "sha3_512")
def hash_md2(data: bytes) -> bytes:
    """Might not work"""
    return _hash_digest(data, "md2")
def hash_md4(data: bytes) -> bytes:
    """Might not work"""
    return _hash_digest(data, "md4")
def hash_md5(data: bytes) -> bytes:
    return _hash_digest(data, "md5")
def hash_sm3(data: bytes) -> bytes:
    """Might not work"""
    return _hash_digest(data, "sm3")
def hash_ripemd160(data: bytes) -> bytes:
    """Might not work"""
    return _hash_digest(data, "ripemd160")

def hash_blake2b(data: bytes, digest_size: int = 64) -> bytes:
    if not 1 <= digest_size <= 64:
        raise ValueError("blake2b digest_size must be between 1 and 64 bytes")
    return hashlib.blake2b(data, digest_size=digest_size).digest()

def hash_blake2s(data: bytes, digest_size: int = 32) -> bytes:
    if not 1 <= digest_size <= 32:
        raise ValueError("blake2s digest_size must be between 1 and 32 bytes")
    return hashlib.blake2s(data, digest_size=digest_size).digest()

def hash_sha3_shake_128(data: bytes, length: int = 16) -> bytes:
    if length <= 0:
        raise ValueError("SHAKE128 output length must be positive")
    return hashlib.shake_128(data).digest(length)

def hash_sha3_shake_256(data: bytes, length: int = 32) -> bytes:
    if length <= 0:
        raise ValueError("SHAKE256 output length must be positive")
    return hashlib.shake_256(data).digest(length)

def hash_verify_sha1(data: bytes, expected_hash: bytes) -> bool:
    return hmac.compare_digest(expected_hash, _hash_digest(data, "sha1"))
def hash_verify_sha224(data: bytes, expected_hash: bytes) -> bool:
    return hmac.compare_digest(expected_hash, _hash_digest(data, "sha224"))
def hash_verify_sha256(data: bytes, expected_hash: bytes) -> bool:
    return hmac.compare_digest(expected_hash, _hash_digest(data, "sha256"))
def hash_verify_sha384(data: bytes, expected_hash: bytes) -> bool:
    return hmac.compare_digest(expected_hash, _hash_digest(data, "sha384"))
def hash_verify_sha512(data: bytes, expected_hash: bytes) -> bool:
    return hmac.compare_digest(expected_hash, _hash_digest(data, "sha512"))
def hash_verify_sha3_224(data: bytes, expected_hash: bytes) -> bool:
    return hmac.compare_digest(expected_hash, _hash_digest(data, "sha3_224"))
def hash_verify_sha3_256(data: bytes, expected_hash: bytes) -> bool:
    return hmac.compare_digest(expected_hash, _hash_digest(data, "sha3_256"))
def hash_verify_sha3_384(data: bytes, expected_hash: bytes) -> bool:
    return hmac.compare_digest(expected_hash, _hash_digest(data, "sha3_384"))
def hash_verify_sha3_512(data: bytes, expected_hash: bytes) -> bool:
    return hmac.compare_digest(expected_hash, _hash_digest(data, "sha3_512"))
def hash_verify_md2(data: bytes, expected_hash: bytes) -> bool:
    return hmac.compare_digest(expected_hash, _hash_digest(data, "md2"))
def hash_verify_md4(data: bytes, expected_hash: bytes) -> bool:
    return hmac.compare_digest(expected_hash, _hash_digest(data, "md4"))
def hash_verify_md5(data: bytes, expected_hash: bytes) -> bool:
    return hmac.compare_digest(expected_hash, _hash_digest(data, "md5"))
def hash_verify_sm3(data: bytes, expected_hash: bytes) -> bool:
    return hmac.compare_digest(expected_hash, _hash_digest(data, "sm3"))
def hash_verify_ripemd160(data: bytes, expected_hash: bytes) -> bool:
    return hmac.compare_digest(expected_hash, _hash_digest(data, "ripemd160"))

def hash_verify_blake2b(data: bytes, expected_hash: bytes) -> bool:
    actual = hashlib.blake2b(data, digest_size=len(expected_hash)).digest()
    return hmac.compare_digest(expected_hash, actual)

def hash_verify_blake2s(data: bytes, expected_hash: bytes) -> bool:
    actual = hashlib.blake2s(data, digest_size=len(expected_hash)).digest()
    return hmac.compare_digest(expected_hash, actual)

def hash_verify_sha3_shake_128(data: bytes, expected_hash: bytes) -> bool:
    actual = hashlib.shake_128(data).digest(len(expected_hash))
    return hmac.compare_digest(expected_hash, actual)

def hash_verify_sha3_shake_256(data: bytes, expected_hash: bytes) -> bool:
    actual = hashlib.shake_256(data).digest(len(expected_hash))
    return hmac.compare_digest(expected_hash, actual)

def derive_pbkdf1(password: bytes, salt: bytes, length: int, iterations: int, hash_alg: str) -> bytes:
    """
    Derive a key using PBKDF1 (legacy).
    """
    if not salt or len(salt) < 8:
        raise ValueError("Salt must be at least 8 bytes for PBKDF1")
    if iterations < 1:
        raise ValueError("PBKDF1 requires at least 1 iteration")

    try:
        digest_size = hashlib.new(hash_alg).digest_size
    except ValueError as e:
        raise ValueError(f"Unsupported hash algorithm: '{hash_alg}'") from e

    if length > digest_size:
        raise ValueError(f"PBKDF1 maximum output length is {digest_size} bytes for '{hash_alg}'")

    dk = password + salt
    for _ in range(iterations):
        dk = hashlib.new(hash_alg, dk).digest()
    return dk[:length]

def derive_hkdf(password: bytes, salt: bytes, info: bytes, length: int, hash_alg: str) -> bytes:
    """
    Derive a key using HKDF (RFC 5869).
    """
    try:
        hashlib.new(hash_alg)
    except ValueError as e:
        raise ValueError(f"Unsupported hash algorithm: '{hash_alg}'") from e

    def hmac_d(key: bytes, data: bytes) -> bytes:
        return hmac.new(key, data, hashlib.new(hash_alg).name).digest()

    prk = hmac_d(salt, password)

    okm, t, counter = b"", b"", 0
    while len(okm) < length:
        counter += 1
        t = hmac_d(prk, t + info + bytes([counter]))
        okm += t
    return okm[:length]

def derive_scrypt(password: bytes, salt: bytes, length: int, n: int, r: int, p: int) -> bytes:
    """
    Derive a key using scrypt.
    """
    if len(salt) < 8:
        raise ValueError("Salt must be at least 8 bytes for scrypt")
    if not all(isinstance(x, int) and x > 0 for x in (n, r, p, length)):
        raise ValueError("scrypt parameters must be positive integers")
    return hashlib.scrypt(password, salt=salt, n=n, r=r, p=p, dklen=length)

def derive_pbkdf2hmac(password: bytes, salt: bytes, length: int, iterations: int, hash_alg: str) -> bytes:
    """
    Derive a cryptographic key using PBKDF2.
    """
    if not isinstance(password, bytes):
        raise TypeError("password must be bytes")
    if not isinstance(salt, bytes):
        raise TypeError("salt must be bytes")
    if not isinstance(iterations, int) or iterations < 1:
        raise ValueError("iterations must be a positive integer")
    if not isinstance(length, int) or length < 1:
        raise ValueError("length must be a positive integer")

    try:
        return hashlib.pbkdf2_hmac(hash_alg.lower(), password, salt, iterations, dklen=length)
    except (ValueError, TypeError) as e:
        raise ValueError(f"PBKDF2 derivation failed: {e}")

def derive_concatkdf(shared_secret: bytes, length: int, otherinfo: bytes, hash_alg: str) -> bytes:
    """
    Approximate ConcatKDF from NIST SP 800-56A using hashlib.
    """
    hash_len = hashlib.new(hash_alg).digest_size
    if length > 255 * hash_len:
        raise ValueError("Cannot derive more than 255 blocks of hash_len")

    output = b""
    counter = 1
    while len(output) < length:
        h = hashlib.new(hash_alg)
        h.update(counter.to_bytes(4, "big"))
        h.update(shared_secret)
        h.update(otherinfo)
        output += h.digest()
        counter += 1
    return output[:length]
