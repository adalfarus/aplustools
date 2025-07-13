"""TBA"""
import enum
import typing

from .exceptions import NotSupportedError as _NotSupportedError
# from .. import GenericLabeledEnum as _GenericLabeledEnum
# from . import Backend as _Backend
# TODO: Fix circular import
# from .algos._sym import (KeyEncoding as SymKeyEncoding, Padding as SymPadding,
#                          Operation as SymOperation, MessageAuthenticationCode)
# from .algos._asym import (KeyEncoding as ASymKeyEncoding, KeyFormat as ASymKeyFormat,
#                           Padding as ASymPadding)
# from .algos import _hash_algorithm

from abc import ABCMeta, abstractmethod

# Standard typing imports for aps
import typing_extensions as _te
import collections.abc as _a
import typing as _ty
if _ty.TYPE_CHECKING:
    import _typeshed as _tsh
import types as _ts

# TODO: Fix circular import
SymKeyEncoding = None
SymPadding = None
SymOperation = None
MessageAuthenticationCode = None
ASymKeyEncoding = None
ASymKeyFormat = None
ASymPadding = None


class Backend(enum.Enum):
    """One of the cryptography backends"""
    # cryptography = ("aplustools.security.crypto._crypto", "Cryptography backend")  # Unsupported
    # pycryptodomex = ("aplustools.security.crypto._pycrypto", "PyCryptodomeX backend")  # Unsupported
    cryptography_alpha = ("aplustools.security.crypto._crypto_alpha", "Cryptography backend alpha")
    pycryptodomex_alpha = ("aplustools.security.crypto._pycrypto_alpha", "PyCryptodomeX backend alpha")
    quantcrypt = ("aplustools.security.crypto._quantcrypt", "Post-quantum via QuantCrypt")
    argon2_cffi = ("aplustools.security.crypto._argon2_cffi", "Argon2 via argon2_cffi")
    bcrypt = ("aplustools.security.crypto._bcrypt", "Bcrypt backend")
    # pynacl = ("aplustools.security.crypto._pynacl", "NaCl/libsodium backend")  # Unsupported
    # tink = ("aplustools.security.crypto._tink", "Google Tink backend")  # Unsupported
    # rust_crypto = ("aplustools.security.crypto._rust", "Rust-backed cryptographic backend")  # Unsupported
    # openssl = ("aplustools.security.crypto._openssl", "OpenSSL backend")  # Unsupported
    std_lib = ("aplustools.security.crypto._std_lib", "Standard library fallbacks")


class Cipher(metaclass=ABCMeta):
    """Base class for symmetric and asymmetric ciphers."""
    # cipher: str
    # def decode_key(self, key: bytes, encoding: SymKeyEncoding | ASymKeyEncoding): ...
    # def __str__(self) -> str:
    #     return self.cipher
class SymCipher(Cipher, metaclass=ABCMeta):
    """Base class for symmetric ciphers."""
    key: _ty.Type["_BaseSymmetricKey"]
    def __str__(self) -> str:
        return self.key.cipher
    # @abstractmethod
    # def new_key(self, __item: _ty.Any) -> "_BaseSymmetricKey":
    #     """Generate or derive a new key from the given input."""
    # @classmethod
    # def decode_key(cls, key: bytes, encoding: SymKeyEncoding) -> "_BaseSymmetricKey":
    #     """Decode a symmetric key from its encoded representation."""
    #     if cls.key is None:
    #         raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")
    #     if not (isinstance(key, bytes) and isinstance(encoding, SymKeyEncoding)):
    #         raise ValueError("key needs to be of type bytes and encoding needs to be of type Sym.KeyEncoding")
    #     return cls.key.decode(key, encoding)
class AsymCipher(Cipher, metaclass=ABCMeta):
    """Base class for asymmetric ciphers."""
    keypair: _ty.Type["_BaseAsymmetricKeypair"]
    def __str__(self) -> str:
        return self.keypair.cipher
    # @abstractmethod
    # def new_key(self, __item: _ty.Any) -> "_BaseAsymmetricKeypair":
    #     """Generate or derive a new key from the given input."""
    # @classmethod
    # def decode_private_key(cls, key: bytes, format_: ASymKeyFormat, encoding: ASymKeyEncoding) -> "_BaseAsymmetricKeypair":
    #     """Decode an asymmetric key from its encoded representation."""
    #     if cls.keypair is None:
    #         raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")
    #     if not (isinstance(key, bytes) and isinstance(format_, ASymKeyFormat) and isinstance(encoding, ASymKeyEncoding)):
    #         raise ValueError("key needs to be of type bytes and encoding needs to be of type ASym.KeyEncoding")
    #     return cls.keypair.decode_private_key(key, format_, encoding)
    # @classmethod
    # def decode_public_key(cls, key: bytes, format_: ASymKeyFormat, encoding: ASymKeyEncoding) -> "_BaseAsymmetricKeypair":
    #     """Decode an asymmetric key from its encoded representation."""
    #     if cls.keypair is None:
    #         raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")
    #     if not (isinstance(key, bytes) and isinstance(format_, ASymKeyFormat) and isinstance(encoding, ASymKeyEncoding)):
    #         raise ValueError("key needs to be of type bytes and encoding needs to be of type ASym.KeyEncoding")
    #     return cls.keypair.decode_public_key(key, format_, encoding)


class _BaseKey(metaclass=ABCMeta):
    backend: Backend
    cipher: str
    __concrete__: bool = False  # Is flipped true if the set_backend function sets this key, otherwise false

    @abstractmethod
    def new(self, *args: _ty.Any, **kwargs: _ty.Any) -> _te.Self:
        """TBA"""
    @abstractmethod
    def __repr__(self) -> str: ...
class _BaseSymmetricKey(_BaseKey, metaclass=ABCMeta):
    """Abstract base class for basic key types used in symmetric encryption schemes."""
class _BaseAsymmetricKeypair(_BaseKey, metaclass=ABCMeta):
    """Abstract base class for asymmetric key pair operations."""

# Serialization
class SingleSerializable(metaclass=ABCMeta):
    """Interface for encoding and decoding single keys."""
    @classmethod
    @abstractmethod
    def decode(cls, *args: _ty.Any, **kwargs: _ty.Any) -> _te.Self:
        """TBA"""
    @abstractmethod
    def encode(self, *args: _ty.Any, **kwargs: _ty.Any) -> _ty.Any:
        """TBA"""
class SymKeySerializable(SingleSerializable, metaclass=ABCMeta):
    """Interface for encoding and decoding symmetric keys."""
    @classmethod
    @abstractmethod
    def decode(cls, key: bytes, encoding: SymKeyEncoding) -> _te.Self:
        """
        Deserialize a key from its encoded byte representation.
        :param key: The encoded key bytes.
        :param encoding: The encoding format used (e.g., RAW, BASE64).
        :return: An instance of the key class constructed from the input.
        """
    @abstractmethod
    def encode(self, encoding: SymKeyEncoding) -> bytes:
        """
        Serialize the key into a specific encoding format.
        :param encoding: The format to encode the key into.
        :return: The encoded key.
        """
