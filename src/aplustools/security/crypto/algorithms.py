from typing import Literal as _Literal, Optional as _Optional
from ...data import EANEnum as _EANEnum
from .exceptions import NotSupportedError as _NotSupportedError
from ._hashes import HashAlgorithm


class _AES:  # Advanced Encryption Standard
    _AES_KEY = None

    @classmethod
    def key(cls, key_size_or_key: _Literal[128, 192, 256] | bytes | str) -> _AES_KEY:
        if cls._AES_KEY is not None:
            if isinstance(key_size_or_key, (bytes, str)):
                key_size = len(key_size_or_key) * 8
                key = key_size_or_key
            else:
                key_size = key_size_or_key
                key = None
            return cls._AES_KEY(key_size, key)
        raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")

    def __str__(self):
        return "AES"

    def __repr__(self):
        return str(self)


class _ChaCha20:  # Advanced Encryption Standard
    _ChaCha20_KEY = None

    @classmethod
    def key(cls, key: _Optional[bytes | str] = None) -> _ChaCha20_KEY:
        if cls._ChaCha20_KEY is not None:
            return cls._ChaCha20_KEY(key)
        raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")

    def __str__(self):
        return "ChaCha20"

    def __repr__(self):
        return str(self)


class _TripleDES:  # Advanced Encryption Standard
    _TripleDES_KEY = None

    @classmethod
    def key(cls, key: _Optional[bytes | str] = None) -> _TripleDES_KEY:
        if cls._TripleDES_KEY is not None:
            return cls._TripleDES_KEY(192, key)
        raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")

    def __str__(self):
        return "TripleDES"

    def __repr__(self):
        return str(self)


class _Blowfish:  # Advanced Encryption Standard
    _Blowfish_KEY = None

    @classmethod
    def key(cls, key_size_or_key: _Literal[128, 256] | bytes | str) -> _Blowfish_KEY:
        if cls._Blowfish_KEY is not None:
            if isinstance(key_size_or_key, (bytes, str)):
                key_size = len(key_size_or_key) * 8
                key = key_size_or_key
            else:
                key_size = key_size_or_key
                key = None
            return cls._Blowfish_KEY(key_size, key)
        raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")

    def __str__(self):
        return "Blowfish"

    def __repr__(self):
        return str(self)


class _CAST5:  # Advanced Encryption Standard
    _CAST5_KEY = None

    @classmethod
    def key(cls, key_size_or_key: _Literal[40, 128] | bytes | str) -> _CAST5_KEY:
        if cls._CAST5_KEY is not None:
            if isinstance(key_size_or_key, (bytes, str)):
                key_size = len(key_size_or_key) * 8
                key = key_size_or_key
            else:
                key_size = key_size_or_key
                key = None
            return cls._CAST5_KEY(key_size, key)
        raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")

    def __str__(self):
        return "CAST5"

    def __repr__(self):
        return str(self)


class _ARC4:
    _ARC4_KEY = None

    @classmethod
    def key(cls, key: _Optional[bytes | str] = None) -> _ARC4_KEY:
        if cls._ARC4_KEY is not None:
            return cls._ARC4_KEY(key)
        raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")

    def __str__(self):
        return "ARC4"

    def __repr__(self):
        return str(self)


class _Camellia:
    _Camellia_KEY = None

    @classmethod
    def key(cls, key_size_or_key: _Literal[128, 192, 256] | bytes | str) -> _Camellia_KEY:
        if cls._Camellia_KEY is not None:
            if isinstance(key_size_or_key, (bytes, str)):
                key_size = len(key_size_or_key) * 8
                key = key_size_or_key
            else:
                key_size = key_size_or_key
                key = None
            return cls._Camellia_KEY(key_size, key)
        raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")

    def __str__(self):
        return "Camellia"

    def __repr__(self):
        return str(self)


class _IDEA:
    _IDEA_KEY = None

    @classmethod
    def key(cls, key: _Optional[bytes | str] = None) -> _IDEA_KEY:
        if cls._IDEA_KEY is not None:
            return cls._IDEA_KEY(key)
        raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")

    def __str__(self):
        return "IDEA"

    def __repr__(self):
        return str(self)


class _SEED:
    _SEED_KEY = None

    @classmethod
    def key(cls, key: _Optional[bytes | str] = None) -> _SEED_KEY:
        if cls._SEED_KEY is not None:
            return cls._SEED_KEY(key)
        raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")

    def __str__(self):
        return "SEED"

    def __repr__(self):
        return str(self)


