from cryptography.hazmat.primitives.asymmetric import rsa, dsa, ec, padding as asym_padding, ed25519, ed448, x25519, x448
from cryptography.hazmat.primitives.kdf import pbkdf2, scrypt, hkdf, concatkdf, x963kdf
from cryptography.hazmat.primitives import serialization, hashes, padding as sym_padding, hmac, cmac, poly1305
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import modes, Cipher, algorithms
from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm

from typing import Union, Literal, Optional
import warnings
import secrets
import os

from .._keys import _BASIC_KEY, _BASIC_KEYPAIR
from ..algorithms import Sym, ASym, _ECCCurve, _ECCType, KeyDerivationFunction, MessageAuthenticationCode
from ..backends import Backend
from ..exceptions import NotSupportedError


_ECC_CURVE_CONVERSION = {
    _ECCCurve.SECP192R1: ec.SECP192R1,
    _ECCCurve.SECP224R1: ec.SECP224R1,
    _ECCCurve.SECP256K1: ec.SECP256K1,
    _ECCCurve.SECP256R1: ec.SECP256R1,  # Default
    _ECCCurve.SECP384R1: ec.SECP384R1,
    _ECCCurve.SECP521R1: ec.SECP521R1,
    _ECCCurve.SECT163K1: ec.SECT163K1,
    _ECCCurve.SECT163R2: ec.SECT163R2,
    _ECCCurve.SECT233K1: ec.SECT233K1,
    _ECCCurve.SECT233R1: ec.SECT233R1,
    _ECCCurve.SECT283K1: ec.SECT283K1,
    _ECCCurve.SECT283R1: ec.SECT283R1,
    _ECCCurve.SECT409K1: ec.SECT409K1,
    _ECCCurve.SECT409R1: ec.SECT409R1,
    _ECCCurve.SECT571K1: ec.SECT571K1,
    _ECCCurve.SECT571R1: ec.SECT571R1
}
_ECC_TYPE_CONVERSION = {
    _ECCType.ECDSA: _ECCType.ECDSA,  # Catch this before conversion
    _ECCType.Ed25519: ed25519.Ed25519PrivateKey,
    _ECCType.Ed448: ed448.Ed448PrivateKey,
    _ECCType.X25519: x25519.X25519PrivateKey,
    _ECCType.X448: x448.X448PrivateKey
}
_SYM_OPERATION_CONVERSION = {
    Sym.Operation.ECB: modes.ECB,  # Electronic Codebook
    Sym.Operation.CBC: modes.CBC,  # Cipher Block Chaining
    Sym.Operation.CFB: modes.CFB,  # Cipher Feedback
    Sym.Operation.OFB: modes.OFB,  # Output Feedback
    Sym.Operation.CTR: modes.CTR,  # Counter
    Sym.Operation.GCM: modes.GCM,  # Galois/Counter Mode
}
_SYM_PADDING_CONVERSION = {
    Sym.Padding.PKCS7: sym_padding.PKCS7,
    Sym.Padding.ANSIX923: sym_padding.ANSIX923
}
_SYM_ALGORITHM_CONVERSION = {
    Sym.Cipher.AES: algorithms.AES,
    Sym.Cipher.ChaCha20: algorithms.ChaCha20,
    Sym.Cipher.TripleDES: algorithms.TripleDES,
    Sym.Cipher.Blowfish: algorithms.Blowfish,
    Sym.Cipher.CAST5: algorithms.CAST5,
    Sym.Cipher.ARC4: algorithms.ARC4,
    Sym.Cipher.Camellia: algorithms.Camellia,
    Sym.Cipher.IDEA: algorithms.IDEA,
    Sym.Cipher.SEED: algorithms.SEED,
    Sym.Cipher.SM4: algorithms.SM4
}
_ASYM_PADDING_CONVERSION = {
    ASym.Padding.PKCShash1v15: asym_padding.PKCS1v15,  # Older padding scheme for RSA
    ASym.Padding.OAEP: asym_padding.OAEP,  # Optimal Asymmetric Encryption Padding
    ASym.Padding.PSS: asym_padding.PSS  # Probabilistic Signature Scheme
}


class _BASIC_CRYPTO_KEY(_BASIC_KEY):
    backend = Backend.cryptography