class DoubleSerializable(metaclass=ABCMeta):
    """Interface for encoding and decoding double keys."""
    @classmethod
    @abstractmethod
    def decode_private_key(cls, *args: _ty.Any, **kwargs: _ty.Any) -> _te.Self:
        """
        Deserialize a private key from the given encoded data.
        :param data:: Encoded private key data.
        :param format_: The key format (e.g., PKCS8).
        :param encoding: The key encoding (e.g., PEM, DER).
        :param password: Password used to decrypt the private key if encrypted.
        :return: A new instance of the key pair object containing the private key.
        """
    @classmethod
    @abstractmethod
    def decode_public_key(cls, *args: _ty.Any, **kwargs: _ty.Any) -> _te.Self:
        """
        Deserialize a public key from the given encoded data.
        :param data: Encoded public key data.
        :param format_: The key format (e.g., SubjectPublicKeyInfo).
        :param encoding: The key encoding (e.g., PEM, DER).
        :return: An instance containing only the public key.
        """
    @abstractmethod
    def encode_private_key(self, *args: _ty.Any, **kwargs: _ty.Any) -> _ty.Any:
        """
        Serialize the private key to the given format and encoding.
        :param format_: Format to use for the private key.
        :param encoding: Encoding (PEM, DER, etc.).
        :param password: If provided, encrypts the private key with this password.
        :return: The encoded private key.
        """
    @abstractmethod
    def encode_public_key(self, *args: _ty.Any, **kwargs: _ty.Any) -> _ty.Any:
        """
        Serialize the public key to the given format and encoding.
        :param format_: Format to use for the public key.
        :param encoding: Encoding (PEM, DER, etc.).
        :return: The encoded public key.
        """
class AsymKeySerializable(DoubleSerializable, metaclass=ABCMeta):
    """Interface for encoding and decoding asymmetric key pairs."""
    @classmethod
    @abstractmethod
    def decode_private_key(cls, data: bytes, format_: ASymKeyFormat, encoding: ASymKeyEncoding, password: bytes | None = None) -> _te.Self:
        """
        Deserialize a private key from the given encoded data.
        :param data:: Encoded private key data.
        :param format_: The key format (e.g., PKCS8).
        :param encoding: The key encoding (e.g., PEM, DER).
        :param password: Password used to decrypt the private key if encrypted.
        :return: A new instance of the key pair object containing the private key.
        """
    @classmethod
    @abstractmethod
    def decode_public_key(cls, data: bytes, format_: ASymKeyFormat, encoding: ASymKeyEncoding) -> _te.Self:
        """
        Deserialize a public key from the given encoded data.
        :param data: Encoded public key data.
        :param format_: The key format (e.g., SubjectPublicKeyInfo).
        :param encoding: The key encoding (e.g., PEM, DER).
        :return: An instance containing only the public key.
        """
    @abstractmethod
    def encode_private_key(self, format_: ASymKeyFormat, encoding: ASymKeyEncoding, password: bytes | None = None) -> bytes:
        """
        Serialize the private key to the given format and encoding.
        :param format_: Format to use for the private key.
        :param encoding: Encoding (PEM, DER, etc.).
        :param password: If provided, encrypts the private key with this password.
        :return: The encoded private key.
        """
    @abstractmethod
    def encode_public_key(self, format_: ASymKeyFormat, encoding: ASymKeyEncoding) -> bytes:
        """
        Serialize the public key to the given format and encoding.
        :param format_: Format to use for the public key.
        :param encoding: Encoding (PEM, DER, etc.).
        :return: The encoded public key.
        """

# Capabilities
class SymKeyEncryptable(metaclass=ABCMeta):
    """Interface for symmetric encryption and decryption."""
    @abstractmethod
    def encrypt(self, plain_bytes: bytes, padding: SymPadding, mode: SymOperation, /, *, auto_pack: bool = True) -> bytes | dict[str, bytes]:
        """
        Encrypt a block of plaintext bytes.
        :param plain_bytes: The plaintext data to encrypt.
        :param padding: The padding scheme to apply.
        :param mode: The cipher operation mode (e.g., CBC, GCM).
        :param auto_pack: If all data should be packed into one bytes object.
        :return: The encrypted output, either as raw bytes or a structured dictionary depending on `auto_pack`.
        """
    @abstractmethod
    def decrypt(self, cipher_bytes_or_dict: bytes | dict[str, bytes], padding: SymPadding, mode: SymOperation, /, *, auto_pack: bool = True) -> bytes:
        """
        Decrypt ciphertext bytes into plaintext.
        :param cipher_bytes_or_dict: The ciphertext input, either as raw bytes or a dictionary containing metadata.
        :param padding: The padding scheme used during encryption.
        :param mode: The cipher operation mode.
        :param auto_pack: If True, expects bytes. Defaults to True.
        :return: The decrypted plaintext bytes.
        """
class SymKeyMACCapable(metaclass=ABCMeta):
    """Interface for MAC generation and verification."""
    @abstractmethod
    def generate_mac(self, data: bytes, auth_type: MessageAuthenticationCode) -> bytes:
        """
        Generate a message authentication code.

        :param data: Message to authenticate.
        :param auth_type: Type of MAC (e.g., HMAC, CMAC).
        :return: Generated MAC bytes.
        """

    @abstractmethod
    def verify_mac(self, data: bytes, mac: bytes, auth_type: MessageAuthenticationCode) -> bool:
        """
        Verify a message authentication code.

        :param data: Original message.
        :param mac: Expected MAC.
        :param auth_type: MAC type used.
        :return: True if MAC is valid, else False.
        """
class AsymKeyEncryptable(metaclass=ABCMeta):
    """Interface for public-key encryption and decryption."""
    @abstractmethod
    def encrypt(self, plain_bytes: bytes, padding: ASymPadding) -> bytes:
        """
        Encrypt data using the public key and specified padding scheme.
        :param plain_bytes: Data to encrypt.
        :param padding: Padding scheme to use.
        :return: Encrypted ciphertext.
        """
    @abstractmethod
    def decrypt(self, cipher_bytes: bytes, padding: ASymPadding) -> bytes:
        """
        Decrypt data using the private key and specified padding scheme.
        :param cipher_bytes: Data to decrypt.
        :param padding: Padding scheme used during encryption.
        :return: Decrypted plaintext.
        """
class Signable(metaclass=ABCMeta):
    """Interface for signing and verifying data with asymmetric keys."""
    @abstractmethod
    def sign(self, *args: _ty.Any, **kwargs: _ty.Any) -> bytes:
        """TBA"""
    @abstractmethod
    def sign_verify(self, *args: _ty.Any, **kwargs: _ty.Any) -> bool:
        """TBA"""
class AsymKeySignable(Signable, metaclass=ABCMeta):
    """Interface for signing and verifying data with asymmetric keys."""
    @abstractmethod
    def sign(self, data: bytes, padding: ASymPadding) -> bytes:
        """
        Generate a digital signature for the given data using the private key.
        :param data: Data to sign.
        :param padding: Padding scheme for signing.
        :return: Signature.
        """
    @abstractmethod
    def sign_verify(self, data: bytes, signature: bytes, padding: ASymPadding) -> bool:
        """
        Verify a digital signature using the public key.
        :param data: Original data that was signed.
        :param signature: The signature to verify.
        :param padding: Padding scheme used during signing.
        :return: True if the signature is valid, False otherwise.
        """
class AsymKeyKeyExchangeable(metaclass=ABCMeta):
    """Interface for performing a key exchange operation."""
    @abstractmethod
    def key_exchange(self, peer_public_key: _te.Self) -> bytes:
        """
        Perform a key exchange operation using this private key and a peer's public key.
        :param peer_public_key: The peer's public key.
        :return: The shared secret resulting from the key exchange.
        """
class AsymEncapsulatable(metaclass=ABCMeta):
    """Interface for key encapsulation mechanisms (KEM)."""
    @abstractmethod
    def encapsulate(self) -> tuple[bytes, bytes]:
        """
        Generate a key encapsulation.
        :return: (ciphertext, shared_secret)
        """
    @abstractmethod
    def decapsulate(self, ciphertext: bytes) -> bytes:
        """
        Derive shared secret from encapsulated ciphertext.
        :param ciphertext: The ciphertext from peer.
        :return: The shared secret.
        """