class _SM4:
    _SM4_KEY = None

    @classmethod
    def key(cls, key: _Optional[bytes | str] = None) -> _SM4_KEY:
        if cls._SM4_KEY is not None:
            return cls._SM4_KEY(key)
        raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")

    def __str__(self):
        return "SM4"

    def __repr__(self):
        return str(self)


class _DES:
    _DES_KEY = None

    @classmethod
    def key(cls, key: _Optional[bytes | str] = None) -> _DES_KEY:
        if cls._DES_KEY is not None:
            if isinstance(key, (bytes, str)):
                if len(key) * 8 != 64:
                    raise ValueError("DES key size must be 64 bits")
            return cls._DES_KEY(key)
        raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")

    def __str__(self):
        return "DES"

    def __repr__(self):
        return str(self)


class _ARC2:
    _ARC2_KEY = None

    @classmethod
    def key(cls, key_size_or_key: _Literal[40, 64, 128] | bytes | str) -> _ARC2_KEY:
        if cls._ARC2_KEY is not None:
            if isinstance(key_size_or_key, (bytes, str)):
                key_size = len(key_size_or_key) * 8
                key = key_size_or_key
                if key_size not in (40, 64, 128):
                    raise ValueError("ARC2 key size must be one of 40, 64, or 128 bits")
            else:
                key_size = key_size_or_key
                key = None
            return cls._ARC2_KEY(key_size, key)
        raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")

    def __str__(self):
        return "ARC2"

    def __repr__(self):
        return str(self)


class _Salsa20:
    _Salsa20_KEY = None

    @classmethod
    def key(cls, key_size_or_key: _Literal[128, 256] | bytes | str) -> _Salsa20_KEY:
        if cls._Salsa20_KEY is not None:
            if isinstance(key_size_or_key, (bytes, str)):
                key_size = len(key_size_or_key) * 8
                key = key_size_or_key
                if key_size not in (128, 256):
                    raise ValueError("Salsa20 key size must be one of 128 or 256 bits")
            else:
                key_size = key_size_or_key
                key = None
            return cls._Salsa20_KEY(key_size, key)
        raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")

    def __str__(self):
        return "Salsa20"

    def __repr__(self):
        return str(self)


class _SymCipher:
    """Symmetric Encryption"""
    AES = _AES
    ChaCha20 = _ChaCha20
    TripleDES = _TripleDES
    Blowfish = _Blowfish
    CAST5 = _CAST5
    ARC4 = _ARC4
    Camellia = _Camellia
    IDEA = _IDEA
    SEED = _SEED
    SM4 = _SM4
    DES = _DES
    ARC2 = _ARC2
    Salsa20 = _Salsa20


class _SymOperation(_EANEnum):
    """Different modes of operation"""
    ECB = "Electronic Codebook"
    CBC = "Cipher Block Chaining"
    CFB = "Cipher Feedback"
    OFB = "Output Feedback"
    CTR = "Counter"
    GCM = "Galois/Counter Mode"


class _SymPadding(_EANEnum):
    """Padding Schemes"""
    PKCS7 = ""
    ANSIX923 = ""


class _SymKeyEncoding(_EANEnum):
    HEX = ""
    RAW = ""
    ASCII = ""
    BASE16 = ""
    BASE32 = ""
    BASE64 = ""


class Sym:
    """Provides all enums for symmetric cryptography operations"""
    Cipher = _SymCipher
    Operation = _SymOperation
    Padding = _SymPadding
    KeyEncoding = _SymKeyEncoding


class _RSA:  # Rivest-Shamir-Adleman
    _RSA_KEYPAIR = None

    @classmethod
    def key(cls, key_size_or_private_key: _Literal[512, 768, 1024, 2048, 3072, 4096, 8192, 15360] | bytes | str) -> _RSA_KEYPAIR:
        """
        Generate an RSA key pair object.

        Parameters:
        key_size_or_private_key (Union[int, bytes, str, rsa.RSAPrivateKey]): The key size or an existing private key.

        Returns:
        _RSA_KEYPAIR: An object containing the key size and private key.
        """
        if isinstance(key_size_or_private_key, (str, bytes)):
            key_size = len(key_size_or_private_key) * 8
            private_key = key_size_or_private_key
        elif isinstance(key_size_or_private_key, int) and key_size_or_private_key in {512, 768, 1024, 2048, 3072, 4096, 8192, 15360}:
            key_size = key_size_or_private_key
            private_key = None
        else:
            raise ValueError("Invalid key size or private key provided.")

        return cls._RSA_KEYPAIR(key_size, private_key)

    def __str__(self):
        return "RSA"


