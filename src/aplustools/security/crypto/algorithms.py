"""TBA"""
from .exceptions import NotSupportedError as _NotSupportedError
from ._hashes import HashAlgorithm  # To export this value
from .. import GenericLabeledEnum as _GenericLabeledEnum

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts


class _BASIC_KEYTYPE(_ty.Protocol):
    # def __int__(self, key: bytes, original_key: str) -> None: ...
    def get_key(self) -> bytes: ...
    def get_original_key(self) -> str: ...
    def __bytes__(self) -> bytes: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...


class _BASIC_KEYPAIRTYPE(_ty.Protocol):
    # def __init__(self, private_key: _ty.Any, public_key: _ty.Any) -> None: ...
    def get_private_key(self) -> _ty.Any: ...
    def get_public_key(self) -> _ty.Any: ...
    def get_private_bytes(self) -> bytes: ...
    def get_public_bytes(self) -> bytes: ...
    def __bytes__(self) -> bytes: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...


_AES_KEYSIZES = (128, 192, 256)
_AES_KEYLITERAL = _ty.Literal[128, 192, 256]
class _AES_KEYTYPE(_BASIC_KEYTYPE):
    def __init__(self, key_size: _AES_KEYLITERAL, key: _ty.Optional[bytes | str]) -> None: ...


class _AES:  # Advanced Encryption Standard
    _KEY: _ty.Type[_AES_KEYTYPE] | None = None

    @classmethod
    def key(cls, key_size_or_key: _AES_KEYLITERAL | bytes | tuple[_AES_KEYLITERAL, str]) -> _AES_KEYTYPE:
        """
        TBA

        :param key_size_or_key:
        :return:
        """
        if cls._KEY is None:
            raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")
        key: str | bytes | None = None
        key_size: _AES_KEYLITERAL

        if isinstance(key_size_or_key, bytes):
            size: int = len(key_size_or_key) * 8
            if size not in _AES_KEYSIZES:
                raise ValueError(f"Can't accept key of size '{size}' for the {cls()} cipher")
            key_size = _ty.cast(_AES_KEYLITERAL, size)
            key = key_size_or_key
        elif isinstance(key_size_or_key, int) and key_size_or_key in _AES_KEYSIZES:
            key_size = key_size_or_key
        elif isinstance(key_size_or_key, tuple) and len(key_size_or_key) == 2 and \
             isinstance((key_size := key_size_or_key[0]), int) and key_size in _AES_KEYSIZES and \
             isinstance((key := key_size_or_key[1]), str):
            key_size = _ty.cast(_AES_KEYLITERAL, key_size_or_key)
        else:
            raise ValueError(f"key_size_or_key needs to be of type '{_AES_KEYLITERAL} | bytes | tuple[{_AES_KEYLITERAL}, str]', and not '{repr(key_size_or_key)}'")
        return cls._KEY(key_size, key)

    def __str__(self) -> str:
        return "AES"


class _ChaCha20_KEYTYPE(_BASIC_KEYTYPE):
    def __init__(self, key: _ty.Optional[bytes | str] = None) -> None: ...


class _ChaCha20:  # Advanced Encryption Standard
    _KEY: _ty.Type[_ChaCha20_KEYTYPE] | None = None

    @classmethod
    def key(cls, key: bytes | str | None = None) -> _ChaCha20_KEYTYPE:
        """
        TBA

        :param key:
        :return:
        """
        if cls._KEY is None:
            raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")
        if not (isinstance(key, (bytes, str)) or key is None):
            raise ValueError(f"key needs to be of type 'bytes | str | None', and not '{repr(key)}'")
        return cls._KEY(key)

    def __str__(self) -> str:
        return "ChaCha20"


class _TripleDES_KEYTYPE(_BASIC_KEYTYPE):
    def __init__(self, key_size: _ty.Literal[192], key: _ty.Optional[bytes | str] = None) -> None: ...


class _TripleDES:  # Advanced Encryption Standard
    _KEY: _ty.Type[_TripleDES_KEYTYPE] | None = None

    @classmethod
    def key(cls, key: bytes | str | None = None) -> _TripleDES_KEYTYPE:
        """
        TBA

        :param key:
        :return:
        """
        if cls._KEY is None:
            raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")
        if not (isinstance(key, (bytes, str)) or key is None):
            raise ValueError(f"key needs to be of type 'bytes | str | None', and not '{repr(key)}'")
        return cls._KEY(192, key)

    def __str__(self) -> str:
        return "TripleDES"