# Advanced
class Fingerprintable(metaclass=ABCMeta):
    """Allows generation of fingerprints from public keys."""
    @abstractmethod
    def fingerprint(self, hash_alg: str = "sha256") -> str:
        """
        Return a hash-based identifier of the key.

        :param hash_alg: Hash function to use.
        :return: Hex-encoded fingerprint.
        """
class Zeroizable(metaclass=ABCMeta):
    """Interface for zeroizing sensitive key material."""
    @abstractmethod
    def zeroize(self) -> None:
        """Securely wipes key material from memory."""


class _BASIC_HASHER(metaclass=ABCMeta):
    """Abstract base class for hashing algorithms."""
    backend: Backend

    @abstractmethod
    def hash(self, *args: _ty.Any, **kwargs: _ty.Any) -> bytes:
        """
        Generate a hash of the given input data.
        :param to_hash: The input data to hash.
        :param text_ids: Add text ids to the resulting hash
        :return: The resulting hash digest.
        """
    @abstractmethod
    def verify(self, to_verify: bytes, original_hash: bytes, *args: _ty.Any, **kwargs: _ty.Any) -> bool:  # , text_ids: bool = True
        """
        Verify that the hash of the given input matches the provided hash.
        :param to_verify: The input data to hash and verify.
        :param original_hash: The original hash to compare against.
        :return: True if the hash matches, False otherwise.
        """


_HASHLITERAL = _ty.Literal[
    4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
    15, 16, 17, 18, 19, 20, 21, 22, 23, 24,
    25, 26, 27, 28, 29, 30, 31, 32, 33
]
_HASHALGOLITERAL = _ty.Literal[
    "sha1",
    "sha224",
    "sha256",
    "sha384",
    "sha512",
    "sha512_224",
    "sha512_256",
    "sha3_224",
    "sha3_256",
    "sha3_384",
    "sha3_512",
    "sha3_shake_128",
    "sha3_shake_256",
    "sha3_turbo_shake_128",
    "sha3_turbo_shake_256",
    "sha3_kangaroo_twelve",
    "sha3_tuple_hash_128",
    "sha3_tuple_hash_256",
    "sha3_keccak",
    "sha3_cshake_128",
    "sha3_cshake_256",
    "blake2b",
    "blake2s",
    "md2",
    "md4",
    "md5",
    "sm3",
    "ripemd160",
    "bcrypt",
    "argon2"
]
_HASHID_TO_STRING: dict[_HASHLITERAL, str] = {
             4: "sha1",
             5: "sha224",
             6: "sha256",
             7: "sha384",
             8: "sha512",
             9: "sha512_224",
            10: "sha512_256",
            11: "sha3_224",
            12: "sha3_256",
            13: "sha3_384",
            14: "sha3_512",
            15: "sha3_shake_128",
            16: "sha3_shake_256",
            17: "sha3_turbo_shake_128",
            18: "sha3_turbo_shake_256",
            19: "sha3_kangaroo_twelve",
            20: "sha3_tuple_hash_128",
            21: "sha3_tuple_hash_256",
            22: "sha3_keccak",
            23: "blake2b",
            24: "blake2s",
            25: "md2",
            26: "md4",
            27: "md5",
            28: "sm3",
            29: "ripemd160",
            30: "bcrypt",
            31: "argon2",
            32: "cshake_128",
            33: "cshake_256"
        }
class _HASHER_BACKEND(_BASIC_HASHER):
    _MAPPING: dict[str, tuple[_a.Callable[[bytes], bytes], _a.Callable[[bytes, bytes], bool]]] = {}

    def __init__(self, hash_algorithm: _HASHALGOLITERAL):  # , hash_type: _HASHLITERAL
        # self.hash_type: _HASHLITERAL = hash_type
        #algorithm: str  #  | None = _HASHID_TO_STRING.get(hash_type)
        if hash_algorithm not in list(_HASHID_TO_STRING.values()):#not algorithm:
            raise ValueError(f"Unsupported hash algorithm {hash_algorithm}")
        self.algorithm: str = hash_algorithm

    @classmethod
    def verify_unknown(cls, to_verify: bytes, original_hash: bytes, /, fallback_algorithm: str = "sha256", text_ids: bool = True) -> bool:
        algorithm: str = fallback_algorithm
        if text_ids:
            _, algo, original_hash = original_hash.split(b"$", maxsplit=2)
            algorithm = algo.decode("utf-8")
        impl: tuple[_a.Callable[[bytes], bytes], _a.Callable[[bytes, bytes], bool]] | None = cls._MAPPING.get(algorithm)
        if impl is None:
            raise _NotSupportedError(f"Could not verify unknown algorithm '{algorithm}'.")
        return impl[1](to_verify, original_hash)

    def hash(self, to_hash: bytes, /, text_ids: bool = True) -> bytes:
        impl: tuple[_a.Callable[[bytes], bytes], _a.Callable[[bytes, bytes], bool]] | None = self._MAPPING.get(self.algorithm)
        if impl is None:
            raise _NotSupportedError(f"The {self} hash is not supported by this backend")
        result: bytes = impl[0](to_hash)
        if text_ids:
            result = b"$" + self.algorithm.encode("utf-8") + b"$" + result
        return result

    def verify(self, to_verify: bytes, original_hash: bytes, /, text_ids: bool = True) -> bool:
        impl: tuple[_a.Callable[[bytes], bytes], _a.Callable[[bytes, bytes], bool]] | None = self._MAPPING.get(self.algorithm)
        if impl is None:
            raise _NotSupportedError(f"The {self} hash is not supported by this backend")
        if text_ids:
            _, _, original_hash = original_hash.split(b"$", maxsplit=2)
        return impl[1](to_verify, original_hash)

    def __str__(self) -> str:
        return self.algorithm

    def __repr__(self) -> str:
        return f"<HashBackend alg={self.algorithm}>"


class _HASHER_WITH_LEN_BACKEND(_HASHER_BACKEND):
    def hash(self, to_hash: bytes, hash_len: int, /, text_ids: bool = True) -> bytes:
        impl: tuple[_a.Callable[[bytes, int], bytes], _a.Callable[[bytes, bytes], bool]] | None = _HASHER_BACKEND._MAPPING.get(self.algorithm)
        if impl is None:
            raise _NotSupportedError(f"The {self} hash is not supported by this backend")
        result: bytes = impl[0](to_hash, hash_len)
        if text_ids:
            result = b"$" + self.algorithm.encode("utf-8") + b"$" + result
        return result

# TODO: REMOVE WHEN THE CIRCULAR IMPORTS ARE FIXED
class _hash_algorithm:
    class SHA2:
        SHA256 = _HASHER_BACKEND("sha256")
    MD5 = _HASHER_BACKEND("md5")


class _BASIC_KEY_DERIVATION_FUNC(metaclass=ABCMeta):
    """Abstract base class for key derivation functions (KDFs)."""
    backend: Backend
    _IMPL: _a.Callable[..., bytes] | None = None

    # @classmethod
    # @abstractmethod
    # def derive(cls, password: bytes) -> bytes:
    #     """
    #     Derive a cryptographic key from a password.
    #     :param password: The input password or secret to derive the key from.
    #     :return: The derived key of the requested length.
    #     """


kdfs = [
    "pbkdf2hmac",
    "scrypt",
    "hkdf",
    "x963",
    "concatkdf",
    "pbkdf1",
    "kmac128",
    "kmac256",
    "argon2",
    "kkdf",
    "bcrypt",
]
class PBKDF2HMAC(_BASIC_KEY_DERIVATION_FUNC):
    """Password-Based Key Derivation Function 2"""
    _IMPL: _a.Callable[[bytes, bytes, int, int, str], bytes] | None = None

    @classmethod
    def derive(cls, password: bytes, *, salt: bytes, length: int = 32, iterations: int = 100_000,
               hash_alg: _HASHER_BACKEND = _hash_algorithm.SHA2.SHA256) -> bytes:
        """

        :param password:
        :param salt:
        :param length:
        :param iterations:
        :param hash_alg:
        :return:
        """
        if cls._IMPL is None:
            raise _NotSupportedError(f"The {cls()} KDF is not supported by this backend")  # Throw tantrum
        return cls._IMPL(password, salt, length, iterations, hash_alg.algorithm)

    def __str__(self) -> str:
        return "PBKDF2HMAC"


