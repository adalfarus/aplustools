from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding, ec, dsa, ed25519, ed448, x25519, x448
from cryptography.hazmat.primitives import serialization, hashes, padding as sym_padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.kdf.concatkdf import ConcatKDFHash
from cryptography.hazmat.primitives.kdf.x963kdf import X963KDF
from cryptography.hazmat.primitives import hmac, cmac
from typing import Literal, Tuple, Optional, IO, Union, Any, NewType
from pathlib import Path
import warnings
import secrets
import bcrypt
import os

from aplustools.security.passwords import SpecificPasswordGenerator, PasswordFilter
from aplustools.io.environment import safe_remove, strict
from aplustools.data import enum_auto
from aplustools.security import Security
from tempfile import mkdtemp

from traits.trait_types import self

try:
    from quantcrypt.kem import Kyber
    from quantcrypt.cipher import KryptonKEM
    from quantcrypt.kdf import Argon2
except ImportError:
    Kyber = KryptonKEM = Argon2 = None


class _BASIC_KEY:
    cipher_type = "SymCipher"
    cipher = "Unknown"

    def __init__(self, key: bytes, original_key):
        self._key = key
        self._original_key = original_key

    def get_key(self) -> bytes:
        """Get the key"""
        return self._key

    def get_original_key(self) -> str:
        """Get the original key used to generate the key"""
        return self._original_key

    def __bytes__(self):
        return self._key

    def __str__(self):
        return self._key.hex()

    def __repr__(self):
        return str(self)


class _BASIC_KEYPAIR:
    cipher_type = "ASymCipher"
    cipher = "Unknown"

    def __init__(self, private_key, public_key):
        self._private_key = private_key
        self._public_key = public_key

    @staticmethod
    def _load_pem_private_key(key_to_load: bytes | str):
        if isinstance(key_to_load, (bytes, str)):
            if isinstance(key_to_load, str):
                key_to_load = bytes(key_to_load, "utf-8")
            key_to_load = serialization.load_pem_private_key(key_to_load, None, default_backend())
        return key_to_load

    def get_private_key(self):
        """Returns the private key"""
        return self._private_key

    def get_public_key(self):
        """Returns the public key"""
        return self._public_key

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

    def __bytes__(self):
        return self.get_public_bytes()

    def __str__(self):
        return bytes(self).decode()

    def __repr__(self):
        return str(self)


# Bunch of enums to make it easier for the user
class _SHA2:
    """SHA2"""
    SHA224 = enum_auto()
    SHA256 = enum_auto()
    SHA384 = enum_auto()
    SHA512 = enum_auto()
    SHA512_244 = enum_auto()
    SHA512_256 = enum_auto()


class _SHA3:
    """SHA3"""
    SHA224 = enum_auto()
    SHA256 = enum_auto()
    SHA384 = enum_auto()
    SHA512 = enum_auto()
    SHAKE128 = enum_auto()
    SHAKE256 = enum_auto()


class _BLAKE2:
    """BLAKE2"""
    BLAKE2b = enum_auto()
    BLAKE2s = enum_auto()


class HashAlgorithm:
    """Provides an easy way for the user to specify a hash algorithm."""
    SHA1 = enum_auto()
    SHA2 = _SHA2
    SHA3 = _SHA3
    BLAKE2 = _BLAKE2
    MD5 = enum_auto()
    SM3 = enum_auto()
    BCRYPT = enum_auto()
    ARGON2 = enum_auto()