_Blowfish_KEYSIZES = (128, 256)
_Blowfish_KEYLITERAL = _ty.Literal[128, 256]
class _Blowfish_KEYTYPE(_BASIC_KEYTYPE):
    def __init__(self, key_size: _ty.Literal[128, 256], key: _ty.Optional[bytes | str] = None) -> None: ...


class _Blowfish:  # Advanced Encryption Standard
    _KEY: _ty.Type[_Blowfish_KEYTYPE] | None = None

    @classmethod
    def key(cls, key_size_or_key: _Blowfish_KEYLITERAL | bytes | tuple[_Blowfish_KEYLITERAL, str]) -> _Blowfish_KEYTYPE:
        """
        TBA

        :param key_size_or_key:
        :return:
        """
        if cls._KEY is None:
            raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")
        key: str | bytes | None = None
        key_size: _Blowfish_KEYLITERAL

        if isinstance(key_size_or_key, bytes):
            size: int = len(key_size_or_key) * 8
            if size not in _Blowfish_KEYSIZES:
                raise ValueError(f"Can't accept key of size '{size}' for the {cls()} cipher")
            key_size = _ty.cast(_Blowfish_KEYLITERAL, size)
            key = key_size_or_key
        elif isinstance(key_size_or_key, int) and key_size_or_key in _Blowfish_KEYSIZES:
            key_size = key_size_or_key
        elif isinstance(key_size_or_key, tuple) and len(key_size_or_key) == 2 and \
             isinstance((key_size := key_size_or_key[0]), int) and key_size in _Blowfish_KEYSIZES and \
             isinstance((key := key_size_or_key[1]), str):
            key_size = _ty.cast(_Blowfish_KEYLITERAL, key_size_or_key)
        else:
            raise ValueError(f"key_size_or_key needs to be of type '{_Blowfish_KEYLITERAL} | bytes | tuple[{_Blowfish_KEYLITERAL}, str]', and not '{repr(key_size_or_key)}'")
        return cls._KEY(key_size, key)

    def __str__(self) -> str:
        return "Blowfish"


_CAST5_KEYSIZES = (40, 128)
_CAST5_KEYLITERAL = _ty.Literal[40, 128]
class _CAST5_KEYTYPE(_BASIC_KEYTYPE):
    def __init__(self, key_size: _ty.Literal[40, 128], key: _ty.Optional[bytes | str] = None) -> None: ...


class _CAST5:  # Advanced Encryption Standard
    _KEY: _ty.Type[_CAST5_KEYTYPE] | None = None

    @classmethod
    def key(cls, key_size_or_key: _CAST5_KEYLITERAL | bytes | tuple[_CAST5_KEYLITERAL, str]) -> _CAST5_KEYTYPE:
        """
        TBA

        :param key_size_or_key:
        :return:
        """
        if cls._KEY is None:
            raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")
        key: str | bytes | None = None
        key_size: _CAST5_KEYLITERAL

        if isinstance(key_size_or_key, bytes):
            size: int = len(key_size_or_key) * 8
            if size not in _CAST5_KEYSIZES:
                raise ValueError(f"Can't accept key of size '{size}' for the {cls()} cipher")
            key_size = _ty.cast(_CAST5_KEYLITERAL, size)
            key = key_size_or_key
        elif isinstance(key_size_or_key, int) and key_size_or_key in _CAST5_KEYSIZES:
            key_size = key_size_or_key
        elif isinstance(key_size_or_key, tuple) and len(key_size_or_key) == 2 and \
             isinstance((key_size := key_size_or_key[0]), int) and key_size in _CAST5_KEYSIZES and \
             isinstance((key := key_size_or_key[1]), str):
            key_size = _ty.cast(_CAST5_KEYLITERAL, key_size_or_key)
        else:
            raise ValueError(f"key_size_or_key needs to be of type '{_CAST5_KEYLITERAL} | bytes | tuple[{_CAST5_KEYLITERAL}, str]', and not '{repr(key_size_or_key)}'")
        return cls._KEY(key_size, key)

    def __str__(self) -> str:
        return "CAST5"