class Scrypt(_BASIC_KEY_DERIVATION_FUNC):
    """TBA"""
    _IMPL: _a.Callable[[bytes, bytes | None, int, int, int, int], bytes] | None = None

    @classmethod
    def derive(cls, password: bytes, *, salt: bytes, length: int = 32,
               n: int = 2**14, r: int = 8, p: int = 1) -> bytes:
        """

        :param password:
        :param salt:
        :param length:
        :param n:
        :param r:
        :param p:
        :return:
        """
        if cls._IMPL is None:
            raise _NotSupportedError(f"The {cls()} KDF is not supported by this backend")  # Throw tantrum
        return cls._IMPL(password, salt, length, n, r, p)

    def __str__(self) -> str:
        return "Scrypt"


class HKDF(_BASIC_KEY_DERIVATION_FUNC):
    """HMAC-based Extract-and-Expand Key Derivation Function"""
    _IMPL: _a.Callable[[bytes, bytes | None, bytes, int, str], bytes] | None = None

    @classmethod
    def derive(cls, password: bytes, *, salt: bytes, info: bytes = b"",
               length: int = 32, hash_alg: _HASHER_BACKEND = _hash_algorithm.SHA2.SHA256) -> bytes:
        """

        :param password:
        :param salt:
        :param info:
        :param length:
        :param hash_alg:
        :return:
        """
        if cls._IMPL is None:
            raise _NotSupportedError(f"The {cls()} KDF is not supported by this backend")  # Throw tantrum
        return cls._IMPL(password, salt, info, length, hash_alg.algorithm)

    def __str__(self) -> str:
        return "HKDF"


class X963(_BASIC_KEY_DERIVATION_FUNC):
    """TBA"""
    _IMPL: _a.Callable[[bytes, int, bytes, str], bytes] | None = None

    @classmethod
    def derive(cls, password: bytes, *, length: int = 32, otherinfo: bytes, hash_alg: _HASHER_BACKEND = _hash_algorithm.SHA2.SHA256) -> bytes:
        """

        :param password:
        :param length:
        :param otherinfo:
        :param hash_alg:
        :return:
        """
        if cls._IMPL is None:
            raise _NotSupportedError(f"The {cls()} KDF is not supported by this backend")  # Throw tantrum
        return cls._IMPL(password, length, otherinfo, hash_alg.algorithm)

    def __str__(self) -> str:
        return "X963"


class ConcatKDF(X963):
    """TBA"""
    def __str__(self) -> str:
        return "ConcatKDF"


class PBKDF1(_BASIC_KEY_DERIVATION_FUNC):
    """TBA"""
    _IMPL: _a.Callable[[bytes, bytes, int, int, str], bytes] | None = None

    @classmethod
    def derive(cls, password: bytes, *, salt: bytes, length: int = 32, iterations: int = 1_000,
               hash_alg: _HASHER_BACKEND = _hash_algorithm.MD5) -> bytes:
        """

        :param password:
        :param salt:
        :param length:
        :param iterations:
        :param hash_alg:
        :return:
        """
        if cls._IMPL is None:
            raise _NotSupportedError(f"The {cls()} KDF is not supported by this backend")  # Throw tantrum
        return cls._IMPL(password, salt, length, iterations, hash_alg.algorithm)

    def __str__(self) -> str:
        return "PBKDF1"


class KMAC128(_BASIC_KEY_DERIVATION_FUNC):
    """TBA"""
    _IMPL: _a.Callable[[bytes, int, bytes, bytes], bytes] | None = None

    @classmethod
    def derive(cls, password: bytes, *, length: int, key: bytes = b"", customization: bytes = b"") -> bytes:
        """

        :param password:
        :param length:
        :param key:
        :param customization:
        :return:
        """
        if cls._IMPL is None:
            raise _NotSupportedError(f"The {cls()} KDF is not supported by this backend")  # Throw tantrum
        return cls._IMPL(password, length, key, customization)

    def __str__(self) -> str:
        return "KMAC128"


class KMAC256(KMAC128):
    def __str__(self) -> str:
        return "KMAC256"


class ARGON2(_BASIC_KEY_DERIVATION_FUNC):
    """TBA"""
    _IMPL: _a.Callable[[bytes, bytes, int, int, int, int, _ty.Literal["i", "d", "id"]], bytes] | None = None

    @classmethod
    def derive(cls, password: bytes, *, salt: bytes, length: int = 32, time_cost: int = 2,
               memory_cost: int = 102_400, parallelism: int = 8, variant: _ty.Literal["i", "d", "id"] = "i") -> bytes:
        """

        :param password:
        :param salt:
        :param length:
        :param time_cost:
        :param memory_cost:
        :param parallelism:
        :param variant:
        :return:
        """
        if cls._IMPL is None:
            raise _NotSupportedError(f"The {cls()} KDF is not supported by this backend")  # Throw tantrum
        return cls._IMPL(password, salt, length, time_cost, memory_cost, parallelism, variant)

    def __str__(self) -> str:
        return "ARGON2"


class KKDF(_BASIC_KEY_DERIVATION_FUNC):
    """TBA"""
    _IMPL: _a.Callable[[bytes, int, bytes], bytes] | None = None

    @classmethod
    def derive(cls, password: bytes, *, length: int = 32, salt: bytes = b"") -> bytes:
        """

        :param password:
        :param length:
        :param salt:
        :return:
        """
        if cls._IMPL is None:
            raise _NotSupportedError(f"The {cls()} KDF is not supported by this backend")  # Throw tantrum
        return cls._IMPL(password, length, salt)

    def __str__(self) -> str:
        return "KKDF"


class BCRYPT(_BASIC_KEY_DERIVATION_FUNC):
    """TBA"""
    _IMPL: _a.Callable[[bytes, bytes, int, int], bytes] | None = None

    @classmethod
    def derive(cls, password: bytes, /, salt: bytes, rounds: int = 12, length: int = 32) -> bytes:
        """

        :param password:
        :param salt:
        :param rounds:
        :param length:
        :return:
        """
        if cls._IMPL is None:
            raise _NotSupportedError(f"The {cls()} KDF is not supported by this backend")  # Throw tantrum
        return cls._IMPL(password, salt, rounds, length)

    def __str__(self) -> str:
        return "BCRYPT"


_AES_KEYSIZES = (128, 192, 256)
_AES_KEYLITERAL = _ty.Literal[128, 192, 256]
class _AES_KEYTYPE(
    _BaseSymmetricKey,
    SymKeyEncryptable,
    SymKeyMACCapable,
    SymKeySerializable,
    metaclass=ABCMeta
):
    cipher = "AES"
    def __init__(self, key_size: _AES_KEYLITERAL, pwd: _ty.Optional[bytes | str]) -> None: ...

    @classmethod
    def new(cls, pwd_or_keysize: _AES_KEYLITERAL | tuple[_AES_KEYLITERAL, str | bytes]) -> _te.Self:
        """TBA"""
        if not cls.__concrete__:
            raise _NotSupportedError(f"The {cls.cipher} cipher is not supported by this backend")
        pwd: str | bytes | None = None
        key_size: _AES_KEYLITERAL

        if isinstance(pwd_or_keysize, int) and pwd_or_keysize in _AES_KEYSIZES:
            key_size = pwd_or_keysize
        elif isinstance(pwd_or_keysize, tuple) and len(pwd_or_keysize) == 2 and \
             isinstance((key_size := pwd_or_keysize[0]), int) and key_size in _AES_KEYSIZES and \
             isinstance((pwd := pwd_or_keysize[1]), (str, bytes)):
            pass  # key_size = _ty.cast(_AES_KEYLITERAL, key_size_or_key)
        else:
            raise ValueError(f"pwd_or_keysize needs to be of type '{_AES_KEYLITERAL} | tuple[{_AES_KEYLITERAL}, str | bytes]', and not '{repr(pwd_or_keysize)}'")
        return cls(key_size, pwd)