class _BASIC_CRYPTO_KEYPAIR(_BASIC_KEYPAIR):
    backend = Backend.cryptography

    @staticmethod
    def _load_pem_private_key(key_to_load: bytes | str):
        if isinstance(key_to_load, (bytes, str)):
            if isinstance(key_to_load, str):
                key_to_load = bytes(key_to_load, "utf-8")
            key_to_load = serialization.load_pem_private_key(key_to_load, None, default_backend())
        return key_to_load

    def get_private_bytes(self) -> bytes:
        """Returns the private key in a byte format"""
        return self._private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

    def get_public_bytes(self) -> bytes:
        """Returns the public key in a byte format"""
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )


class _AES_KEY(_BASIC_CRYPTO_KEY):
    cipher = Sym.Cipher.AES

    def __init__(self, key_size: Literal[128, 192, 256], key: Optional[bytes | str]):
        _original_key = key if key is not None else secrets.token_hex(key_size // 8)
        if isinstance(_original_key, bytes):
            if len(_original_key) * 8 != float(key_size):
                raise ValueError(f"Key size of given key ({len(_original_key) * 8}) "
                                 f"doesn't match the specified key size ({key_size})")
            _key = _original_key
        else:
            _key = pbkdf2.PBKDF2HMAC(algorithm=hashes.SHA3_512(), length=key_size // 8, salt=os.urandom(64),
                                     iterations=800_000, backend=default_backend()).derive(_original_key.encode())
        super().__init__(_key, _original_key)


class _ChaCha20_KEY(_BASIC_CRYPTO_KEY):
    cipher = Sym.Cipher.ChaCha20

    def __init__(self, key: Optional[bytes | str] = None):
        _original_key = key if key is not None else secrets.token_hex(32)
        if isinstance(_original_key, bytes):
            if len(_original_key) != 32:
                raise ValueError("Key size for ChaCha20 must be 256 bits")
            _key = _original_key
        else:
            _key = pbkdf2.PBKDF2HMAC(algorithm=hashes.SHA3_512(), length=32, salt=os.urandom(64), iterations=800_000,
                                     backend=default_backend()).derive(_original_key.encode())
        super().__init__(_key, _original_key)


class _TripleDES_KEY(_BASIC_CRYPTO_KEY):
    cipher = Sym.Cipher.TripleDES

    def __init__(self, key_size: Literal[192], key: Optional[bytes | str] = None):
        _original_key = key if key is not None else secrets.token_hex(24)
        if isinstance(_original_key, bytes):
            if len(_original_key) != 24:
                raise ValueError("Key size for TripleDES must be 192 bits (24 bytes)")
            _key = _original_key
        else:
            _key = pbkdf2.PBKDF2HMAC(algorithm=hashes.SHA3_512(), length=key_size // 8, salt=os.urandom(64),
                                     iterations=800_000, backend=default_backend()).derive(_original_key.encode())
        super().__init__(_key, _original_key)


class _Blowfish_KEY(_BASIC_CRYPTO_KEY):
    cipher = Sym.Cipher.Blowfish

    def __init__(self, key_size: Literal[128, 256], key: Optional[bytes | str] = None):
        _original_key = key if key is not None else secrets.token_hex(key_size // 8)
        if isinstance(_original_key, bytes):
            if len(_original_key) * 8 != key_size:
                raise ValueError(f"Key size for Blowfish must be {key_size} bits")
            _key = _original_key
        else:
            _key = pbkdf2.PBKDF2HMAC(algorithm=hashes.SHA3_512(), length=key_size // 8, salt=os.urandom(64),
                                     iterations=800_000, backend=default_backend()).derive(_original_key.encode())
        super().__init__(_key, _original_key)


class _CAST5_KEY(_BASIC_CRYPTO_KEY):
    cipher = Sym.Cipher.CAST5

    def __init__(self, key_size: Literal[40, 128], key: Optional[bytes | str] = None):
        _original_key = key if key is not None else secrets.token_hex(key_size // 8)
        if isinstance(_original_key, bytes):
            if len(_original_key) * 8 != key_size:
                raise ValueError(f"Key size for CAST5 must be {key_size} bits")
            _key = _original_key
        else:
            _key = pbkdf2.PBKDF2HMAC(algorithm=hashes.SHA3_512(), length=key_size // 8, salt=os.urandom(64),
                                     iterations=800_000, backend=default_backend()).derive(_original_key.encode())
        super().__init__(_key, _original_key)


class _ARC4_KEY(_BASIC_CRYPTO_KEY):
    cipher = Sym.Cipher.ARC4

    def __init__(self, key: Optional[bytes | str] = None):
        _original_key = key if key is not None else secrets.token_hex(16)
        if isinstance(_original_key, bytes):
            if len(_original_key) != 16:
                raise ValueError("Key size for ARC4 must be 128 bits")
            _key = _original_key
        else:
            _key = pbkdf2.PBKDF2HMAC(
                algorithm=hashes.SHA3_512(),
                length=16,  # Typical key length for ARC4
                salt=os.urandom(64),
                iterations=800_000,
                backend=default_backend()
            ).derive(_original_key.encode())
        super().__init__(_key, _original_key)


class _Camellia_KEY(_BASIC_CRYPTO_KEY):
    cipher = Sym.Cipher.Camellia

    def __init__(self, key_size: Literal[128, 192, 256], key: Optional[bytes | str] = None):
        _original_key = key if key is not None else secrets.token_hex(key_size // 8)
        if isinstance(_original_key, bytes):
            if len(_original_key) * 8 != key_size:
                raise ValueError(f"Key size for Camellia must be {key_size} bits")
            _key = _original_key
        else:
            _key = pbkdf2.PBKDF2HMAC(
                algorithm=hashes.SHA3_512(),
                length=key_size // 8,
                salt=os.urandom(64),
                iterations=800_000,
                backend=default_backend()
            ).derive(_original_key.encode())
        super().__init__(_key, _original_key)


class _IDEA_KEY(_BASIC_CRYPTO_KEY):
    cipher = Sym.Cipher.IDEA

    def __init__(self, key: Optional[bytes | str] = None):
        _original_key = key if key is not None else secrets.token_hex(16)
        if isinstance(_original_key, bytes):
            if len(_original_key) != 16:
                raise ValueError("Key size for IDEA must be 128 bits")
            _key = _original_key
        else:
            _key = pbkdf2.PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=16,  # Key length for IDEA (128 bits)
                salt=os.urandom(16),
                iterations=100_000,
                backend=default_backend()
            ).derive(_original_key.encode())
        super().__init__(_key, _original_key)


class _SEED_KEY(_BASIC_CRYPTO_KEY):
    cipher = Sym.Cipher.SEED

    def __init__(self, key: Optional[bytes | str] = None):
        _original_key = key if key is not None else secrets.token_hex(16)
        if isinstance(_original_key, bytes):
            if len(_original_key) != 16:
                raise ValueError("Key size for SEED must be 128 bits")
            _key = _original_key
        else:
            _key = pbkdf2.PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=16,  # Key length for SEED (128 bits)
                salt=os.urandom(16),
                iterations=100_000,
                backend=default_backend()
            ).derive(_original_key.encode())
        super().__init__(_key, _original_key)


class _SM4_KEY(_BASIC_CRYPTO_KEY):
    cipher = Sym.Cipher.SM4

    def __init__(self, key: Optional[bytes | str] = None):
        _original_key = key if key is not None else secrets.token_hex(16)
        if isinstance(_original_key, bytes):
            if len(_original_key) != 16:
                raise ValueError("Key size for SM4 must be 128 bits")
            _key = _original_key
        else:
            _key = pbkdf2.PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=16,  # Key length for SM4 (128 bits)
                salt=os.urandom(16),
                iterations=100_000,
                backend=default_backend()
            ).derive(_original_key.encode())
        super().__init__(_key, _original_key)


_DES_KEY = _ARC2_KEY = _Salsa20_KEY = None


class _RSA_KEYPAIR(_BASIC_CRYPTO_KEYPAIR):
    """You need to give a pem private key if it's in bytes"""
    public_exponent = 65537
    cipher = ASym.Cipher.RSA

    def __init__(self, key_size: Literal[512, 768, 1024, 2048, 3072, 4096, 8192, 15360],
                 private_key: Optional[bytes | str | rsa.RSAPrivateKey] = None):
        _private_key = self._load_pem_private_key(private_key) \
            if private_key is not None else rsa.generate_private_key(public_exponent=self.public_exponent,
                                                                     key_size=key_size)
        if _private_key.key_size != key_size:
            raise ValueError(f"Key size of given private key ({_private_key.key_size}) "
                             f"doesn't match the specified key size ({key_size})")
        _public_key = _private_key.public_key()
        super().__init__(_private_key, _public_key)


class _DSA_KEYPAIR(_BASIC_CRYPTO_KEYPAIR):
    cipher = ASym.Cipher.DSA

    def __init__(self, key_size: Literal[1024, 2048, 3072],
                 private_key: Optional[bytes | str | dsa.DSAPrivateKey] = None):
        _private_key = self._load_pem_private_key(private_key) \
            if private_key is not None else dsa.generate_private_key(key_size=key_size)

        if _private_key.key_size != key_size:
            raise ValueError(f"Key size of given private key ({_private_key.key_size}) "
                             f"doesn't match the specified key size ({key_size})")
        _public_key = _private_key.public_key()
        super().__init__(_private_key, _public_key)


class _ECC_KEYPAIR(_BASIC_CRYPTO_KEYPAIR):
    cipher = ASym.Cipher.ECC

    def __init__(self, ecc_type: _ECCType = _ECCType.ECDSA,
                 ecc_curve: Optional[ec.SECP192R1 | ec.SECP224R1 | ec.SECP256K1 | ec.SECP256R1 |
                                     ec.SECP384R1 | ec.SECP521R1 | ec.SECT163K1 | ec.SECT163R2 |
                                     ec.SECT233K1 | ec.SECT233R1 | ec.SECT283K1 | ec.SECT283R1 |
                                     ec.SECT409K1 | ec.SECT409R1 | ec.SECT571K1 | ec.SECT571R1] = _ECCCurve.SECP256R1,
                 private_key: Optional[bytes | str] = None):
        if private_key is None:
            if ecc_type == _ECCType.ECDSA:
                _private_key = ec.generate_private_key(_ECC_CURVE_CONVERSION[ecc_curve]())
            else:
                if ecc_curve is not None:
                    raise ValueError("You can't use an ECC curve when you aren't using the ECC Type ECDSA. "
                                     "Please set it to None instead.")
                ecc = _ECC_TYPE_CONVERSION[ecc_type]
                _private_key = ecc.generate()
        else:
            _private_key = self._load_pem_private_key(private_key)

        _public_key = _private_key.public_key()
        super().__init__(_private_key, _public_key)


def _get_iv_nonce_size(algorithm):
    if algorithm in {Sym.Cipher.AES, Sym.Cipher.ChaCha20, Sym.Cipher.SM4, Sym.Cipher.Camellia, Sym.Cipher.SEED}:
        return 16
    elif algorithm in {Sym.Cipher.TripleDES, Sym.Cipher.CAST5, Sym.Cipher.Blowfish, Sym.Cipher.IDEA}:
        return 8
    elif algorithm == Sym.Cipher.ARC4:
        return 0  # ARC4 does not use an IV or nonce
    raise ValueError("Unsupported Algorithm for size")


def _create_mode_instance(mode, cipher, forced_iv_or_nonce=None, extra_tag=None):
    match mode:
        case modes.CTR:
            nonce = forced_iv_or_nonce or os.urandom(_get_iv_nonce_size(cipher))
            mode_instance = mode(nonce)
            return mode_instance, ('nonce', nonce)
        case modes.ECB:
            mode_instance = mode()
            return mode_instance, (None, None)
        case _:
            iv = forced_iv_or_nonce or os.urandom(_get_iv_nonce_size(cipher))
            if extra_tag is None:
                mode_instance = mode(iv)
            else:
                mode_instance = mode(iv, extra_tag)
            return mode_instance, ('iv', iv)


def encrypt_sym(plain_bytes: bytes, cipher_key, padding=None, mode_id=None):
    parts = {}

    if cipher_key.cipher in (Sym.Cipher.ChaCha20, Sym.Cipher.ARC4):
        mode = identification = None
        iv_or_nonce = os.urandom(16)  # nonce for ChaCha20
    else:
        mode = _SYM_OPERATION_CONVERSION[mode_id]
        mode_instance, (identification, iv_or_nonce) = _create_mode_instance(mode, cipher_key.cipher)

    if identification:
        parts[identification] = iv_or_nonce
    elif cipher_key.cipher == Sym.Cipher.ChaCha20:
        parts['nonce'] = iv_or_nonce

    algorithm_class = _SYM_ALGORITHM_CONVERSION[cipher_key.cipher]

    if algorithm_class == algorithms.ChaCha20:
        cipher = Cipher(algorithm_class(cipher_key.get_key(), nonce=iv_or_nonce), mode=None)
    elif algorithm_class == algorithms.ARC4:
        cipher = Cipher(algorithm_class(cipher_key.get_key()), mode=None)
    else:
        cipher = Cipher(algorithm_class(cipher_key.get_key()), mode_instance)

    if mode in (modes.CBC, modes.ECB):
        padder = _SYM_PADDING_CONVERSION[padding](algorithm_class.block_size).padder()
        padded_data = padder.update(plain_bytes) + padder.finalize()
    else:
        padded_data = plain_bytes

    try:
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    except UnsupportedAlgorithm:
        raise NotSupportedError("Algorithm is not supported")

    if mode == modes.GCM:
        parts['tag'] = encryptor.tag
    parts['ciphertext'] = ciphertext

    return parts


def decrypt_sym(ciphertext: Union[bytes, dict[str, bytes]], cipher_key, padding=None, mode_id=None) -> bytes:
    mode = _SYM_OPERATION_CONVERSION[mode_id] if (
            cipher_key.cipher not in (Sym.Cipher.ChaCha20, Sym.Cipher.ARC4)) \
        else None

    if isinstance(ciphertext, dict):
        ciphertext = ciphertext['ciphertext']
        iv_or_nonce = ciphertext.get('iv') or ciphertext.get('nonce')
    else:
        iv_nonce_size = _get_iv_nonce_size(cipher_key.cipher) if mode != modes.ECB else 0
        iv_or_nonce, ciphertext = ciphertext[:iv_nonce_size], ciphertext[iv_nonce_size:]

    if mode_id == Sym.Operation.GCM:
        tag, ciphertext = ciphertext[:16], ciphertext[16:]
        mode_instance, (_, __) = _create_mode_instance(mode, cipher_key.cipher, iv_or_nonce, tag)
    else:
        if cipher_key.cipher in (Sym.Cipher.ChaCha20, Sym.Cipher.ARC4):
            mode_instance = None
        else:
            mode_instance, (_, __) = _create_mode_instance(mode, cipher_key.cipher, iv_or_nonce)

    algorithm_class = _SYM_ALGORITHM_CONVERSION[cipher_key.cipher]

    if algorithm_class == algorithms.ChaCha20:
        cipher = Cipher(algorithm_class(cipher_key.get_key(), nonce=iv_or_nonce), mode=None)
    elif algorithm_class == algorithms.ARC4:
        cipher = Cipher(algorithm_class(cipher_key.get_key()), mode=None)
    else:
        cipher = Cipher(algorithm_class(cipher_key.get_key()), mode_instance)

    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()

    if mode in (modes.CBC, modes.ECB):
        unpadder = _SYM_PADDING_CONVERSION[padding](algorithm_class.block_size).unpadder()
        plain_bytes = unpadder.update(padded_data) + unpadder.finalize()
    else:
        plain_bytes = padded_data
    return plain_bytes


def encrypt_asym(plain_bytes: bytes, cipher_key, padding=None, strength=None):
    parts = {}

    if cipher_key.cipher == ASym.Cipher.RSA:
        warnings.warn("RSA is insecure and should be migrated away from.")
        hash_type = (hashes.SHA224, hashes.SHA256,
                     hashes.SHA384, hashes.SHA512)[strength.value]()

        if padding == ASym.Padding.OAEP:
            padding_obj = _ASYM_PADDING_CONVERSION[padding](
                mgf=asym_padding.MGF1(algorithm=hash_type), algorithm=hash_type, label=None)
        elif padding == ASym.Padding.PKCShash1v15:
            padding_obj = _ASYM_PADDING_CONVERSION[padding]()
        else:
            raise NotSupportedError("PSS is only supported for signing")

        try:
            parts['ciphertext'] = cipher_key.get_public_key().encrypt(plain_bytes, padding_obj)
        except ValueError as e:
            raise NotSupportedError(f"An error occurred, the data may be too big for the key [{e}]")
    else:
        raise UserWarning(f"Algorithm '{cipher_key.cipher}' does not support encryption")
    return parts


def decrypt_asym(ciphertext: Union[bytes, dict[str, bytes]], cipher_key, padding=None, strength=None):
    if cipher_key.cipher == ASym.Cipher.RSA:
        warnings.warn("RSA is insecure and should be migrated away from.")
        hash_type = (hashes.SHA224, hashes.SHA256,
                     hashes.SHA384, hashes.SHA512)[strength.value]()

        if padding == ASym.Padding.OAEP:
            padding_obj = _ASYM_PADDING_CONVERSION[padding](
                asym_padding.MGF1(algorithm=hash_type), algorithm=hash_type, label=None)
        elif padding == ASym.Padding.PKCShash1v15:
            padding_obj = _ASYM_PADDING_CONVERSION[padding]()
        else:
            raise NotSupportedError("PSS is only supported for signing")

        try:
            return cipher_key.get_private_key().decrypt(ciphertext, padding_obj)
        except ValueError as e:
            raise ValueError(f"An error occurred, the data may be corrupted or tampered with [{e}]")
    else:
        raise UserWarning(f"Algorithm '{cipher_key.cipher}' does not support encryption")


def key_derivation(password: bytes, length: int, salt: bytes = None, type_=None, strength=2):
    if salt is None:
        salt = os.urandom([16, 32, 64, 128][strength.value])

    hash_type = (hashes.SHA3_224, hashes.SHA3_256,
                 hashes.SHA3_384, hashes.SHA3_512)[strength.value]

    match type_:
        case KeyDerivationFunction.PBKDF2HMAC:
            iter_mult = [1, 4, 8, 12][strength.value]
            kdf = pbkdf2.PBKDF2HMAC(
                algorithm=hash_type(),
                length=length,
                salt=salt,
                iterations=100_000 * iter_mult,
                backend=default_backend()
            )
        case KeyDerivationFunction.Scrypt:
            n, r, p = (
                (2 ** 14, 8, 1),
                (2 ** 15, 8, 1),
                (2 ** 16, 8, 2),
                (2 ** 17, 8, 2)
            )[strength.value]
            kdf = scrypt.Scrypt(
                salt=salt,
                length=length,
                n=n,
                r=r,
                p=p,
                backend=default_backend()
            )
        case KeyDerivationFunction.HKDF:
            kdf = hkdf.HKDF(
                algorithm=hash_type(),
                length=length,
                salt=salt,
                info=b"",
                backend=default_backend()
            )
        case KeyDerivationFunction.X963:
            kdf = x963kdf.X963KDF(
                algorithm=hash_type(),
                length=length,
                sharedinfo=None,
                backend=default_backend()
            )
        case KeyDerivationFunction.ConcatKDF:
            kdf = concatkdf.ConcatKDFHash(
                algorithm=hash_type(),
                length=length,
                otherinfo=None,
                backend=default_backend()
            )
        case _:
            raise NotSupportedError(f"Unsupported Key Derivation Function (Index {type_})")
    return kdf.derive(password)


def generate_auth_code(auth_type, cipher_key, data, strength) -> bytes:
    if not isinstance(cipher_key, _BASIC_KEY) or cipher_key.cipher != Sym.Cipher.AES:
        raise ValueError("Invalid key type for generating authentication code")

    hash_type = (hashes.SHA3_224, hashes.SHA3_256,
                 hashes.SHA3_384, hashes.SHA3_512)[strength.value]
    if auth_type == MessageAuthenticationCode.HMAC:
        auth = hmac.HMAC(cipher_key.get_key(), hash_type(), backend=default_backend())
    elif auth_type == MessageAuthenticationCode.CMAC:
        auth = cmac.CMAC(algorithms.AES(cipher_key.get_key()), backend=default_backend())
    elif auth_type == MessageAuthenticationCode.Poly1305:
        auth = poly1305.Poly1305.generate_tag(cipher_key.get_key(), data)
        return auth
    else:
        raise NotSupportedError("Unsupported Authentication Code")
    auth.update(data)
    return auth.finalize()


def key_exchange(cipher_key, peer_public_key, algorithm: Literal["ECDH", "DH"]):
    """Diffie Hellman key exchange"""
    if not isinstance(cipher_key, _BASIC_KEYPAIR) or cipher_key.cipher_type != ASym:
        raise ValueError("Invalid key type for key exchange")
    if algorithm == "ECDH":
        return cipher_key.get_private_key().exchange(ec.ECDH(), peer_public_key)
    elif algorithm == "DH":
        return cipher_key.get_private_key().exchange(peer_public_key)
    else:
        raise NotSupportedError(f"Key exchange is not supported for the algorithm index '{algorithm}'")


def sign(data, cipher_key, padding, strength):
    if not isinstance(cipher_key, _BASIC_KEYPAIR) or cipher_key.cipher_type != ASym:
        raise ValueError("Invalid key type for signing")

    hash_type = (hashes.SHA3_224, hashes.SHA3_256,
                 hashes.SHA3_384, hashes.SHA3_512)[strength.value]

    if cipher_key.cipher == ASym.Cipher.RSA:
        warnings.warn("RSA is insecure and should be migrated away from.")
        if padding == ASym.Padding.PSS:
            padding_obj = asym_padding.PSS(
                mgf=asym_padding.MGF1(hash_type()),
                salt_length=asym_padding.PSS.MAX_LENGTH
            )
        elif padding == ASym.Padding.OAEP:
            raise NotSupportedError("OAEP is not supported for signing")
        elif padding == ASym.Padding.PKCShash1v15:
            padding_obj = asym_padding.PKCS1v15()
        else:
            raise NotSupportedError("Unsupported padding for RSA")
        try:
            return cipher_key.get_private_key().sign(
                data,
                padding_obj,
                hash_type()
            )
        except ValueError:
            raise NotSupportedError("ValueError occurred, maybe the RSA key is too small for the data/salt")
    elif cipher_key.cipher == ASym.Cipher.ECC:
        return cipher_key.get_private_key().sign(data, ec.ECDSA(hash_type()))
    elif cipher_key.cipher == ASym.Cipher.DSA:
        return cipher_key.get_private_key().sign(data, hash_type())
    else:
        raise NotSupportedError("Unsupported signing algorithm")


def sign_verify(data, signature, cipher_key, padding, strength):
    if not isinstance(cipher_key, _BASIC_KEYPAIR) or cipher_key.cipher_type != ASym:
        raise ValueError("Invalid key type for signature verification")

    hash_type = (hashes.SHA3_224, hashes.SHA3_256,
                 hashes.SHA3_384, hashes.SHA3_512)[strength.value]

    try:
        if cipher_key.cipher == ASym.Cipher.RSA:
            warnings.warn("RSA is insecure and should be migrated away from.")
            if padding == ASym.Padding.PSS:
                padding_obj = asym_padding.PSS(
                    mgf=asym_padding.MGF1(hash_type()),
                    salt_length=asym_padding.PSS.MAX_LENGTH
                )
            elif padding == ASym.Padding.OAEP:
                raise ValueError("OAEP is not supported for signing")
            elif padding == ASym.Padding.PKCShash1v15:
                padding_obj = asym_padding.PKCS1v15()
            else:
                raise NotSupportedError("Unsupported padding for RSA")
            cipher_key.get_public_key().verify(
                signature,
                data,
                padding_obj,
                hash_type()
            )
        elif cipher_key.cipher == ASym.Cipher.ECC:
            cipher_key.get_public_key().verify(signature, data, ec.ECDSA(hash_type()))
        elif cipher_key.cipher == ASym.Cipher.DSA:
            cipher_key.get_public_key().verify(signature, data, hash_type())
        else:
            raise NotSupportedError("Unsupported signing verification algorithm")
        return True
    except InvalidSignature:
        return False