class _ARC4_KEYTYPE(_BASIC_KEYTYPE):
    def __init__(self, key: _ty.Optional[bytes | str] = None) -> None: ...


class _ARC4:
    _KEY: _ty.Type[_ARC4_KEYTYPE] | None = None

    @classmethod
    def key(cls, key: bytes | str | None = None) -> _ARC4_KEYTYPE:
        """
        TBA

        :param key:
        :return:
        """
        if cls._KEY is None:
            raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")
        if not (isinstance(key, (bytes, str)) or key is None):
            raise ValueError(f"key needs to be of type 'bytes | str | None', and not '{repr(key)}'")
        return cls._KEY(key)

    def __str__(self) -> str:
        return "ARC4"


_Camellia_KEYSIZES = (128, 192, 256)
_Camellia_KEYLITERAL = _ty.Literal[128, 192, 256]
class _Camellia_KEYTYPE(_BASIC_KEYTYPE):
    def __init__(self, key_size: _Camellia_KEYLITERAL, key: _ty.Optional[bytes | str] = None) -> None: ...


class _Camellia:
    _KEY: _ty.Type[_Camellia_KEYTYPE] | None = None

    @classmethod
    def key(cls, key_size_or_key: _Camellia_KEYLITERAL | bytes | tuple[_Camellia_KEYLITERAL, str]) -> _Camellia_KEYTYPE:
        """
        TBA

        :param key_size_or_key:
        :return:
        """
        if cls._KEY is None:
            raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")
        key: str | bytes | None = None
        key_size: _Camellia_KEYLITERAL

        if isinstance(key_size_or_key, bytes):
            size: int = len(key_size_or_key) * 8
            if size not in _Camellia_KEYSIZES:
                raise ValueError(f"Can't accept key of size '{size}' for the {cls()} cipher")
            key_size = _ty.cast(_Camellia_KEYLITERAL, size)
            key = key_size_or_key
        elif isinstance(key_size_or_key, int) and key_size_or_key in _Camellia_KEYSIZES:
            key_size = key_size_or_key
        elif isinstance(key_size_or_key, tuple) and len(key_size_or_key) == 2 and \
             isinstance((key_size := key_size_or_key[0]), int) and key_size in _Camellia_KEYSIZES and \
             isinstance((key := key_size_or_key[1]), str):
            key_size = _ty.cast(_Camellia_KEYLITERAL, key_size_or_key)
        else:
            raise ValueError(f"key_size_or_key needs to be of type '{_Camellia_KEYLITERAL} | bytes | tuple[{_Camellia_KEYLITERAL}, str]', and not '{repr(key_size_or_key)}'")
        return cls._KEY(key_size, key)

    def __str__(self) -> str:
        return "Camellia"


class _IDEA_KEYTYPE(_BASIC_KEYTYPE):
    def __init__(self, key: _ty.Optional[bytes | str] = None) -> None: ...


class _IDEA:
    _KEY: _ty.Type[_IDEA_KEYTYPE] | None = None

    @classmethod
    def key(cls, key: bytes | str | None = None) -> _IDEA_KEYTYPE:
        """
        TBA

        :param key:
        :return:
        """
        if cls._KEY is None:
            raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")
        if not (isinstance(key, (bytes, str)) or key is None):
            raise ValueError(f"key needs to be of type 'bytes | str | None', and not '{repr(key)}'")
        return cls._KEY(key)

    def __str__(self) -> str:
        return "IDEA"


class _SEED_KEYTYPE(_BASIC_KEYTYPE):
    def __init__(self, key: _ty.Optional[bytes | str] = None) -> None: ...


class _SEED:
    _KEY: _ty.Type[_SEED_KEYTYPE] | None = None

    @classmethod
    def key(cls, key: bytes | str | None = None) -> _SEED_KEYTYPE:
        """
        TBA

        :param key:
        :return:
        """
        if cls._KEY is None:
            raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")
        if not (isinstance(key, (bytes, str)) or key is None):
            raise ValueError(f"key needs to be of type 'bytes | str | None', and not '{repr(key)}'")
        return cls._KEY(key)

    def __str__(self) -> str:
        return "SEED"


