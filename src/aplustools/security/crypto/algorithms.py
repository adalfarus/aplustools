from cryptography.hazmat.primitives.asymmetric import rsa, dsa, ec, padding as asym_padding
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives.ciphers import modes

from .keys import _AES_KEY, _RSA_KEYPAIR, _DSA_KEYPAIR, _ECC_KEYPAIR, ECC_TYPE, ECC_CURVE, _KYBER_KEYPAIR
from typing import Literal, Optional

from aplustools.data import enum_auto


class _AES:  # Advanced Encryption Standard
    @staticmethod
    def key(key_size_or_key: Literal[128, 192, 256] | bytes | str) -> _AES_KEY:
        if isinstance(key_size_or_key, (bytes, str)):
            key_size = len(key_size_or_key) * 8
            key = key_size_or_key
        else:
            key_size = key_size_or_key
            key = None
        return _AES_KEY(key_size, key)


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


class SymPadding:
    """Padding Schemes"""
    PKCS7 = sym_padding.PKCS7
    ANSIX923 = sym_padding.ANSIX923


class _RSA:  # Rivest-Shamir-Adleman
    @staticmethod
    def key(key_size_or_private_key: Literal[512, 768, 1024, 2048, 3072, 4096, 8192, 15360] | bytes | str | rsa.RSAPrivateKey) -> _RSA_KEYPAIR:
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
        elif isinstance(key_size_or_private_key, rsa.RSAPrivateKey):
            key_size = key_size_or_private_key.key_size
            private_key = key_size_or_private_key
        elif isinstance(key_size_or_private_key, int) and key_size_or_private_key in {512, 768, 1024, 2048, 3072, 4096, 8192, 15360}:
            key_size = key_size_or_private_key
            private_key = None
        else:
            raise ValueError("Invalid key size or private key provided.")

        return _RSA_KEYPAIR(key_size, private_key)


class _DSA:
    @staticmethod
    def key(key_size_or_private_key: Literal[1024, 2048, 3072] | bytes | str | dsa.DSAPrivateKey) -> _DSA_KEYPAIR:
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
        elif isinstance(key_size_or_private_key, dsa.DSAPrivateKey):
            key_size = key_size_or_private_key.key_size
            private_key = key_size_or_private_key
        elif isinstance(key_size_or_private_key, int) and key_size_or_private_key in {512, 768, 1024, 2048, 3072, 4096,
                                                                                      8192, 15360}:
            key_size = key_size_or_private_key
            private_key = None
        else:
            raise ValueError("Invalid key size or private key provided.")

        return _DSA_KEYPAIR(key_size, private_key)


class _ECC:
    """Elliptic Curve Cryptography"""
    @staticmethod
    def ecdsa_key(ecc_curve: ec.SECP192R1 | ec.SECP224R1 | ec.SECP256K1 | ec.SECP256R1 | ec.SECP384R1 | ec.SECP521R1 |
                             ec.SECT163K1 | ec.SECT163R2 | ec.SECT233K1 | ec.SECT233R1 | ec.SECT283K1 | ec.SECT283R1 |
                             ec.SECT409K1 | ec.SECT409R1 | ec.SECT571K1 | ec.SECT571R1 = ECC_CURVE.SECP256R1,
                  private_key: Optional[bytes | str] = None):
        """Elliptic Curve Digital Signature Algorithm"""
        return _ECC_KEYPAIR(ECC_TYPE.ECDSA, ecc_curve, private_key)

    @staticmethod
    def optimized_key(ecc_type: ECC_TYPE.Ed25519 | ECC_TYPE.Ed448 | ECC_TYPE.X25519 | ECC_TYPE.X448 = ECC_TYPE.Ed25519,
                      private_key: Optional[bytes | str] = None):
        if ecc_type == ECC_TYPE.ECDSA:
            raise ValueError("Please use ECC.ecdsa_key to generate ECDSA keys")
        return _ECC_KEYPAIR(ecc_type, None, private_key)


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


# UNDER CONSTRUCTION
class DiffieHellmanAlgorithm:
    ECDH = enum_auto()  # Elliptic Curve Diffie-Hellman
    DH = enum_auto()