class _DSA:
    _DSA_KEYPAIR = None

    @classmethod
    def key(cls, key_size_or_private_key: _Literal[1024, 2048, 3072] | bytes | str) -> _DSA_KEYPAIR:
        """
        Generate an DSA key pair object.

        Parameters:
        key_size_or_private_key (Union[int, bytes, str, dsa.DSAPrivateKey]): The key size or an existing private key.

        Returns:
        _DSA_KEYPAIR: An object containing the key size and private key.
        """
        if isinstance(key_size_or_private_key, (str, bytes)):
            key_size = len(key_size_or_private_key) * 8
            private_key = key_size_or_private_key
        elif isinstance(key_size_or_private_key, int) and key_size_or_private_key in {512, 768, 1024, 2048, 3072, 4096,
                                                                                      8192, 15360}:
            key_size = key_size_or_private_key
            private_key = None
        else:
            raise ValueError("Invalid key size or private key provided.")

        return cls._DSA_KEYPAIR(key_size, private_key)

    def __str__(self):
        return "DSA"


class _ECCCurve(_EANEnum):
    """Elliptic key functions"""
    SECP192R1 = ""
    SECP224R1 = ""
    SECP256K1 = ""
    SECP256R1 = ""  # Default
    SECP384R1 = ""
    SECP521R1 = ""
    SECT163K1 = ""
    SECT163R2 = ""
    SECT233K1 = ""
    SECT233R1 = ""
    SECT283K1 = ""
    SECT283R1 = ""
    SECT409K1 = ""
    SECT409R1 = ""
    SECT571K1 = ""
    SECT571R1 = ""


class _ECCType(_EANEnum):
    """How the signing is done, heavily affects the performance, key generation and what you can do with it"""
    ECDSA = "Elliptic Curve Digital Signature Algorithm"
    Ed25519 = ""
    Ed448 = ""
    X25519 = ""
    X448 = ""


class _ECC:
    """Elliptic Curve Cryptography"""
    _ECC_KEYPAIR = None
    Curve = _ECCCurve
    Type = _ECCType

    @classmethod
    def ecdsa_key(cls, ecc_curve: _ECCCurve = _ECCCurve.SECP256R1,
                  private_key: _Optional[bytes | str] = None):
        """Elliptic Curve Digital Signature Algorithm"""
        return cls._ECC_KEYPAIR(_ECCType.ECDSA, ecc_curve, private_key)

    @classmethod
    def optimized_key(cls, ecc_type: _ECCType,
                      private_key: _Optional[bytes | str] = None):
        if ecc_type == _ECCType.ECDSA:
            raise ValueError("Please use ECC.ecdsa_key to generate ECDSA keys")
        return cls._ECC_KEYPAIR(ecc_type, None, private_key)

    def __str__(self):
        return "ECC"


class _KYBER:
    _KYBER_KEYPAIR = None

    @classmethod
    def key(cls):
        return cls._KYBER_KEYPAIR()

    def __str__(self):
        return "KYBER"


class _DILITHIUM:
    _DILITHIUM_KEYPAIR = None

    @classmethod
    def key(cls):
        return cls._DILITHIUM_KEYPAIR()

    def __str__(self):
        return "DILITHIUM"


class _ASymCipher:
    """Asymmetric Encryption"""
    RSA = _RSA
    DSA = _DSA  # Digital Signature Algorithm
    ECC = _ECC
    KYBER = _KYBER
    DILITHIUM = _DILITHIUM


class _ASymPadding(_EANEnum):
    """Asymmetric Encryption Padding Schemes"""
    PKCShash1v15 = ""
    OAEP = ""
    PSS = ""


class _ASymKeyEncoding(_EANEnum):
    PEM = ""
    PKCS8 = ""
    ASN1_DER = ""
    OPENSSH = ""


class ASym:
    """Provides all enums for asymmetric cryptography operations"""
    Cipher = _ASymCipher
    Padding = _ASymPadding
    KeyEncoding = _ASymKeyEncoding


class KeyDerivationFunction(_EANEnum):
    """Key Derivation Functions (KDFs)"""
    PBKDF2HMAC = "Password-Based Key Derivation Function 2"
    Scrypt = ""
    HKDF = "HMAC-based Extract-and-Expand Key Derivation Function"
    X963 = ""
    ConcatKDF = ""
    PBKDF1 = ""
    KMAC128 = ""
    KMAC256 = ""
    ARGON2 = ""
    KKDF = ""
    BCRYPT = ""


class MessageAuthenticationCode(_EANEnum):
    """Authentication Codes"""
    HMAC = "Hash-based Message Authentication Code"
    CMAC = "Cipher-based Message Authentication Code"
    KMAC128 = ""
    KMAC256 = ""
    Poly1305 = ""