class _SM4_KEYTYPE(_BASIC_KEYTYPE):
    def __init__(self, key: _ty.Optional[bytes | str] = None): ...


class _SM4:
    _KEY: _ty.Type[_SM4_KEYTYPE] | None = None

    @classmethod
    def key(cls, key: bytes | str | None = None) -> _SM4_KEYTYPE:
        """
        TBA

        :param key:
        :return:
        """
        if cls._KEY is None:
            raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")
        if not (isinstance(key, (bytes, str)) or key is None):
            raise ValueError(f"key needs to be of type 'bytes | str | None', and not '{repr(key)}'")
        return cls._KEY(key)

    def __str__(self) -> str:
        return "SM4"


class _DES_KEYTYPE(_BASIC_KEYTYPE):
    def __init__(self, key: _ty.Optional[bytes | str] = None) -> None: ...


class _DES:
    _KEY: _ty.Type[_DES_KEYTYPE] | None = None

    @classmethod
    def key(cls, key: bytes | str | None = None) -> _DES_KEYTYPE:
        """
        TBA

        :param key:
        :return:
        """
        if cls._KEY is None:
            raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")
        if isinstance(key, (bytes, str)):
            if len(key) * 8 != 64:
                raise ValueError(f"Can't accept key of size '{len(key) * 8}' for the {cls()} cipher, please use a 64-bit long one")
        elif key is not None:
            raise ValueError(f"key needs to be of type 'bytes | str | None', and not '{repr(key)}'")
        return cls._KEY(key)

    def __str__(self) -> str:
        return "DES"


_ARC2_KEYSIZES = (40, 64, 128)
_ARC2_KEYLITERAL = _ty.Literal[40, 64, 128]
class _ARC2_KEYTYPE(_BASIC_KEYTYPE):
    def __init__(self, key_size: _ARC2_KEYLITERAL = 128, key: _ty.Optional[bytes | str] = None) -> None: ...


class _ARC2:
    _KEY: _ty.Type[_ARC2_KEYTYPE] | None = None

    @classmethod
    def key(cls, key_size_or_key: _ARC2_KEYLITERAL | bytes | tuple[_ARC2_KEYLITERAL, str]) -> _ARC2_KEYTYPE:
        """
        TBA

        :param key_size_or_key:
        :return:
        """
        if cls._KEY is None:
            raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")
        key: str | bytes | None = None
        key_size: _ARC2_KEYLITERAL

        if isinstance(key_size_or_key, bytes):
            size: int = len(key_size_or_key) * 8
            if size not in _ARC2_KEYSIZES:
                raise ValueError(f"Can't accept key of size '{size}' for the {cls()} cipher")
            key_size = _ty.cast(_ARC2_KEYLITERAL, size)
            key = key_size_or_key
        elif isinstance(key_size_or_key, int) and key_size_or_key in _ARC2_KEYSIZES:
            key_size = key_size_or_key
        elif isinstance(key_size_or_key, tuple) and len(key_size_or_key) == 2 and \
             isinstance((key_size := key_size_or_key[0]), int) and key_size in _ARC2_KEYSIZES and \
             isinstance((key := key_size_or_key[1]), str):
            key_size = _ty.cast(_ARC2_KEYLITERAL, key_size_or_key)
        else:
            raise ValueError(f"key_size_or_key needs to be of type '{_ARC2_KEYLITERAL} | bytes | tuple[{_ARC2_KEYLITERAL}, str]', and not '{repr(key_size_or_key)}'")

        return cls._KEY(key_size, key)

    def __str__(self) -> str:
        return "ARC2"


_Salsa20_KEYSIZES = (128, 256)
_Salsa20_KEYLITERAL = _ty.Literal[128, 256]
class _Salsa20_KEYTYPE(_BASIC_KEYTYPE):
    def __init__(self, key_size: _Salsa20_KEYLITERAL = 256, key: _ty.Optional[bytes | str] = None) -> None: ...