class AES(SymCipher):
    """Advanced Encryption Standard"""
    key: _ty.Type[_AES_KEYTYPE] = _AES_KEYTYPE


class _ChaCha20_KEYTYPE(
    _BaseSymmetricKey,
    SymKeyEncryptable,
    SymKeySerializable,
    metaclass=ABCMeta
):
    cipher = "ChaCha20"
    def __init__(self, pwd: _ty.Optional[bytes | str] = None) -> None: ...

    @classmethod
    def new(cls, pwd: bytes | str | None = None) -> _te.Self:
        if not cls.__concrete__:
            raise _NotSupportedError(f"The {cls.cipher} cipher is not supported by this backend")
        if not (isinstance(pwd, (bytes, str)) or pwd is None):
            raise ValueError(f"pwd needs to be of type 'bytes | str | None', and not '{repr(pwd)}'")
        return cls(pwd)
class ChaCha20(SymCipher):
    key: _ty.Type[_ChaCha20_KEYTYPE] = _ChaCha20_KEYTYPE


class _TripleDES_KEYTYPE(
    _BaseSymmetricKey,
    SymKeyEncryptable,
    SymKeySerializable,
    metaclass=ABCMeta
):
    cipher = "TripleDES"
    def __init__(self, key_size: _ty.Literal[192], pwd: _ty.Optional[bytes | str] = None) -> None: ...

    @classmethod
    def new(cls, pwd: bytes | str | None = None) -> _te.Self:
        if not cls.__concrete__:
            raise _NotSupportedError(f"The {cls.cipher} cipher is not supported by this backend")
        if not (isinstance(pwd, (bytes, str)) or pwd is None):
            raise ValueError(f"pwd needs to be of type 'bytes | str | None', and not '{repr(pwd)}'")
        return cls(192, pwd)
class TripleDES(SymCipher):
    key: _ty.Type[_TripleDES_KEYTYPE] = _TripleDES_KEYTYPE


_Blowfish_KEYSIZES = (128, 256)
_Blowfish_KEYLITERAL = _ty.Literal[128, 256]
class _Blowfish_KEYTYPE(
    _BaseSymmetricKey,
    SymKeyEncryptable,
    SymKeySerializable,
    metaclass=ABCMeta
):
    cipher = "Blowfish"
    def __init__(self, key_size: _ty.Literal[128, 256], pwd: _ty.Optional[bytes | str] = None) -> None: ...

    @classmethod
    def new(cls, pwd_or_keysize: _Blowfish_KEYLITERAL | tuple[_Blowfish_KEYLITERAL, str | bytes]) -> _te.Self:
        if not cls.__concrete__:
            raise _NotSupportedError(f"The {cls.cipher} cipher is not supported by this backend")
        pwd: str | bytes | None = None
        key_size: _Blowfish_KEYLITERAL

        if isinstance(pwd_or_keysize, int) and pwd_or_keysize in _Blowfish_KEYSIZES:
            key_size = pwd_or_keysize
        elif isinstance(pwd_or_keysize, tuple) and len(pwd_or_keysize) == 2 and \
             isinstance((key_size := pwd_or_keysize[0]), int) and key_size in _Blowfish_KEYSIZES and \
             isinstance((pwd := pwd_or_keysize[1]), (str, bytes)):
            pass  # key_size = _ty.cast(_Blowfish_KEYLITERAL, key_size_or_key)
        else:
            raise ValueError(f"pwd_or_keysize needs to be of type '{_Blowfish_KEYLITERAL} | tuple[{_Blowfish_KEYLITERAL}, str | bytes]', and not '{repr(pwd_or_keysize)}'")
        return cls(key_size, pwd)
class Blowfish(SymCipher):
    key: _ty.Type[_Blowfish_KEYTYPE] = _Blowfish_KEYTYPE


_CAST5_KEYSIZES = (40, 128)
_CAST5_KEYLITERAL = _ty.Literal[40, 128]
class _CAST5_KEYTYPE(
    _BaseSymmetricKey,
    SymKeyEncryptable,
    SymKeySerializable,
    metaclass=ABCMeta
):
    cipher = "CAST5"
    def __init__(self, key_size: _ty.Literal[40, 128], pwd: _ty.Optional[bytes | str] = None) -> None: ...

    @classmethod
    def new(cls, pwd_or_keysize: _CAST5_KEYLITERAL | tuple[_CAST5_KEYLITERAL, str | bytes]) -> _te.Self:
        if not cls.__concrete__:
            raise _NotSupportedError(f"The {cls.cipher} cipher is not supported by this backend")
        pwd: str | bytes | None = None
        key_size: _CAST5_KEYLITERAL

        if isinstance(pwd_or_keysize, int) and pwd_or_keysize in _CAST5_KEYSIZES:
            key_size = pwd_or_keysize
        elif isinstance(pwd_or_keysize, tuple) and len(pwd_or_keysize) == 2 and \
             isinstance((key_size := pwd_or_keysize[0]), int) and key_size in _CAST5_KEYSIZES and \
             isinstance((pwd := pwd_or_keysize[1]), str):
            pass  # key_size = _ty.cast(_CAST5_KEYLITERAL, __item)
        else:
            raise ValueError(f"pwd_or_keysize needs to be of type '{_CAST5_KEYLITERAL} | tuple[{_CAST5_KEYLITERAL}, str | bytes]', and not '{repr(pwd_or_keysize)}'")
        return cls(key_size, pwd)
class CAST5(SymCipher):
    key: _ty.Type[_CAST5_KEYTYPE] = _CAST5_KEYTYPE


class _ARC4_KEYTYPE(
    _BaseSymmetricKey,
    SymKeyEncryptable,
    SymKeySerializable,
    metaclass=ABCMeta
):
    cipher = "ARC4"
    def __init__(self, pwd: _ty.Optional[bytes | str] = None) -> None: ...

    @classmethod
    def new(cls, pwd: bytes | str | None = None) -> _te.Self:
        if not cls.__concrete__:
            raise _NotSupportedError(f"The {cls.cipher} cipher is not supported by this backend")
        if not (isinstance(pwd, (bytes, str)) or pwd is None):
            raise ValueError(f"pwd needs to be of type 'bytes | str | None', and not '{repr(pwd)}'")
        return cls(pwd)
class ARC4(SymCipher):
    key: _ty.Type[_ARC4_KEYTYPE] = _ARC4_KEYTYPE


_Camellia_KEYSIZES = (128, 192, 256)
_Camellia_KEYLITERAL = _ty.Literal[128, 192, 256]
class _Camellia_KEYTYPE(
    _BaseSymmetricKey,
    SymKeyEncryptable,
    SymKeySerializable,
    metaclass=ABCMeta
):
    cipher = "Camellia"
    def __init__(self, key_size: _Camellia_KEYLITERAL, pwd: _ty.Optional[bytes | str] = None) -> None: ...

    @classmethod
    def new(cls, pwd_or_keysize: _Camellia_KEYLITERAL | tuple[_Camellia_KEYLITERAL, str | bytes]) -> _te.Self:
        if not cls.__concrete__:
            raise _NotSupportedError(f"The {cls.cipher} cipher is not supported by this backend")
        pwd: str | bytes | None = None
        key_size: _Camellia_KEYLITERAL

        if isinstance(pwd_or_keysize, int) and pwd_or_keysize in _Camellia_KEYSIZES:
            key_size = pwd_or_keysize
        elif isinstance(pwd_or_keysize, tuple) and len(pwd_or_keysize) == 2 and \
             isinstance((key_size := pwd_or_keysize[0]), int) and key_size in _Camellia_KEYSIZES and \
             isinstance((pwd := pwd_or_keysize[1]), (str, bytes)):
            pass  # key_size = _ty.cast(_Camellia_KEYLITERAL, pwd_or_keysize)
        else:
            raise ValueError(f"pwd_or_keysize needs to be of type '{_Camellia_KEYLITERAL} | tuple[{_Camellia_KEYLITERAL}, str | bytes]', and not '{repr(pwd_or_keysize)}'")
        return cls(key_size, pwd)
