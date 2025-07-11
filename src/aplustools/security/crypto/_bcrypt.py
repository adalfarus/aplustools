import bcrypt


def hash_bcrypt(password: bytes) -> bytes:
    if not password:
        raise ValueError("Password must not be empty")
    return bcrypt.hashpw(password, bcrypt.gensalt())


def hash_verify_bcrypt(password: bytes, hash_: bytes) -> bool:
    if not password:
        raise ValueError("Password must not be empty")
    return bcrypt.checkpw(password, hash_)


def derive_bcrypt(password: bytes, salt: bytes, rounds: int = 12, length: int = 32) -> bytes:
    if len(salt) < 16:
        raise ValueError("Salt must be at least 16 bytes for bcrypt.kdf")
    return bcrypt.kdf(password=password, salt=salt, desired_key_bytes=length, rounds=rounds)