class _Salsa20:
    _KEY: _ty.Type[_Salsa20_KEYTYPE] | None = None

    @classmethod
    def key(cls, key_size_or_key: _Salsa20_KEYLITERAL | bytes | tuple[_Salsa20_KEYLITERAL, str]) -> _Salsa20_KEYTYPE:
        """
        TBA

        :param key_size_or_key:
        :return:
        """
        if cls._KEY is None:
            raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")
        key: str | bytes | None = None
        key_size: _Salsa20_KEYLITERAL

        if isinstance(key_size_or_key, bytes):
            size: int = len(key_size_or_key) * 8
            if size not in _Salsa20_KEYSIZES:
                raise ValueError(f"Can't accept key of size '{size}' for the {cls()} cipher")
            key_size = _ty.cast(_Salsa20_KEYLITERAL, size)
            key = key_size_or_key
        elif isinstance(key_size_or_key, int) and key_size_or_key in _Salsa20_KEYSIZES:
            key_size = key_size_or_key
        elif isinstance(key_size_or_key, tuple) and len(key_size_or_key) == 2 and \
             isinstance((key_size := key_size_or_key[0]), int) and key_size in _Salsa20_KEYSIZES and \
             isinstance((key := key_size_or_key[1]), str):
            key_size = _ty.cast(_Salsa20_KEYLITERAL, key_size_or_key)
        else:
            raise ValueError(f"key_size_or_key needs to be of type '{_Salsa20_KEYLITERAL} | bytes | tuple[{_Salsa20_KEYLITERAL}, str]', and not '{repr(key_size_or_key)}'")
        return cls._KEY(key_size, key)

    def __str__(self) -> str:
        return "Salsa20"


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


class _SymOperation(_GenericLabeledEnum):
    """Different modes of operation"""
    ECB = (None, "Electronic Codebook")
    CBC = (None, "Cipher Block Chaining")
    CFB = (None, "Cipher Feedback")
    OFB = (None, "Output Feedback")
    CTR = (None, "Counter")
    GCM = (None, "Galois/Counter Mode")


class _SymPadding(_GenericLabeledEnum):
    """Padding Schemes"""
    PKCS7 = (None, "")
    ANSIX923 = (None, "")


class _SymKeyEncoding(_GenericLabeledEnum):
    HEX = (None, "")
    RAW = (None, "")
    ASCII = (None, "")
    BASE16 = (None, "")
    BASE32 = (None, "")
    BASE64 = (None, "")


class Sym:
    """Provides all enums for symmetric cryptography operations"""
    Cipher = _SymCipher
    Operation = _SymOperation
    Padding = _SymPadding
    KeyEncoding = _SymKeyEncoding


_RSA_KEYSIZES = (512, 768, 1024, 2048, 3072, 4096, 8192, 15360)
_RSA_KEYLITERAL = _ty.Literal[512, 768, 1024, 2048, 3072, 4096, 8192, 15360]
class _RSA_KEYPAIRTYPE(_BASIC_KEYPAIRTYPE):
    """You need to give a pem private key if it's in bytes"""
    def __init__(self, key_size: _RSA_KEYLITERAL, private_key: _ty.Optional[bytes | str] = None) -> None: ...


class _RSA:  # Rivest-Shamir-Adleman
    _KEYPAIR: _ty.Type[_RSA_KEYPAIRTYPE] | None = None

    @classmethod
    def key(cls, key_size_or_private_key: _RSA_KEYLITERAL | bytes | tuple[_RSA_KEYLITERAL, str]) -> _RSA_KEYPAIRTYPE:
        """
        Generate an RSA key pair object.

        Parameters:
        key_size_or_private_key (Union[int, bytes, str, rsa.RSAPrivateKey]): The key size or an existing private key.

        Returns:
        _RSA_KEYPAIR: An object containing the key size and private key.
        """
        if cls._KEYPAIR is None:
            raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")
        private_key: str | bytes | None = None
        key_size: _RSA_KEYLITERAL

        if isinstance(key_size_or_private_key, bytes):
            size: int = len(key_size_or_private_key) * 8
            if size not in _RSA_KEYSIZES:
                raise ValueError(f"Can't accept key of size '{size}' for the {cls()} cipher")
            key_size = _ty.cast(_RSA_KEYLITERAL, size)
            private_key = key_size_or_private_key
        elif isinstance(key_size_or_private_key, int) and key_size_or_private_key in _RSA_KEYSIZES:
            key_size = key_size_or_private_key
        elif isinstance(key_size_or_private_key, tuple) and len(key_size_or_private_key) == 2 and \
             isinstance((key_size := key_size_or_private_key[0]), int) and key_size in _RSA_KEYSIZES and \
             isinstance((private_key := key_size_or_private_key[1]), str):
            key_size = _ty.cast(_RSA_KEYLITERAL, key_size_or_private_key)
        else:
            raise ValueError(f"key_size_or_private_key needs to be of type '{_RSA_KEYLITERAL} | bytes | tuple[{_RSA_KEYLITERAL}, str]', and not '{repr(key_size_or_private_key)}'")

        return cls._KEYPAIR(key_size, private_key)

    def __str__(self) -> str:
        return "RSA"