class Camellia(SymCipher):
    key: _ty.Type[_Camellia_KEYTYPE] = _Camellia_KEYTYPE


class _IDEA_KEYTYPE(
    _BaseSymmetricKey,
    SymKeyEncryptable,
    SymKeySerializable,
    metaclass=ABCMeta
):
    cipher = "IDEA"
    def __init__(self, pwd: _ty.Optional[bytes | str] = None) -> None: ...

    @classmethod
    def new(cls, pwd: bytes | str | None = None) -> _te.Self:
        if not cls.__concrete__:
            raise _NotSupportedError(f"The {cls.cipher} cipher is not supported by this backend")
        if not (isinstance(pwd, (bytes, str)) or pwd is None):
            raise ValueError(f"pwd needs to be of type 'bytes | str | None', and not '{repr(pwd)}'")
        return cls(pwd)
class IDEA(SymCipher):
    key: _ty.Type[_IDEA_KEYTYPE] = _IDEA_KEYTYPE


class _SEED_KEYTYPE(
    _BaseSymmetricKey,
    SymKeyEncryptable,
    SymKeySerializable,
    metaclass=ABCMeta
):
    cipher = "SEED"
    def __init__(self, pwd: _ty.Optional[bytes | str] = None) -> None: ...

    @classmethod
    def new(cls, pwd: bytes | str | None = None) -> _te.Self:
        if not cls.__concrete__:
            raise _NotSupportedError(f"The {cls.cipher} cipher is not supported by this backend")
        if not (isinstance(pwd, (bytes, str)) or pwd is None):
            raise ValueError(f"pwd needs to be of type 'bytes | str | None', and not '{repr(pwd)}'")
        return cls(pwd)
class SEED(SymCipher):
    key: _ty.Type[_SEED_KEYTYPE] = _SEED_KEYTYPE


class _SM4_KEYTYPE(
    _BaseSymmetricKey,
    SymKeyEncryptable,
    SymKeySerializable,
    metaclass=ABCMeta
):
    cipher = "SM4"
    def __init__(self, pwd: _ty.Optional[bytes | str] = None): ...

    @classmethod
    def new(cls, pwd: bytes | str | None = None) -> _te.Self:
        if not cls.__concrete__:
            raise _NotSupportedError(f"The {cls.cipher} cipher is not supported by this backend")
        if not (isinstance(pwd, (bytes, str)) or pwd is None):
            raise ValueError(f"pwd needs to be of type 'bytes | str | None', and not '{repr(pwd)}'")
        return cls(pwd)
class SM4(SymCipher):
    key: _ty.Type[_SM4_KEYTYPE] = _SM4_KEYTYPE


class _DES_KEYTYPE(
    _BaseSymmetricKey,
    SymKeyEncryptable,
    SymKeySerializable,
    metaclass=ABCMeta
):
    cipher = "DES"
    def __init__(self, pwd: _ty.Optional[bytes | str] = None) -> None: ...

    @classmethod
    def new(cls, pwd: bytes | str | None = None) -> _te.Self:
        """
        if isinstance(pwd, (bytes, str)):
            if len(pwd) * 8 != 64:
                raise ValueError(f"Can't accept key of size '{len(pwd) * 8}' for the {cls()} cipher, please use a 64-bit long one")
            elif pwd is not None:
                raise ValueError(f"pwd needs to be of type 'bytes | str | None', and not '{repr(pwd)}'")
        """
        if not cls.__concrete__:
            raise _NotSupportedError(f"The {cls.cipher} cipher is not supported by this backend")
        if not (isinstance(pwd, (bytes, str)) or pwd is None):
            raise ValueError(f"pwd needs to be of type 'bytes | str | None', and not '{repr(pwd)}'")
        return cls(pwd)
class DES(SymCipher):
    key: _ty.Type[_DES_KEYTYPE] = _DES_KEYTYPE


_ARC2_KEYSIZES = (40, 64, 128)
_ARC2_KEYLITERAL = _ty.Literal[40, 64, 128]
class _ARC2_KEYTYPE(
    _BaseSymmetricKey,
    SymKeyEncryptable,
    SymKeySerializable,
    metaclass=ABCMeta
):
    cipher = "ARC2"
    def __init__(self, key_size: _ARC2_KEYLITERAL = 128, pwd: _ty.Optional[bytes | str] = None) -> None: ...

    @classmethod
    def new(cls, pwd_or_keysize: _ARC2_KEYLITERAL | tuple[_ARC2_KEYLITERAL, str | bytes]) -> _te.Self:
        if not cls.__concrete__:
            raise _NotSupportedError(f"The {cls.cipher} cipher is not supported by this backend")
        pwd: str | bytes | None = None
        key_size: _ARC2_KEYLITERAL

        if isinstance(pwd_or_keysize, int) and pwd_or_keysize in _ARC2_KEYSIZES:
            key_size = pwd_or_keysize
        elif isinstance(pwd_or_keysize, tuple) and len(pwd_or_keysize) == 2 and \
             isinstance((key_size := pwd_or_keysize[0]), int) and key_size in _ARC2_KEYSIZES and \
             isinstance((pwd := pwd_or_keysize[1]), (str, bytes)):
            pass  # key_size = _ty.cast(_ARC2_KEYLITERAL, pwd_or_keysize)
        else:
            raise ValueError(f"pwd_or_keysize needs to be of type '{_ARC2_KEYLITERAL} | tuple[{_ARC2_KEYLITERAL}, str | bytes]', and not '{repr(pwd_or_keysize)}'")

        return cls(key_size, pwd)
class ARC2(SymCipher):
    key: _ty.Type[_ARC2_KEYTYPE] = _ARC2_KEYTYPE


_Salsa20_KEYSIZES = (128, 256)
_Salsa20_KEYLITERAL = _ty.Literal[128, 256]
class _Salsa20_KEYTYPE(
    _BaseSymmetricKey,
    SymKeyEncryptable,
    SymKeySerializable,
    metaclass=ABCMeta
):
    cipher = "Salsa20"
    def __init__(self, key_size: _Salsa20_KEYLITERAL = 256, pwd: _ty.Optional[bytes | str] = None) -> None: ...

    @classmethod
    def new(cls, pwd_or_keysize: _Salsa20_KEYLITERAL | tuple[_Salsa20_KEYLITERAL, str | bytes]) -> _te.Self:
        if not cls.__concrete__:
            raise _NotSupportedError(f"The {cls.cipher} cipher is not supported by this backend")
        pwd: str | bytes | None = None
        key_size: _Salsa20_KEYLITERAL

        if isinstance(pwd_or_keysize, int) and pwd_or_keysize in _Salsa20_KEYSIZES:
            key_size = pwd_or_keysize
        elif isinstance(pwd_or_keysize, tuple) and len(pwd_or_keysize) == 2 and \
             isinstance((key_size := pwd_or_keysize[0]), int) and key_size in _Salsa20_KEYSIZES and \
             isinstance((pwd := pwd_or_keysize[1]), (str, bytes)):
            pass  # key_size = _ty.cast(_Salsa20_KEYLITERAL, pwd_or_keysize)
        else:
            raise ValueError(f"pwd_or_keysize needs to be of type '{_Salsa20_KEYLITERAL} | tuple[{_Salsa20_KEYLITERAL}, str | bytes]', and not '{repr(pwd_or_keysize)}'")
        return cls(key_size, pwd)