class _AES_KEY(_BASIC_KEY):
    cipher = "AES"

    def __init__(self, key_size: Literal[128, 192, 256], key: Optional[bytes | str]):
        _original_key = key if key is not None else secrets.token_hex(key_size // 8)
        if isinstance(_original_key, bytes):
            if len(_original_key) * 8 != float(key_size):
                raise ValueError(f"Key size of given key ({len(_original_key) * 8}) "
                                 f"doesn't match the specified key size ({key_size})")
            _key = _original_key
        else:
            _key = PBKDF2HMAC(algorithm=hashes.SHA3_512(), length=32, salt=os.urandom(64), iterations=800_000,
                              backend=default_backend()).derive(_original_key.encode())
        super().__init__(_key, _original_key)

    def get_key(self) -> bytes:
        """Get the AES key"""
        return self._key

    def get_original_key(self) -> str:
        """Get the original key used to generate the AES key"""
        return self._original_key

    def __bytes__(self):
        return self._key

    def __str__(self):
        return self._key.hex()

    def __repr__(self):
        return str(self)


class _AES:  # Advanced Encryption Standard
    @staticmethod
    def key(key_size: Literal[128, 192, 256], key: Optional[bytes | str] = None) -> _AES_KEY:
        return _AES_KEY(key_size, key)

    AES128 = AES192 = AES256 = None


def _create_aes_subclass(key_size: Literal[128, 192, 256]):
    """Helper method to create a subclass with a specific key size."""
    subclass_name = f"AES{key_size}"

    class SubClass(_AES):
        @classmethod
        def key(cls, key: Optional[bytes | str] = None) -> _AES_KEY:
            return _AES.key(key_size, key)

    SubClass.__name__ = subclass_name
    return SubClass


_AES.AES128 = _create_aes_subclass(128)
_AES.AES192 = _create_aes_subclass(192)
_AES.AES256 = _create_aes_subclass(256)


class SymCipher:
    """Symmetric Encryption"""
    AES = _AES
    ChaCha20 = enum_auto()
    TripleDES = enum_auto()
    Blowfish = enum_auto()
    CASTS = enum_auto()


class SymOperation:
    """Different modes of operation"""
    ECB = modes.ECB  # Electronic Codebook
    CBC = modes.CBC  # Cipher Block Chaining
    CFB = modes.CFB  # Cipher Feedback
    OFB = modes.OFB  # Output Feedback
    CTR = modes.CTR  # Counter
    GCM = modes.GCM  # Galois/Counter Mode
#    OCB = modes.OCB  # Offset Codebook Mode


class SymPadding:
    """Padding Schemes"""
    PKCS7 = sym_padding.PKCS7
    ANSIX923 = sym_padding.ANSIX923
#    ISO7816 = sym_padding.ISO7816


class _RSA_KEYPAIR(_BASIC_KEYPAIR):
    """You need to give a pem private key if it's in bytes"""
    public_exponent = 65537
    cipher = "RSA"

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


class _RSA:  # Rivest-Shamir-Adleman
    @staticmethod
    def key(key_size: Literal[512, 768, 1024, 2048, 3072, 4096, 8192, 15360],
            private_key: Optional[bytes | str | rsa.RSAPrivateKey] = None) -> _RSA_KEYPAIR:
        return _RSA_KEYPAIR(key_size, private_key)

    RSA512 = RSA768 = RSA1024 = RSA2048 = RSA3072 = RSA4096 = RSA8192 = RSA15360 = None


def _create_rsa_subclass(key_size: Literal[512, 768, 1024, 2048, 3072, 4096, 8192, 15360]):
    """Helper method to create a subclass with a specific key size."""
    subclass_name = f"RSA{key_size}"

    class SubClass(_RSA):
        @classmethod
        def key(cls, private_key: Optional[bytes | str | rsa.RSAPrivateKey] = None) -> _RSA_KEYPAIR:
            return _RSA.key(key_size, private_key)

    SubClass.__name__ = subclass_name
    return SubClass


_RSA.RSA512 = _create_rsa_subclass(512)
_RSA.RSA768 = _create_rsa_subclass(768)
_RSA.RSA1024 = _create_rsa_subclass(1024)
_RSA.RSA2048 = _create_rsa_subclass(2048)
_RSA.RSA3072 = _create_rsa_subclass(3072)
_RSA.RSA4096 = _create_rsa_subclass(4096)
_RSA.RSA8192 = _create_rsa_subclass(8192)
_RSA.RSA15360 = _create_rsa_subclass(15360)


class _DSA_KEYPAIR(_BASIC_KEYPAIR):
    cipher = "DSA"

    def __init__(self, key_size: Literal[1024, 2048, 3072],
                 private_key: Optional[bytes | str | dsa.DSAPrivateKey] = None):
        _private_key = self._load_pem_private_key(private_key) \
            if private_key is not None else dsa.generate_private_key(key_size=key_size)

        if _private_key.key_size != key_size:
            raise ValueError(f"Key size of given private key ({_private_key.key_size}) "
                             f"doesn't match the specified key size ({key_size})")
        _public_key = _private_key.public_key()
        super().__init__(_private_key, _public_key)


class _DSA:
    @staticmethod
    def key(key_size: Literal[1024, 2048, 3072], private_key: Optional[bytes | str | dsa.DSAPrivateKey] = None
            ) -> _DSA_KEYPAIR:
        return _DSA_KEYPAIR(key_size, private_key)

    DSA1024 = DSA2048 = DSA3072 = None


def _create_dsa_subclass(key_size: Literal[1024, 2048, 3072]):
    """Helper method to create a subclass with a specific key size."""
    subclass_name = f"DSA{key_size}"

    class SubClass(_DSA):
        @classmethod
        def key(cls, private_key: Optional[bytes | str | dsa.DSAPrivateKey] = None) -> _DSA_KEYPAIR:
            return _DSA.key(key_size, private_key)

    SubClass.__name__ = subclass_name
    return SubClass


_DSA.DSA1024 = _create_dsa_subclass(1024)
_DSA.DSA2048 = _create_dsa_subclass(2048)
_DSA.DSA3072 = _create_dsa_subclass(3072)


class ECC_CURVE:
    """Elliptic key functions"""
    SECP192R1 = ec.SECP192R1
    SECP224R1 = ec.SECP224R1
    SECP256K1 = ec.SECP256K1
    SECP256R1 = ec.SECP256R1  # Default
    SECP384R1 = ec.SECP384R1
    SECP521R1 = ec.SECP521R1
    SECT163K1 = ec.SECT163K1
    SECT163R2 = ec.SECT163R2
    SECT233K1 = ec.SECT233K1
    SECT233R1 = ec.SECT233R1
    SECT283K1 = ec.SECT283K1
    SECT283R1 = ec.SECT283R1
    SECT409K1 = ec.SECT409K1
    SECT409R1 = ec.SECT409R1
    SECT571K1 = ec.SECT571K1
    SECT571R1 = ec.SECT571R1


class ECC_TYPE:
    """How the signing is done, heavily affects the performance, key generation and what you can do with it"""
    ECDSA = enum_auto()  # Elliptic Curve Digital Signature Algorithm
    Ed25519 = ed25519.Ed25519PrivateKey
    Ed448 = ed448.Ed448PrivateKey
    X25519 = x25519.X25519PrivateKey
    X448 = x448.X448PrivateKey


class _ECC_KEYPAIR(_BASIC_KEYPAIR):
    cipher = "ECC"

    def __init__(self, ecc_type: Union[ECC_TYPE.ECDSA, ECC_TYPE.Ed25519] | ECC_TYPE.Ed448 | ECC_TYPE.X25519 | ECC_TYPE.X448 = ECC_TYPE.ECDSA,
                 ecc_curve: Optional[ec.SECP192R1 | ec.SECP224R1 | ec.SECP256K1 | ec.SECP256R1 |
                                     ec.SECP384R1 | ec.SECP521R1 | ec.SECT163K1 | ec.SECT163R2 |
                                     ec.SECT233K1 | ec.SECT233R1 | ec.SECT283K1 | ec.SECT283R1 |
                                     ec.SECT409K1 | ec.SECT409R1 | ec.SECT571K1 | ec.SECT571R1] = ECC_CURVE.SECP256R1,
                 private_key: Optional[bytes | str] = None):
        if private_key is None:
            if ecc_type == ECC_TYPE.ECDSA:
                _private_key = ec.generate_private_key(ecc_curve())
            else:
                if ecc_curve is not None:
                    raise ValueError("You can't use an ECC curve when you aren't using the ECC Type ECDSA. "
                                     "Please set it to None instead.")
                _private_key = ecc_type.generate()
        else:
            _private_key = self._load_pem_private_key(private_key)

        _public_key = _private_key.public_key()
        super().__init__(_private_key, _public_key)


class _ECC:
    """Elliptic Curve Cryptography"""
    @staticmethod
    def key(ecc_type: Union[ECC_TYPE.ECDSA, ECC_TYPE.Ed25519] | ECC_TYPE.Ed448 | ECC_TYPE.X25519 | ECC_TYPE.X448 = ECC_TYPE.ECDSA,
            ecc_curve: Optional[ec.SECP192R1 | ec.SECP224R1 | ec.SECP256K1 | ec.SECP256R1 |
                                ec.SECP384R1 | ec.SECP521R1 | ec.SECT163K1 | ec.SECT163R2 |
                                ec.SECT233K1 | ec.SECT233R1 | ec.SECT283K1 | ec.SECT283R1 |
                                ec.SECT409K1 | ec.SECT409R1 | ec.SECT571K1 | ec.SECT571R1] = ECC_CURVE.SECP256R1,
            private_key: Optional[bytes | str] = None):
        return _ECC_KEYPAIR(ecc_type, ecc_curve, private_key)


class _KYBER_KEYPAIR(_BASIC_KEYPAIR):
    cipher = "KYBER"

    def __init__(self):
        if Kyber is None:
            raise EnvironmentError("Module QuantCrypt is not installed.")
        _public_key, _private_key = Kyber().keygen()
        super().__init__(_private_key, _public_key)

    def get_private_bytes(self) -> bytes:
        """Returns the private key in a byte format"""
        return self._private_key

    def get_public_bytes(self) -> bytes:
        """Returns the public key in a byte format"""
        return self._public_key

    def encrypt(self, plaintext_path_or_file: Union[bytes, IO, Path],
                      get: Literal["content", "path", "file"] = "content") -> Union[bytes, Path, IO]:
        """
        Encrypts a file using the Kyber public key.
        """
        if Kyber is None:
            raise EnvironmentError("Module QuantCrypt is not installed.")
        krypton = KryptonKEM(Kyber)
        temp_dir = mkdtemp()
        if isinstance(plaintext_path_or_file, (bytes, IO)):
            plaintext_file = Path(os.path.join(temp_dir, "kyper_inp"))

            if isinstance(plaintext_path_or_file, IO):
                with plaintext_path_or_file as f:
                    plaintext_path_or_file = f.read()

            with open(plaintext_file, "wb") as f:
                f.write(plaintext_path_or_file)
        elif isinstance(plaintext_path_or_file, Path):
            plaintext_file = plaintext_path_or_file
        else:
            raise ValueError("Please only input accepted types as plaintext.")
        ciphertext_file = Path(os.path.join(temp_dir, "kyper_out"))
        krypton.encrypt(self._public_key, plaintext_file, ciphertext_file)

        if not isinstance(plaintext_path_or_file, Path):
            safe_remove(plaintext_file)
        if get == "path":
            return ciphertext_file
        elif get == "file":
            return open(ciphertext_file, "rb")
        with open(ciphertext_file, "rb") as f:
            content = f.read()
        safe_remove(temp_dir)
        return content

    def decrypt(self, ciphertext_path_or_file: Union[bytes, IO, Path],
                      get: Literal["content", "path", "file"] = "content") -> Union[bytes, Path, IO]:
        """
        Decrypts a file to memory using the Kyber secret key.
        """
        if Kyber is None:
            raise EnvironmentError("Module QuantCrypt is not installed.")
        krypton = KryptonKEM(Kyber)
        temp_dir = mkdtemp()
        if isinstance(ciphertext_path_or_file, (bytes, IO)):
            ciphertext_file = Path(os.path.join(temp_dir, "kyper_inp"))

            if isinstance(ciphertext_path_or_file, IO):
                with ciphertext_path_or_file as f:
                    ciphertext_path_or_file = f.read()

            with open(ciphertext_file, "wb") as f:
                f.write(ciphertext_path_or_file)
        elif isinstance(ciphertext_path_or_file, Path):
            ciphertext_file = ciphertext_path_or_file
        else:
            raise ValueError("Please only input accepted types as ciphertext.")
        plaintext_file = Path(os.path.join(temp_dir, "kyper_out"))
        krypton.decrypt_to_file(self._secret_key, ciphertext_file, plaintext_file)

        if not isinstance(ciphertext_path_or_file, Path):
            safe_remove(ciphertext_file)
        if get == "path":
            return plaintext_file
        elif get == "file":
            return open(plaintext_file, "rb")
        with open(plaintext_file, "rb") as f:
            content = f.read()
        safe_remove(temp_dir)
        return content

    def __str__(self):
        return self.get_public_bytes().hex()


class _KYBER:
    @staticmethod
    def key():
        return _KYBER_KEYPAIR()


class ASymCipher:
    """Asymmetric Encryption"""
    RSA = _RSA
    DSA = _DSA  # Digital Signature Algorithm
    ECC = _ECC
    KYBER = _KYBER


class ASymPadding:
    """Asymmetric Encryption Padding Schemes"""
    PKCShash1v15 = asym_padding.PKCS1v15  # Older padding scheme for RSA
    OAEP = asym_padding.OAEP  # Optimal Asymmetric Encryption Padding
    PSS = asym_padding.PSS  # Probabilistic Signature Scheme


class KeyDerivation:
    """Key Derivation Functions (KDFs)"""
    PBKDF2HMAC = enum_auto()  # Password-Based Key Derivation Function 2
    Scrypt = enum_auto()
    HKDF = enum_auto()  # HMAC-based Extract-and-Expand Key Derivation Function
    X963 = enum_auto()
    ConcatKDF = enum_auto()


class AuthCodes:
    """Authentication Codes"""
    HMAC = 0  # Hash-based Message Authentication Code
    CMAC = 1  # Cipher-based Message Authentication Cod


class DiffieHellmanAlgorithm:
    ECDH = enum_auto()  # Elliptic Curve Diffie-Hellman
    DH = enum_auto()


_BASIC_KEY_TYPE = NewType("_BASIC_KEY_TYPE", _BASIC_KEY)
_BASIC_KEYPAIR_TYPE = NewType("_BASIC_KEYPAIR_TYPE", _BASIC_KEYPAIR)


class AdvancedCryptography:
    """Makes security easy.
    Remember that easy_hash appends one byte to the start of the hash for identification,
    except for argon2, which already has an identifier."""
    _hash_algorithm_map = {
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

    def __init__(self, auto_pack: bool = True, easy_hash: bool = True, backend: Literal["OpenSSL"] = "OpenSSL"):
        self._auto_pack = auto_pack
        self._easy_hash = easy_hash

        if backend != "OpenSSL":
            raise ValueError("Cryptography only supports the OpenSSL backend")

    # Function to create a hash object with special handling for SHAKE algorithms
    def _create_digest(self, algo, digest_size=None):
        if algo in (HashAlgorithm.SHA3.SHAKE128, HashAlgorithm.SHA3.SHAKE256):
            if digest_size is None:
                digest_size = 32  # default size in bytes (256 bits)
            digest = hashes.Hash(self._hash_algorithm_map[algo](digest_size))
        else:
            digest = hashes.Hash(self._hash_algorithm_map[algo]())
        return digest

    def hash(self, to_hash: bytes, algo: int) -> str | bytes:
        match algo:
            case HashAlgorithm.BCRYPT:
                result = bcrypt.hashpw(to_hash, bcrypt.gensalt())
                return algo.to_bytes(1, "big") + result if self._easy_hash else result
            case HashAlgorithm.ARGON2:
                warnings.warn("Argon2 is still not perfectly supported, expect bugs or other mishaps.",
                              category=UserWarning, stacklevel=2)
                if Kyber is None:
                    raise EnvironmentError("Module QuantCrypt is not installed.")
                return Argon2.Hash(to_hash).public_hash
            case _:
                digest = self._create_digest(algo, 64)

        digest.update(to_hash)
        result = digest.finalize()
        return algo.to_bytes(1, "big") + result if self._easy_hash else result

    def hash_verify(self, to_verify: bytes, original_hash: bytes | str, algo: Optional[int] = None):
        """Maybe add an ID to each hash so the HashAlgorithm doesn't have to be passed twice."""
        if self._easy_hash:
            if isinstance(original_hash, bytes) or not original_hash.startswith("$argon2"):
                algo = original_hash[0]
                original_hash = original_hash[1:]
            else:
                algo = HashAlgorithm.ARGON2
        match algo:
            case HashAlgorithm.BCRYPT:
                return bcrypt.checkpw(to_verify, original_hash)
            case HashAlgorithm.ARGON2:
                warnings.warn("Argon2 is still not perfectly supported, expect bugs or other mishaps.",
                              category=UserWarning, stacklevel=2)
                if Kyber is None:
                    raise EnvironmentError("Module QuantCrypt is not installed.")
                try:
                    Argon2.Hash(to_verify, original_hash)
                    return True
                except Exception as e:
                    print(f"Exception occurred: {e}")
                    return False
            case _:
                hash_algorithm_map = {
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
                digest = hashes.Hash(hash_algorithm_map[algo]())

        digest.update(to_verify)
        return digest.finalize() == original_hash

    def encrypt(self, plain_bytes: bytes, cipher_key: _BASIC_KEY_TYPE | _BASIC_KEYPAIR,
                padding: Optional[SymPadding | ASymPadding] = None, mode_or_strength: Optional[SymOperation] | Literal["weak", "average", "strong"] = None) -> bytes | tuple[Any]:
        parts = {}

        if cipher_key.cipher_type == "SymCipher":
            if mode_or_strength == modes.CBC:
                iv = os.urandom(16)
                mode_instance = mode_or_strength(iv)
                parts['iv'] = iv
            elif mode_or_strength == modes.GCM:
                nonce = os.urandom(12)
                mode_instance = mode_or_strength(nonce)
                parts['nonce'] = nonce
            elif mode_or_strength == modes.CTR:
                nonce = os.urandom(16)
                mode_instance = mode_or_strength(nonce)
                parts['nonce'] = nonce
            else:
                mode_instance = mode_or_strength()

            match cipher_key.cipher:
                case "AES":
                    cipher = Cipher(algorithms.AES(cipher_key.get_key()), mode_instance)
                    algorithm = algorithms.AES
                case "ChaCha20":
                    pass
                case "TripleDES":
                    pass
                case "Blowfish":
                    pass
                case "CASTS":
                    pass

            if mode_or_strength in (modes.CBC, modes.ECB):
                padder = padding(algorithm.block_size).padder()
                padded_data = padder.update(plain_bytes) + padder.finalize()
            else:
                padded_data = plain_bytes

            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(padded_data) + encryptor.finalize()
            parts['ciphertext'] = ciphertext
        elif cipher_key.cipher_type == "ASymCipher":
            if cipher_key.cipher == "RSA":
                hash_type = {"weak": hashes.SHA256, "average": hashes.SHA384,  # Shared across too many
                                         "strong": hashes.SHA512}[mode_or_strength]

                if padding == asym_padding.OAEP:
                    padding_obj = padding(
                            asym_padding.MGF1(algorithm=hash_type()),
                            algorithm=hash_type(),
                            label = None
                        )
                elif padding == asym_padding.PKCS1v15:
                    padding_obj = padding()
                elif padding == asym_padding.PSS:
                    raise ValueError("PSS is only supported for signing")

                try:
                    ciphertext = cipher_key.get_public_key().encrypt(
                        plain_bytes,
                        padding_obj
                    )
                except ValueError as e:
                    raise ValueError(f"An error occurred, the data may be too big for the key [{e}]")
                parts['ciphertext'] = ciphertext
            elif cipher_key.cipher == "KYBER":
                warnings.warn("Kyber is still not perfectly supported, expect bugs or other mishaps.",
                              category=UserWarning, stacklevel=2)
                if Kyber is None:
                    raise EnvironmentError("Module QuantCrypt is not installed.")
                parts["ciphertext"] = cipher_key.encrypt(plain_bytes)
            else:
                raise ValueError("DSA and ECC cannot be used for encryption")

        if self._auto_pack:
            outputs = b''.join(v for k, v in parts.items())
        else:
            outputs = parts

        return outputs

    def decrypt(self, cipher_bytes: bytes | tuple[Any], cipher: SymCipher | ASymCipher,
                cipher_key: type[_BASIC_KEY | _BASIC_KEYPAIR], mode: Optional[SymOperation],
                padding: SymPadding | ASymPadding):
        pass

    def KDF(self, password: bytes, length: int, salt: bytes = None,
            key_dev_type: KeyDerivation = KeyDerivation.PBKDF2HMAC,
            strength: Literal["weak", "average", "strong"] = "strong"):
        """

        :param password:
        :param length:
        :param salt:
        :param key_dev_type:
        :param strength:
        """
        if salt is None:
            salt = os.urandom({"weak": 16, "average": 32, "strong": 64}[strength])

        hash_type = hash_type = {"weak": hashes.SHA3_256, "average": hashes.SHA3_384,  # Shared across too many
                                 "strong": hashes.SHA3_512}[strength]  # algorithms, so I made it select at the start.
        match key_dev_type:
            case KeyDerivation.PBKDF2HMAC:
                iter_mult = {"weak": 1, "average": 4, "strong": 8}[strength]
                kdf = PBKDF2HMAC(
                    algorithm=hash_type(),
                    length=length,
                    salt=salt,
                    iterations=100_000 * iter_mult,
                    backend=default_backend()
                )
            case KeyDerivation.Scrypt:
                n, r, p = {
                    "weak": (2 ** 14, 8, 1),
                    "average": (2 ** 16, 8, 2),
                    "strong": (2 ** 18, 8, 4)
                }[strength]
                kdf = Scrypt(
                    salt=salt,
                    length=length,
                    n=n,
                    r=r,
                    p=p,
                    backend=default_backend()
                )
            case KeyDerivation.HKDF:
                kdf = HKDF(
                    algorithm=hash_type(),
                    length=length,
                    salt=salt,
                    info=b"",
                    backend=default_backend()
                )
            case KeyDerivation.X963:
                kdf = X963KDF(
                    algorithm=hash_type(),
                    length=length,
                    sharedinfo=None,
                    backend=default_backend()
                )
            case KeyDerivation.ConcatKDF:
                kdf = ConcatKDFHash(
                    algorithm=hash_type(),
                    length=length,
                    otherinfo=None,
                    backend=default_backend()
                )
            case _:
                raise ValueError(f"Unsupported Key Derivation Function (Index {key_dev_type})")

        return kdf.derive(password)

    @staticmethod
    def generate_auth_code(auth_type: AuthCodes, key: bytes, data: bytes,
                           strength: Literal["weak", "average", "strong"] = "strong") -> bytes:
        hash_type = {"weak": hashes.SHA3_256, "average": hashes.SHA3_384,  # Shared across too many
                     "strong": hashes.SHA3_512}[strength]
        if auth_type == AuthCodes.HMAC:
            h = hmac.HMAC(key, hash_type(), backend=default_backend())
            h.update(data)
            return h.finalize()
        elif auth_type == AuthCodes.CMAC:
            c = cmac.CMAC(algorithms.AES(key), backend=default_backend())
            c.update(data)
            return c.finalize()
        else:
            raise ValueError("Unsupported Authentication Code")

    @staticmethod
    def key_exchange(private_key, peer_public_key, algorithm: DiffieHellmanAlgorithm):
        if algorithm == DiffieHellmanAlgorithm.ECDH:
            return private_key.exchange(ec.ECDH(), peer_public_key)
        elif algorithm == DiffieHellmanAlgorithm.DH:
            return private_key.exchange(peer_public_key)
        else:
            raise ValueError(f"Key exchange is not supported for the algorithm index '{algorithm}'")

    @staticmethod
    def sign():
        pass

    @staticmethod
    def sign_verify():
        pass


# AC = AdvancedCryptography()
# HA = HashAlgorithm
# print(AC.hash("HelloWorld".encode(), HA.SHA3.SHAKE128))
# input(AC.hash_verify("HELL".encode(), AC.hash("HELL".encode(), HA.SHA3.SHA224)))
# print(AC.hash_verify("Hello World".encode(), AC.hash("Hello World".encode(), HA.SHA3.SHA224), HA.SHA3.SHA224))
# print(AC.hash_verify("Hello World".encode(), AC.hash("Hello World".encode(), HA.BCRYPT), HA.BCRYPT))
# print(AC.hash_verify("Zel".encode(), AC.hash("Zel".encode(), HA.ARGON2), HA.ARGON2))
key = SymCipher.AES.AES128.key()
ac = AdvancedCryptography()
cipher = ac.encrypt("Hello World".encode(),
                    key, SymPadding.PKCS7,
                    SymOperation.CBC)
print(cipher)

rsa_key = ASymCipher.KYBER.key()
cipher2 = ac.encrypt("HELL".encode(), rsa_key)
print(cipher2)
input()


class CryptUtils:
    @staticmethod
    def pbkdf2(password: str, salt: bytes, length: int, cycles: int) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA512(),
            length=length,
            salt=salt,
            iterations=cycles,
            backend=default_backend()
        )
        key = kdf.derive(password.encode())
        return key

    @staticmethod
    def generate_salt(length: int) -> bytes:
        # Generate a cryptographically secure salt
        return secrets.token_bytes(length)

    @staticmethod
    def generate_aes_key(bit_length: Literal[128, 192, 256]) -> bytes:
        return secrets.token_bytes(bit_length // 8)

    @staticmethod
    def pack_ae_data(iv: bytes, encrypted_data: bytes, tag: bytes) -> bytes:
        iv_len_encoded = len(iv).to_bytes(1, "big")  # Maximum length of 128
        tag_len_encoded = len(tag).to_bytes(1, "big")  # Maximum length of 128
        return iv_len_encoded + iv + tag_len_encoded + tag + encrypted_data

    @staticmethod
    def unpack_ae_data(data: bytes):
        iv_len = int.from_bytes(data[:1])

        iv_start = 1
        iv_end = iv_start + iv_len
        iv = data[iv_start:iv_end]

        tag_len = int.from_bytes(data[iv_end:iv_end + 1])
        tag_start = iv_end + 1
        tag_end = tag_start + tag_len
        tag = data[tag_start:tag_end]

        encrypted_data = data[tag_end:]
        return iv, encrypted_data, tag

    @staticmethod
    def aes_encrypt(data: bytes, key: bytes) -> Tuple[bytes, bytes, bytes]:
        iv = os.urandom(12)  # Generate IV securely
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        return iv, ciphertext, encryptor.tag

    @staticmethod
    def aes_decrypt(iv: bytes, encrypted_data: bytes, tag: bytes, key: bytes) -> Optional[bytes]:
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        try:
            return decryptor.update(encrypted_data) + decryptor.finalize()
        except ValueError:
            print("AES Decryption Error: MAC check failed")
            return None

    @staticmethod
    def generate_des_key(bit_length: Literal[64, 128, 192]) -> bytes:
        return secrets.token_bytes(bit_length // 8)

    @staticmethod
    def des_encrypt(data: bytes, key: bytes) -> tuple:
        iv = os.urandom(8)
        cipher = Cipher(algorithms.TripleDES(key), modes.CFB(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        return iv, ciphertext, b''  # DES doesn't use a tag in this mode

    @staticmethod
    def des_decrypt(iv: bytes, ciphertext: bytes, tag: bytes, key: bytes) -> bytes:
        cipher = Cipher(algorithms.TripleDES(key), modes.CFB(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()

    @staticmethod
    def generate_rsa_key_pair(bit_length: Literal[1024, 2048, 4096]) -> Tuple[bytes, bytes]:
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=bit_length,
            backend=default_backend()
        )
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption())
        return private_bytes, private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo)

    @staticmethod
    def load_private_key(private_bytes: bytes) -> rsa.RSAPrivateKey:
        return serialization.load_pem_private_key(
            private_bytes,
            password=None,
            backend=default_backend()
        )

    @staticmethod
    def load_public_key(public_bytes: bytes) -> rsa.RSAPublicKey:
        return serialization.load_pem_public_key(
            public_bytes,
            backend=default_backend()
        )

    @staticmethod
    def rsa_encrypt(data: bytes, public_key: rsa.RSAPublicKey) -> bytes:
        try:
            return public_key.encrypt(
                data,
                asym_padding.OAEP(
                    mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
        except ValueError:
            print("ValueError, remember that RSA can only encrypt something shorter than it's key. Otherwise you should"
                  "use hybrid encryption, so encrypt with e.g. AES and then encrypt the aes key with rsa.")

    @staticmethod
    def rsa_decrypt(encrypted_data: bytes, private_key: rsa.RSAPrivateKey) -> bytes:
        return private_key.decrypt(
            encrypted_data,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    @staticmethod
    def generate_hash(message: str, hash_type: Literal["weak", "okay", "strong"] = "strong") -> str:
        hash_algo = {"weak": hashes.SHA256, "okay": hashes.SHA384, "strong": hashes.SHA512}[hash_type]()
        digest = hashes.Hash(hash_algo, backend=default_backend())
        digest.update(message.encode())
        return digest.finalize().hex()


class ModernCryptUtils:  # QuantumCryptography
    def __init__(self):
        warnings.warn("This module is experimental as the exact specifications for Quantum Cryptography haven't been "
                      "decided on yet and will likely change in the future.", category=RuntimeWarning, stacklevel=2)

    @staticmethod
    def generate_kyber_keypair() -> Tuple[bytes, bytes]:
        """
        Generates a Kyber public and private key pair.
        """
        if Kyber is None:
            raise EnvironmentError("Module QuantCrypt is not installed.")
        return Kyber().keygen()



    @staticmethod
    def generate_secure_password(length: int = 24):
        return SpecificPasswordGenerator().generate_ratio_based_password_v3(length, filter_=PasswordFilter(
            exclude_similar=True))


# Example usage
if __name__ == "___main__":
    # Using ModernCryptUtils for Argon2
    password = ModernCryptUtils.generate_secure_password()
    argon2_hash = ModernCryptUtils.hash(password)
    argon2_hash2 = ModernCryptUtils.hash(password)
    print(f"Argon2 Hash: {argon2_hash == argon2_hash2}")
    assert ModernCryptUtils.hash_verify(password, argon2_hash)
    from pathlib import Path

    # Using ModernCryptUtils for Kyber
    public_key, secret_key = ModernCryptUtils.generate_kyber_keypair()

    # Encrypt the plaintext file
    encrypted = ModernCryptUtils.kyber_encrypt(public_key, "Hello World".encode())

    # Decrypt the ciphertext file to a new file
    decrypted = ModernCryptUtils.kyber_decrypt(secret_key, encrypted).decode()

    print(encrypted, decrypted)

    path = ModernCryptUtils.kyber_encrypt(public_key, "HELLO".encode(), get="path")
    decrypted = ModernCryptUtils.kyber_decrypt(secret_key, path, get="content")
    safe_remove(path)
    print(decrypted.decode())