_DSA_KEYSIZES = (1024, 2048, 3072)
_DSA_KEYLITERAL = _ty.Literal[1024, 2048, 3072]
class _DSA_KEYPAIRTYPE(_BASIC_KEYPAIRTYPE):
    def __init__(self, key_size: _DSA_KEYLITERAL, private_key: _ty.Optional[bytes | str] = None) -> None: ...


class _DSA:
    _KEYPAIR: _ty.Type[_DSA_KEYPAIRTYPE] | None = None

    @classmethod
    def key(cls, key_size_or_private_key: _DSA_KEYLITERAL | bytes | tuple[_DSA_KEYLITERAL, str]) -> _DSA_KEYPAIRTYPE:
        """
        Generate an DSA key pair object.

        Parameters:
        key_size_or_private_key (Union[int, bytes, str, dsa.DSAPrivateKey]): The key size or an existing private key.

        Returns:
        _DSA_KEYPAIR: An object containing the key size and private key.
        """
        if cls._KEYPAIR is None:
            raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")
        private_key: str | bytes | None = None
        key_size: _DSA_KEYLITERAL

        if isinstance(key_size_or_private_key, bytes):
            size: int = len(key_size_or_private_key) * 8
            if size not in _DSA_KEYSIZES:
                raise ValueError(f"Can't accept key of size '{size}' for the {cls()} cipher")
            key_size = _ty.cast(_DSA_KEYLITERAL, size)
            private_key = key_size_or_private_key
        elif isinstance(key_size_or_private_key, int) and key_size_or_private_key in _DSA_KEYSIZES:
            key_size = key_size_or_private_key
        elif isinstance(key_size_or_private_key, tuple) and len(key_size_or_private_key) == 2 and \
             isinstance((key_size := key_size_or_private_key[0]), int) and key_size in _RSA_KEYSIZES and \
             isinstance((private_key := key_size_or_private_key[1]), str):
            key_size = _ty.cast(_DSA_KEYLITERAL, key_size_or_private_key)
        else:
            raise ValueError(f"key_size_or_private_key needs to be of type '{_DSA_KEYLITERAL} | bytes | tuple[{_DSA_KEYLITERAL}, str]', and not '{repr(key_size_or_private_key)}'")

        return cls._KEYPAIR(key_size, private_key)

    def __str__(self) -> str:
        return "DSA"


class _ECCCurve(_GenericLabeledEnum):
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


class _ECCType(_GenericLabeledEnum):
    """How the signing is done, heavily affects the performance, key generation and what you can do with it"""
    ECDSA = (None, "Elliptic Curve Digital Signature Algorithm")
    Ed25519 = (None, "")
    Ed448 = (None, "")
    X25519 = (None, "")
    X448 = (None, "")


class _ECC_KEYPAIRTYPE(_BASIC_KEYPAIRTYPE):
    def __init__(self, ecc_type: _ECCType = _ECCType.ECDSA, ecc_curve: _ECCCurve | None = _ECCCurve.SECP256R1,
                 private_key: _ty.Optional[bytes | str] = None) -> None: ...