class Salsa20(SymCipher):
    key: _ty.Type[_Salsa20_KEYTYPE] = _Salsa20_KEYTYPE


_RSA_KEYSIZES = (512, 768, 1024, 2048, 3072, 4096, 8192, 15360)
_RSA_KEYLITERAL = _ty.Literal[512, 768, 1024, 2048, 3072, 4096, 8192, 15360]
class _RSA_KEYPAIRTYPE(
    _BaseAsymmetricKeypair,
    AsymKeyEncryptable,
    AsymKeySignable,
    AsymKeySerializable,
    metaclass=ABCMeta
):
    cipher = "RSA"
    def __init__(self, key_size: _RSA_KEYLITERAL, pwd: _ty.Optional[bytes | str] = None) -> None: ...

    @classmethod
    def new(cls, pwd_or_keysize: _RSA_KEYLITERAL | tuple[_RSA_KEYLITERAL, str | bytes]) -> _te.Self:
        if not cls.__concrete__:
            raise _NotSupportedError(f"The {cls.cipher} cipher is not supported by this backend")
        pwd: str | bytes | None = None
        key_size: _RSA_KEYLITERAL

        if isinstance(pwd_or_keysize, int) and pwd_or_keysize in _RSA_KEYSIZES:
            key_size = pwd_or_keysize
        elif isinstance(pwd_or_keysize, tuple) and len(pwd_or_keysize) == 2 and \
             isinstance((key_size := pwd_or_keysize[0]), int) and key_size in _RSA_KEYSIZES and \
             isinstance((pwd := pwd_or_keysize[1]), (str, bytes)):
            pass  # key_size = _ty.cast(_RSA_KEYLITERAL, pwd_or_keysize)
        else:
            raise ValueError(f"pwd_or_keysize needs to be of type '{_RSA_KEYLITERAL} | tuple[{_RSA_KEYLITERAL}, str | bytes]', and not '{repr(pwd_or_keysize)}'")
        return cls(key_size, pwd)
class RSA(AsymCipher):
    """Rivest-Shamir-Adleman"""
    keypair: _ty.Type[_RSA_KEYPAIRTYPE] = _RSA_KEYPAIRTYPE


_DSA_KEYSIZES = (1024, 2048, 3072)
_DSA_KEYLITERAL = _ty.Literal[1024, 2048, 3072]
class _DSA_KEYPAIRTYPE(
    _BaseAsymmetricKeypair,
    AsymKeySignable,
    AsymKeySerializable,
    metaclass=ABCMeta
):
    cipher = "DSA"
    def __init__(self, key_size: _DSA_KEYLITERAL, pwd: _ty.Optional[bytes | str] = None) -> None: ...

    @classmethod
    def new(cls, pwd_or_keysize: _DSA_KEYLITERAL | tuple[_DSA_KEYLITERAL, str | bytes]) -> _te.Self:
        if not cls.__concrete__:
            raise _NotSupportedError(f"The {cls.cipher} cipher is not supported by this backend")
        pwd: str | bytes | None = None
        key_size: _DSA_KEYLITERAL

        if isinstance(pwd_or_keysize, int) and pwd_or_keysize in _DSA_KEYSIZES:
            key_size = pwd_or_keysize
        elif isinstance(pwd_or_keysize, tuple) and len(pwd_or_keysize) == 2 and \
             isinstance((key_size := pwd_or_keysize[0]), int) and key_size in _RSA_KEYSIZES and \
             isinstance((pwd := pwd_or_keysize[1]), (str, bytes)):
            pass  # key_size = _ty.cast(_DSA_KEYLITERAL, pwd_or_keysize)
        else:
            raise ValueError(f"pwd_or_keysize needs to be of type '{_DSA_KEYLITERAL} | tuple[{_DSA_KEYLITERAL}, str | bytes]', and not '{repr(pwd_or_keysize)}'")
        return cls(key_size, pwd)
class DSA(AsymCipher):
    """Digital Signature Algorithm"""
    keypair: _ty.Type[_DSA_KEYPAIRTYPE] = _DSA_KEYPAIRTYPE


class ECCCurve(enum.Enum):
    """Elliptic key functions"""
    SECP192R1 = (None, "")
    SECP224R1 = (None, "")
    SECP256K1 = (None, "")
    SECP256R1 = (None, "")  # Default
    SECP384R1 = (None, "")
    SECP521R1 = (None, "")
    SECT163K1 = (None, "")
    SECT163R2 = (None, "")
    SECT233K1 = (None, "")
    SECT233R1 = (None, "")
    SECT283K1 = (None, "")
    SECT283R1 = (None, "")
    SECT409K1 = (None, "")
    SECT409R1 = (None, "")
    SECT571K1 = (None, "")
    SECT571R1 = (None, "")
class ECCType(enum.Enum):
    """How the signing is done, heavily affects the performance, key generation and what you can do with it"""
    ECDSA = (None, "Elliptic Curve Digital Signature Algorithm")
    Ed25519 = (None, "")
    Ed448 = (None, "")
    X25519 = (None, "")
    X448 = (None, "")
class _ECC_KEYPAIRTYPE(
    _BaseAsymmetricKeypair,
    AsymKeySignable,
    AsymKeyKeyExchangeable,
    AsymKeySerializable,
    metaclass=ABCMeta
):
    cipher = "ECC"
    def __init__(self, ecc_type: ECCType = ECCType.ECDSA, ecc_curve: ECCCurve | None = ECCCurve.SECP256R1,
                 pwd: _ty.Optional[bytes | str] = None) -> None: ...

    @classmethod
    def new(cls, __item: _ty.Any) -> _te.Self:
        """
        Creates a new ECC key depending on the provided input.

        Accepted forms:
        - ECC.new((ECCType.ECDSA, ECCCurve.SECP384R1))      # For ECDSA
        - ECC.new((ECCType.X25519, None))                   # For optimized curves
        - ECC.new((ECCType.ECDSA, ECCCurve.SECP384R1, b"..."))  # With private key
        """
        if not cls.__concrete__:
            raise _NotSupportedError(f"The {cls.cipher} cipher is not supported by this backend")

        # If it's a tuple, unpack it
        if isinstance(__item, tuple):
            if len(__item) == 2:
                ecc_type, arg = __item
                if ecc_type == ECCType.ECDSA:
                    return cls.ecdsa_key(ecc_curve=arg)
                else:
                    return cls.optimized_key(ecc_type=ecc_type)
            elif len(__item) == 3:
                ecc_type, curve, priv = __item
                if ecc_type == ECCType.ECDSA:
                    return cls.ecdsa_key(ecc_curve=curve, private_key=priv)
                else:
                    return cls.optimized_key(ecc_type=ecc_type, private_key=priv)

        raise ValueError(
            f"{cls.__name__}.new() requires a tuple of the form:\n"
            f"  (ECCType.ECDSA, ECCCurve)\n"
            f"  (ECCType.OTHER, None)\n"
            f"  or with an optional private key as third item."
        )

    @classmethod
    def ecdsa_key(cls, ecc_curve: ECCCurve = ECCCurve.SECP256R1,
                  private_key: bytes | str | None = None) -> _te.Self:
        """Elliptic Curve Digital Signature Algorithm"""
        if not cls.__concrete__:
            raise _NotSupportedError(f"The {cls.cipher} cipher is not supported by this backend")
        elif not isinstance(ecc_curve, ECCCurve):
            raise ValueError(f"ecc_curve needs to be of type 'ECCCurve', and not '{repr(ecc_curve)}'")
        elif not (isinstance(private_key, (str, bytes)) or private_key is None):
            raise ValueError(f"private_key needs to be of type 'bytes | str | None', and not '{repr(private_key)}'")
        return cls(ECCType.ECDSA, ecc_curve, private_key)

    @classmethod
    def optimized_key(cls, ecc_type: ECCType,
                      private_key: bytes | str | None = None) -> _te.Self:
        """
        TBA
        :param ecc_type:
        :param private_key:
        :return:
        """
        if not cls.__concrete__:
            raise _NotSupportedError(f"The {cls.cipher} cipher is not supported by this backend")
        elif not isinstance(ecc_type, ECCType):
            raise ValueError(f"ecc_type needs to be of type 'ECCType', and not '{repr(ecc_type)}'")
        elif not (isinstance(private_key, (str, bytes)) or private_key is None):
            raise ValueError(f"private_key needs to be of type 'bytes | str | None', and not '{repr(private_key)}'")
        elif ecc_type == ECCType.ECDSA:
            raise ValueError("Please use ECC.ecdsa_key to generate ECDSA keys")
        return cls(ecc_type, None, private_key)
