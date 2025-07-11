from argon2.low_level import hash_secret, hash_secret_raw, Type as Argon2Type, verify_secret


def hash_argon2(password: bytes, salt: bytes, time_cost: int, memory_cost: int, parallelism: int, hash_len: int,
                variant: str) -> bytes:
    return hash_secret(
        secret=password,
        salt=salt,
        time_cost=time_cost,
        memory_cost=memory_cost,
        parallelism=parallelism,
        hash_len=hash_len,
        type={"i": Argon2Type.I, "d": Argon2Type.D, "id": Argon2Type.ID}[variant]
    )


def hash_verify_argon2(password: bytes, expected_hash: bytes, variant: str) -> bool:
    try:
        verify_secret(expected_hash, password, {"i": Argon2Type.I, "d": Argon2Type.D, "id": Argon2Type.ID}[variant])
    except:
        return False
    return True


def derive_argon2(password: bytes, salt: bytes, length: int = 32, time_cost: int = 2,
                  memory_cost: int = 102_400, parallelism: int = 8, type_: str = "id") -> bytes:
    if type_ not in {"i", "d", "id"}:
        raise ValueError("Invalid Argon2 type. Use 'i', 'd', or 'id'.")
    argon2_type = {"i": Argon2Type.I, "d": Argon2Type.D, "id": Argon2Type.ID}[type_]
    return hash_secret_raw(
        secret=password,
        salt=salt,
        time_cost=time_cost,
        memory_cost=memory_cost,
        parallelism=parallelism,
        hash_len=length,
        type=argon2_type
    )