class _ECC:
    """Elliptic Curve Cryptography"""
    _KEYPAIR: _ty.Type[_ECC_KEYPAIRTYPE] | None = None
    Curve = _ECCCurve
    Type = _ECCType

    @classmethod
    def ecdsa_key(cls, ecc_curve: _ECCCurve = _ECCCurve.SECP256R1,
                  private_key: bytes | str | None = None) -> _ECC_KEYPAIRTYPE:
        """Elliptic Curve Digital Signature Algorithm"""
        if cls._KEYPAIR is None:
            raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")
        elif not isinstance(ecc_curve, _ECCCurve):
            raise ValueError(f"ecc_curve needs to be of type 'ECCCurve', and not '{repr(ecc_curve)}'")
        elif not (isinstance(private_key, (str, bytes)) or private_key is None):
            raise ValueError(f"private_key needs to be of type 'bytes | str | None', and not '{repr(private_key)}'")
        return cls._KEYPAIR(_ECCType.ECDSA, ecc_curve, private_key)

    @classmethod
    def optimized_key(cls, ecc_type: _ECCType,
                      private_key: bytes | str | None = None) -> _ECC_KEYPAIRTYPE:
        """
        TBA

        :param ecc_type:
        :param private_key:
        :return:
        """
        if cls._KEYPAIR is None:
            raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")
        elif not isinstance(ecc_type, _ECCType):
            raise ValueError(f"ecc_type needs to be of type 'ECCType', and not '{repr(ecc_type)}'")
        elif not (isinstance(private_key, (str, bytes)) or private_key is None):
            raise ValueError(f"private_key needs to be of type 'bytes | str | None', and not '{repr(private_key)}'")
        elif ecc_type == _ECCType.ECDSA:
            raise ValueError("Please use ECC.ecdsa_key to generate ECDSA keys")
        return cls._KEYPAIR(ecc_type, None, private_key)

    def __str__(self) -> str:
        return "ECC"


class _KYBER_KEYPAIRTYPE(_BASIC_KEYPAIRTYPE):
    def __init__(self) -> None: ...


class _KYBER:
    _KEYPAIR: _ty.Type[_KYBER_KEYPAIRTYPE] | None = None

    @classmethod
    def key(cls) -> _KYBER_KEYPAIRTYPE:
        """
        TBA

        :return:
        """
        if cls._KEYPAIR is None:
            raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")
        return cls._KEYPAIR()

    def __str__(self) -> str:
        return "KYBER"


class _DILITHIUM_KEYPAIRTYPE(_BASIC_KEYPAIRTYPE):
    def __init__(self) -> None: ...


class _DILITHIUM:
    _KEYPAIR: _ty.Type[_DILITHIUM_KEYPAIRTYPE] | None = None

    @classmethod
    def key(cls) -> _DILITHIUM_KEYPAIRTYPE:
        """
        TBA
        """
        if cls._KEYPAIR is None:
            raise _NotSupportedError(f"The {cls()} cipher is not supported by this backend")
        return cls._KEYPAIR()

    def __str__(self) -> str:
        return "DILITHIUM"


class _ASymCipher:
    """Asymmetric Encryption"""
    RSA = _RSA
    DSA = _DSA  # Digital Signature Algorithm
    ECC = _ECC
    KYBER = _KYBER
    DILITHIUM = _DILITHIUM


class _ASymPadding(_GenericLabeledEnum):
    """Asymmetric Encryption Padding Schemes"""
    PKCShash1v15 = (0, "")
    OAEP = (1, "")
    PSS = (2, "")


class _ASymKeyEncoding(_GenericLabeledEnum):
    PEM = (3, "")
    PKCS8 = (4, "")
    ASN1_DER = (5, "")
    OPENSSH = (6, "")


class ASym:
    """Provides all enums for asymmetric cryptography operations"""
    Cipher = _ASymCipher
    Padding = _ASymPadding
    KeyEncoding = _ASymKeyEncoding


class KeyDerivationFunction(_GenericLabeledEnum):
    """Key Derivation Functions (KDFs)"""
    PBKDF2HMAC = (None, "Password-Based Key Derivation Function 2")
    Scrypt = (None, "")
    HKDF = (None, "HMAC-based Extract-and-Expand Key Derivation Function")
    X963 = (None, "")
    ConcatKDF = (None, "")
    PBKDF1 = (None, "")
    KMAC128 = (None, "")
    KMAC256 = (None, "")
    ARGON2 = (None, "")
    KKDF = (None, "")
    BCRYPT = (None, "")


class MessageAuthenticationCode(_GenericLabeledEnum):
    """Authentication Codes"""
    HMAC = (None, "Hash-based Message Authentication Code")
    CMAC = (None, "Cipher-based Message Authentication Code")
    KMAC128 = (None, "")
    KMAC256 = (None, "")
    Poly1305 = (None, "")