class ECC(AsymCipher):
    """Elliptic Curve Cryptography"""
    keypair: _ty.Type[_ECC_KEYPAIRTYPE] = _ECC_KEYPAIRTYPE
    Curve = ECCCurve
    Type = ECCType


_KYBER_MODES = ("kyber512", "kyber768", "kyber1024")
_KYBER_MODELITERAL = _ty.Literal["kyber512", "kyber768", "kyber1024"]
class _KYBER_KEYPAIRTYPE(
    _BaseAsymmetricKeypair,
    AsymEncapsulatable,
    # SingleSerializable,
    metaclass=ABCMeta
):
    cipher = "KYBER"
    def __init__(self, mode: _KYBER_MODELITERAL) -> None: ...
    @classmethod
    def new(cls, mode: _KYBER_MODELITERAL) -> _te.Self:
        if not cls.__concrete__:
            raise _NotSupportedError(f"The {cls.cipher} cipher is not supported by this backend")
        if mode not in _KYBER_MODES:
            raise ValueError(f"mode must be one of {_KYBER_MODES}, not '{mode}'")
        return cls(mode)
    @classmethod
    @abstractmethod
    def decode(cls, mode: _KYBER_MODELITERAL, *, public_key: bytes | None = None, private_key: bytes | None = None) -> _te.Self: ...
    @abstractmethod
    def encode_private_key(self) -> bytes | None: ...
    @abstractmethod
    def encode_public_key(self) -> bytes | None: ...
class KYBER(AsymCipher):
    keypair: _ty.Type[_KYBER_KEYPAIRTYPE] = _KYBER_KEYPAIRTYPE


_DILITHIUM_MODES = ("dilithium2", "dilithium3", "dilithium5")
_DILITHIUM_MODELITERAL = _ty.Literal["dilithium2", "dilithium3", "dilithium5"]
class _DILITHIUM_KEYPAIRTYPE(
    _BaseAsymmetricKeypair,
    Signable,
    # SingleSerializable,
    metaclass=ABCMeta
):
    cipher = "DILITHIUM"
    def __init__(self, mode: _DILITHIUM_MODELITERAL) -> None: ...
    @classmethod
    def new(cls, mode: _DILITHIUM_MODELITERAL) -> _te.Self:
        if not cls.__concrete__:
            raise _NotSupportedError(f"The {cls.cipher} cipher is not supported by this backend")
        if mode not in _DILITHIUM_MODES:
            raise ValueError(f"mode must be one of {_DILITHIUM_MODES}, not '{mode}'")
        return cls(mode)
    @classmethod
    @abstractmethod
    def decode(cls, mode: _DILITHIUM_MODELITERAL, *, public_key: bytes | None = None, private_key: bytes | None = None) -> _te.Self: ...
    @abstractmethod
    def encode_private_key(self) -> bytes | None: ...
    @abstractmethod
    def encode_public_key(self) -> bytes | None: ...
    @abstractmethod
    def sign(self, data: bytes) -> bytes: ...
    @abstractmethod
    def sign_verify(self, data: bytes, signature: bytes) -> bool: ...
class DILITHIUM(AsymCipher):
    keypair: _ty.Type[_DILITHIUM_KEYPAIRTYPE] = _DILITHIUM_KEYPAIRTYPE


_SPHINCS_MODES = ("sphincs-sha256-128s", "sphincs-sha256-192s", "sphincs-sha256-256s")
_SPHINCS_MODELITERAL = _ty.Literal["sphincs-sha256-128s", "sphincs-sha256-192s", "sphincs-sha256-256s"]
class _SPHINCS_KEYPAIRTYPE(
    _BaseAsymmetricKeypair,
    AsymKeySignable,
    AsymKeySerializable,
    metaclass=ABCMeta
):
    cipher = "SPHINCS+"
    def __init__(self, mode: _SPHINCS_MODELITERAL) -> None: ...

    @classmethod
    def new(cls, mode: _SPHINCS_MODELITERAL) -> _te.Self:
        if not cls.__concrete__:
            raise _NotSupportedError(f"{cls.cipher} not supported by this backend")
        if mode not in _SPHINCS_MODES:
            raise ValueError(f"mode must be one of {_SPHINCS_MODES}, not '{mode}'")
        return cls(mode)
class SPHINCS(AsymCipher):
    keypair: _ty.Type[_SPHINCS_KEYPAIRTYPE] = _SPHINCS_KEYPAIRTYPE


_FRODOKEM_MODES = ("FrodoKEM-640", "FrodoKEM-976", "FrodoKEM-1344")
_FRODOKEM_MODELITERAL = _ty.Literal["FrodoKEM-640", "FrodoKEM-976", "FrodoKEM-1344"]
class _FRODOKEM_KEYPAIRTYPE(
    _BaseAsymmetricKeypair,
    AsymEncapsulatable,
    AsymKeySerializable,
    metaclass=ABCMeta
):
    cipher = "FrodoKEM"
    def __init__(self, mode: _FRODOKEM_MODELITERAL) -> None: ...

    @classmethod
    def new(cls, mode: _FRODOKEM_MODELITERAL) -> _te.Self:
        if not cls.__concrete__:
            raise _NotSupportedError(f"{cls.cipher} not supported by this backend")
        if mode not in _FRODOKEM_MODES:
            raise ValueError(f"mode must be one of {_FRODOKEM_MODES}, not '{mode}'")
        return cls(mode)
class FRODOKEM(AsymCipher):
    keypair: _ty.Type[_FRODOKEM_KEYPAIRTYPE] = _FRODOKEM_KEYPAIRTYPE


_BIKE_MODES = ("bike1l1", "bike1l3", "bike1l5")
_BIKE_MODELITERAL = _ty.Literal["bike1l1", "bike1l3", "bike1l5"]
class _BIKE_KEYPAIRTYPE(
    _BaseAsymmetricKeypair,
    AsymEncapsulatable,
    AsymKeySerializable,
    metaclass=ABCMeta
):
    cipher = "BIKE"
    def __init__(self, mode: _BIKE_MODELITERAL) -> None: ...

    @classmethod
    def new(cls, mode: _BIKE_MODELITERAL) -> _te.Self:
        if not cls.__concrete__:
            raise _NotSupportedError(f"{cls.cipher} not supported by this backend")
        if mode not in _BIKE_MODES:
            raise ValueError(f"mode must be one of {_BIKE_MODES}, not '{mode}'")
        return cls(mode)
class BIKE(AsymCipher):
    keypair: _ty.Type[_BIKE_KEYPAIRTYPE] = _BIKE_KEYPAIRTYPE
