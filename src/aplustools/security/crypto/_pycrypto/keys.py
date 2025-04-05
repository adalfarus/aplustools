from Cryptodome.PublicKey import RSA, DSA, ECC
from Cryptodome.Cipher import AES, ChaCha20, DES3, Blowfish, CAST, PKCS1_OAEP, PKCS1_v1_5, ARC4, DES, ARC2, Salsa20
from Cryptodome.Hash import SHA256, SHA384, SHA512, HMAC, CMAC, SHA3_512, KMAC128, KMAC256, Poly1305, SHA3_224, SHA3_256, SHA3_384
from Cryptodome.Signature import pkcs1_15, DSS
from Cryptodome.Protocol.KDF import PBKDF2, scrypt, HKDF, PBKDF1
from Cryptodome.Signature.pss import PSS_SigScheme
from Cryptodome.Cipher.PKCS1_OAEP import PKCS1OAEP_Cipher
from Cryptodome.Random import get_random_bytes
from typing import Union, Literal, Optional
import os
import warnings
import secrets


from ..algorithms import Sym, ASym, _ECCCurve, KeyDerivationFunction, MessageAuthenticationCode, _ECCType
from .._keys import _BASIC_KEY, _BASIC_KEYPAIR
from ..backends import Backend
from ..exceptions import NotSupportedError

_ECC_TYPE_MAPPING = {
    _ECCType.ECDSA: 'ECDSA',
    _ECCType.Ed25519: 'Ed25519',
    _ECCType.Ed448: 'Ed448',
    _ECCType.X25519: 'X25519',
    _ECCType.X448: 'X448'
}
_ECC_CURVE_CONVERSION = {
    _ECCCurve.SECP192R1: 'P-192',
    _ECCCurve.SECP224R1: 'P-224',
    _ECCCurve.SECP256K1: 'secp256k1',
    _ECCCurve.SECP256R1: 'P-256',
    _ECCCurve.SECP384R1: 'P-384',
    _ECCCurve.SECP521R1: 'P-521'
}
_SYM_OPERATION_CONVERSION = {
    Sym.Operation.ECB: AES.MODE_ECB,
    Sym.Operation.CBC: AES.MODE_CBC,
    Sym.Operation.CFB: AES.MODE_CFB,
    Sym.Operation.OFB: AES.MODE_OFB,
    Sym.Operation.CTR: AES.MODE_CTR,
    Sym.Operation.GCM: AES.MODE_GCM,
}
_SYM_PADDING_CONVERSION = {
    Sym.Padding.PKCS7: lambda data: data + (16 - len(data) % 16) * bytes([16 - len(data) % 16]),
    Sym.Padding.ANSIX923: lambda data: data + bytes([0] * (16 - len(data) % 16 - 1)) + bytes([16 - len(data) % 16]),
}
_ASYM_PADDING_CONVERSION = {
    ASym.Padding.PKCShash1v15: pkcs1_15.new,
    ASym.Padding.OAEP: lambda hash_algo: PKCS1OAEP_Cipher.new(hashAlgo=hash_algo),
    ASym.Padding.PSS: lambda hash_algo: PSS_SigScheme(mgf=asym_padding.MGF1(hash_algo), salt_length=asym_padding.PSS.MAX_LENGTH)
}
_CIPHER_MODULE_MAPPING = {
    Sym.Cipher.AES: AES,
    Sym.Cipher.ChaCha20: ChaCha20,
    Sym.Cipher.ARC4: ARC4,
    Sym.Cipher.ARC2: ARC2,
    Sym.Cipher.CAST5: CAST,
    Sym.Cipher.TripleDES: DES3,
    Sym.Cipher.DES: DES,
    Sym.Cipher.Blowfish: Blowfish,
    Sym.Cipher.Salsa20: Salsa20
}


class _BASIC_PYCRYPTO_KEY(_BASIC_KEY):
    backend = Backend.pycryptodomex


class _BASIC_PYCRYPTO_KEYPAIR(_BASIC_KEYPAIR):
    backend = Backend.pycryptodomex

    def get_private_bytes(self) -> bytes:
        """Returns the private key in a byte format"""
        return self._private_key.export_key(format='PEM')

    def get_public_bytes(self) -> bytes:
        """Returns the public key in a byte format"""
        return self._public_key.export_key(format='PEM')


class _AES_KEY(_BASIC_PYCRYPTO_KEY):
    cipher = Sym.Cipher.AES

    def __init__(self, key_size: Literal[128, 192, 256], key: Optional[bytes | str] = None):
        _original_key = key if key is not None else secrets.token_bytes(key_size // 8)
        if isinstance(_original_key, bytes):
            if len(_original_key) * 8 != key_size:
                raise ValueError(f"Key size of given key ({len(_original_key) * 8}) doesn't match the specified key size ({key_size})")
            _key = _original_key
        else:
            _key = PBKDF2(_original_key, os.urandom(64), dkLen=32, count=800_000, hmac_hash_module=SHA3_512)
        super().__init__(_key, _original_key)


class _ChaCha20_KEY(_BASIC_PYCRYPTO_KEY):
    cipher = Sym.Cipher.ChaCha20

    def __init__(self, key: Optional[bytes | str] = None):
        _original_key = key if key is not None else secrets.token_bytes(32)
        if isinstance(_original_key, bytes):
            if len(_original_key) != 32:
                raise ValueError("Key size for ChaCha20 must be 256 bits")
            _key = _original_key
        else:
            _key = PBKDF2(_original_key, os.urandom(64), dkLen=32, count=800_000, hmac_hash_module=SHA3_512)
        super().__init__(_key, _original_key)


class _TripleDES_KEY(_BASIC_PYCRYPTO_KEY):
    cipher = Sym.Cipher.TripleDES

    def __init__(self, key_size: Literal[192] = 192, key: Optional[bytes | str] = None):
        _original_key = key if key is not None else secrets.token_bytes(24)
        if isinstance(_original_key, bytes):
            if len(_original_key) != 24:
                raise ValueError("Key size for TripleDES must be 192 bits (24 bytes)")
            _key = _original_key
        else:
            _key = PBKDF2(_original_key, os.urandom(64), dkLen=24, count=800_000, hmac_hash_module=SHA3_512)
        super().__init__(_key, _original_key)


class _Blowfish_KEY(_BASIC_PYCRYPTO_KEY):
    cipher = Sym.Cipher.Blowfish

    def __init__(self, key_size: Literal[128, 256], key: Optional[bytes | str] = None):
        _original_key = key if key is not None else secrets.token_bytes(key_size // 8)
        if isinstance(_original_key, bytes):
            if len(_original_key) * 8 != key_size:
                raise ValueError(f"Key size for Blowfish must be {key_size} bits")
            _key = _original_key
        else:
            _key = PBKDF2(_original_key, os.urandom(64), dkLen=key_size // 8, count=800_000, hmac_hash_module=SHA3_512)
        super().__init__(_key, _original_key)


class _CAST5_KEY(_BASIC_PYCRYPTO_KEY):
    cipher = Sym.Cipher.CAST5

    def __init__(self, key_size: Literal[40, 128], key: Optional[bytes | str] = None):
        _original_key = key if key is not None else secrets.token_bytes(key_size // 8)
        if isinstance(_original_key, bytes):
            if len(_original_key) * 8 != key_size:
                raise ValueError(f"Key size for CAST5 must be {key_size} bits")
            _key = _original_key
        else:
            _key = PBKDF2(_original_key, os.urandom(64), dkLen=key_size // 8, count=800_000, hmac_hash_module=SHA3_512)
        super().__init__(_key, _original_key)


class _ARC4_KEY(_BASIC_PYCRYPTO_KEY):
    cipher = Sym.Cipher.ARC4

    def __init__(self, key: Optional[bytes | str] = None):
        _original_key = key if key is not None else secrets.token_bytes(16)
        if isinstance(_original_key, bytes):
            if len(_original_key) != 16:
                raise ValueError("Key size for ARC4 must be 128 bits (16 bytes)")
            _key = _original_key
        else:
            _key = PBKDF2(_original_key, os.urandom(64), dkLen=16, count=800_000, hmac_hash_module=SHA3_512)
        super().__init__(_key, _original_key)


class _DES_KEY(_BASIC_PYCRYPTO_KEY):
    cipher = Sym.Cipher.DES

    def __init__(self, key: Optional[bytes | str] = None):
        _original_key = key if key is not None else secrets.token_bytes(8)
        if isinstance(_original_key, bytes):
            if len(_original_key) != 8:
                raise ValueError("Key size for DES must be 64 bits (8 bytes)")
            _key = _original_key
        else:
            _key = PBKDF2(_original_key, os.urandom(64), dkLen=8, count=800_000, hmac_hash_module=SHA3_512)
        super().__init__(_key, _original_key)


class _ARC2_KEY(_BASIC_PYCRYPTO_KEY):
    cipher = Sym.Cipher.ARC2

    def __init__(self, key_size: Literal[40, 64, 128] = 128, key: Optional[bytes | str] = None):
        _original_key = key if key is not None else secrets.token_bytes(key_size // 8)
        if isinstance(_original_key, bytes):
            if len(_original_key) * 8 != key_size:
                raise ValueError(f"Key size for ARC2 must be {key_size} bits")
            _key = _original_key
        else:
            _key = PBKDF2(_original_key, os.urandom(64), dkLen=key_size // 8, count=800_000, hmac_hash_module=SHA3_512)
        super().__init__(_key, _original_key)


class _Salsa20_KEY(_BASIC_PYCRYPTO_KEY):
    cipher = Sym.Cipher.Salsa20

    def __init__(self, key_size: Literal[128, 256] = 256, key: Optional[bytes | str] = None):
        _original_key = key if key is not None else secrets.token_bytes(key_size // 8)
        if isinstance(_original_key, bytes):
            if len(_original_key) * 8 != key_size:
                raise ValueError(f"Key size for Salsa20 must be {key_size} bits")
            _key = _original_key
        else:
            _key = PBKDF2(_original_key, os.urandom(64), dkLen=key_size // 8, count=800_000, hmac_hash_module=SHA3_512)
        super().__init__(_key, _original_key)


_Camellia_KEY = _IDEA_KEY = _SEED_KEY = _SM4_KEY = None


class _RSA_KEYPAIR(_BASIC_PYCRYPTO_KEYPAIR):
    cipher = ASym.Cipher.RSA

    def __init__(self, key_size: Literal[2048, 3072, 4096] = 2048, private_key: Optional[bytes | str | RSA.RsaKey] = None):
        _private_key = RSA.import_key(private_key) if private_key else RSA.generate(key_size)
        _public_key = _private_key.publickey()
        super().__init__(_private_key, _public_key)


class _DSA_KEYPAIR(_BASIC_PYCRYPTO_KEYPAIR):
    cipher = ASym.Cipher.DSA

    def __init__(self, key_size: Literal[2048, 3072] = 2048, private_key: Optional[bytes | str | DSA.DsaKey] = None):
        _private_key = DSA.import_key(private_key) if private_key else DSA.generate(key_size)
        _public_key = _private_key.publickey()
        super().__init__(_private_key, _public_key)


class _ECC_KEYPAIR(_BASIC_PYCRYPTO_KEYPAIR):
    cipher = ASym.Cipher.ECC

    def __init__(self, ecc_type: int = 0, ecc_curve: Optional[int] = 3, private_key: Optional[bytes | str] = None):
        if private_key is None:
            ecc_type_str = _ECC_TYPE_MAPPING.get(ecc_type, None)
            if ecc_type_str is None:
                raise ValueError(f"Unsupported ECC type '{ecc_type}'")

            if ecc_type_str == 'ECDSA':
                ecc_curve_str = _ECC_CURVE_CONVERSION.get(ecc_curve, None)
                if ecc_curve_str is None:
                    raise NotSupportedError(f"Unsupported ECC curve '{ecc_curve}'")
                _private_key = ECC.generate(curve=ecc_curve_str)
            else:
                if ecc_curve is not None:
                    raise NotSupportedError("You can't use an ECC curve when you aren't using the ECC Type ECDSA. Please set it to None instead.")
                _private_key = ECC.generate(curve=ecc_type_str)
        else:
            _private_key = ECC.import_key(private_key)

        _public_key = _private_key.public_key()
        super().__init__(_private_key, _public_key)


def encrypt_sym(plain_bytes: bytes, cipher_key, padding=None, mode_id=None):
    parts = {}
    cipher_module = _CIPHER_MODULE_MAPPING[cipher_key.cipher]

    if cipher_key.cipher in [Sym.Cipher.ChaCha20, Sym.Cipher.ARC4]:
        nonce = get_random_bytes(12)
        cipher = cipher_module.new(key=cipher_key.get_key(), nonce=nonce)
        parts['nonce'] = nonce
    if cipher_key.cipher in [Sym.Cipher.Salsa20]:
        nonce = get_random_bytes(8)
        cipher = cipher_module.new(key=cipher_key.get_key(), nonce=nonce)
        parts['nonce'] = nonce
    elif cipher_key.cipher == Sym.Cipher.ARC2:
        iv = get_random_bytes(8)
        cipher = cipher_module.new(cipher_key.get_key(), mode=ARC2.MODE_CFB, iv=iv)
        parts['iv'] = iv
    else:
        mode = _SYM_OPERATION_CONVERSION.get(mode_id)
        if mode is None:
            raise ValueError("Invalid mode")
        if mode == AES.MODE_ECB:
            cipher = cipher_module.new(cipher_key.get_key(), mode)
        elif mode in [AES.MODE_CBC, AES.MODE_CFB, AES.MODE_OFB]:
            iv_or_nonce = get_random_bytes(16)
            cipher = cipher_module.new(cipher_key.get_key(), mode, iv=iv_or_nonce)
            parts['iv'] = iv_or_nonce
        elif mode == AES.MODE_CTR:
            iv_or_nonce = get_random_bytes(8)
            cipher = cipher_module.new(cipher_key.get_key(), mode, nonce=iv_or_nonce)
            parts['nonce'] = iv_or_nonce
        elif mode == AES.MODE_GCM:
            iv_or_nonce = get_random_bytes(12)
            cipher = cipher_module.new(cipher_key.get_key(), mode, nonce=iv_or_nonce)
            parts['nonce'] = iv_or_nonce
        else:
            raise NotSupportedError(f"Unsupported mode '{mode_id}' for encryption")

        if padding and mode != AES.MODE_CTR:
            plain_bytes = _SYM_PADDING_CONVERSION[padding](plain_bytes)
        elif mode == AES.MODE_CBC and len(plain_bytes) % 16 != 0:
            raise ValueError("Data must be padded to 16 byte boundary in CBC mode")

    ciphertext = cipher.encrypt(plain_bytes)
    parts['ciphertext'] = ciphertext
    return parts


def decrypt_sym(ciphertext: Union[bytes, dict[str, bytes]], cipher_key, padding=None, mode_id=None) -> bytes:
    if isinstance(ciphertext, dict):
        ciphertext_bytes = ciphertext['ciphertext']
        iv_or_nonce = ciphertext.get('iv') or ciphertext.get('nonce')
    else:
        ciphertext_bytes = ciphertext
        iv_or_nonce = None

    cipher_module = _CIPHER_MODULE_MAPPING[cipher_key.cipher]

    if cipher_key.cipher in [Sym.Cipher.ChaCha20, Sym.Cipher.ARC4]:
        cipher = cipher_module.new(key=cipher_key.get_key(), nonce=iv_or_nonce)
    elif cipher_key.cipher == Sym.Cipher.ARC2:
        cipher = cipher_module.new(cipher_key.get_key(), mode=ARC2.MODE_CFB, iv=iv_or_nonce)
    else:
        mode = _SYM_OPERATION_CONVERSION.get(mode_id)
        if mode is None:
            raise ValueError("Invalid mode")
        if mode == AES.MODE_ECB:
            cipher = cipher_module.new(cipher_key.get_key(), mode)
        elif mode == AES.MODE_CTR:
            cipher = cipher_module.new(cipher_key.get_key(), mode, nonce=iv_or_nonce)
        else:
            if iv_or_nonce is not None:
                cipher = cipher_module.new(cipher_key.get_key(), mode, iv=iv_or_nonce)
            else:
                nonce, ciphertext_bytes = ciphertext_bytes[:8], ciphertext_bytes[8:]
                cipher = cipher_module.new(cipher_key.get_key(), nonce=nonce)

    plain_bytes = cipher.decrypt(ciphertext_bytes)

    if padding and cipher_key.cipher not in [Sym.Cipher.ChaCha20, Sym.Cipher.ARC4, Sym.Cipher.ARC2]:
        if padding == Sym.Padding.PKCS7:
            pad_len = plain_bytes[-1]
            plain_bytes = plain_bytes[:-pad_len]
        elif padding == Sym.Padding.ANSIX923:
            pad_len = plain_bytes[-1]
            plain_bytes = plain_bytes[:-pad_len]

    return plain_bytes


def encrypt_asym(plain_bytes: bytes, cipher_key, padding=None, strength=None):
    parts = {}

    if cipher_key.cipher == ASym.Cipher.RSA:
        warnings.warn("RSA is insecure and should be migrated away from.")
        hash_algo = (SHA256, SHA384, SHA512)[strength]

        if padding == ASym.Padding.OAEP:
            cipher = PKCS1_OAEP.new(cipher_key.get_public_key(), hashAlgo=hash_algo())
        elif padding == ASym.Padding.PKCShash1v15:
            cipher = PKCS1_v1_5.new(cipher_key.get_public_key())
        else:
            raise NotSupportedError("Unsupported padding for RSA encryption")

        ciphertext = cipher.encrypt(plain_bytes)
        parts['ciphertext'] = ciphertext
    else:
        raise UserWarning(f"Algorithm '{cipher_key.cipher}' does not support encryption")
    return parts


def decrypt_asym(ciphertext: Union[bytes, dict[str, bytes]], cipher_key, padding=None, strength=None):
    if cipher_key.cipher == ASym.Cipher.RSA:
        warnings.warn("RSA is insecure and should be migrated away from.")
        hash_algo = (SHA256, SHA384, SHA512)[strength]

        if padding == ASym.Padding.OAEP:
            cipher = PKCS1_OAEP.new(cipher_key.get_private_key(), hashAlgo=hash_algo())
            plain_bytes = cipher.decrypt(ciphertext)
        elif padding == ASym.Padding.PKCShash1v15:
            cipher = PKCS1_v1_5.new(cipher_key.get_private_key())
            sentinel = b'\x00' * 32  # A sentinel value to detect padding errors
            plain_bytes = cipher.decrypt(ciphertext, sentinel)
            if plain_bytes == sentinel:
                raise ValueError("Decryption failed. Invalid padding.")
        else:
            raise NotSupportedError("Unsupported padding for RSA decryption")
    else:
        raise UserWarning(f"Algorithm '{cipher_key.cipher}' does not support decryption")
    return plain_bytes


def key_derivation(password: bytes, length: int, salt: bytes = None, type_: int = None, strength: int = 2):
    if salt is None:
        if type_ != KeyDerivationFunction.PBKDF1:
            salt = os.urandom([16, 32, 64, 128][strength])
        else:
            salt = os.urandom(8)
    hash_type = (SHA3_224, SHA3_256, SHA3_384, SHA3_512)[strength]

    if type_ == KeyDerivationFunction.PBKDF2HMAC:
        iter_mult = [1, 4, 8, 12][strength]
        return PBKDF2(password, salt, dkLen=length, count=100000 * iter_mult, hmac_hash_module=SHA256)
    elif type_ == KeyDerivationFunction.Scrypt:
        n, r, p = (
            (2 ** 14, 8, 1),
            (2 ** 15, 8, 1),
            (2 ** 16, 8, 2),
            (2 ** 17, 8, 2)
        )[strength]
        return scrypt(password, salt, key_len=length, N=n, r=r, p=p)
    elif type_ == KeyDerivationFunction.HKDF:
        return HKDF(password, key_len=length, salt=salt, hashmod=hash_type)
    elif type_ == KeyDerivationFunction.X963:
        return HKDF(password, key_len=length, salt=salt, hashmod=hash_type)
    elif type_ == KeyDerivationFunction.PBKDF1:
        if length > 20:
            raise ValueError("PBKDF1 cannot derive keys longer than 20 bytes.")
        return PBKDF1(password, salt, dkLen=length, count=100000 * (strength + 1))
    elif type_ == KeyDerivationFunction.KMAC128:
        h = KMAC128.new(key=password, mac_len=length)
        h.update(salt)
        return h.digest()
    elif type_ == KeyDerivationFunction.KMAC256:
        h = KMAC256.new(key=password, mac_len=length)
        h.update(salt)
        return h.digest()
    else:
        raise NotSupportedError(f"Unsupported Key Derivation Function (Index {type_})")


def generate_auth_code(auth_type, cipher_key, data, strength) -> bytes:
    if not isinstance(cipher_key, _BASIC_KEY) or cipher_key.cipher != Sym.Cipher.AES:
        raise ValueError("Invalid key type for generating authentication code")

    hash_algo = (SHA3_224, SHA3_256, SHA3_384, SHA3_512)[strength]
    if auth_type == MessageAuthenticationCode.HMAC:
        h = HMAC.new(cipher_key.get_key(), digestmod=hash_algo)
    elif auth_type == MessageAuthenticationCode.CMAC:
        h = CMAC.new(cipher_key.get_key(), ciphermod=AES)
    elif auth_type == MessageAuthenticationCode.KMAC128:
        h = KMAC128.new(key=cipher_key.get_key(), data=data, custom=b'', mac_len=32)
    elif auth_type == MessageAuthenticationCode.KMAC256:
        h = KMAC256.new(key=cipher_key.get_key(), data=data, custom=b'', mac_len=32)
    elif auth_type == MessageAuthenticationCode.Poly1305:
        h = Poly1305.new(key=cipher_key.get_key(), cipher=AES)
        h.update(data)
        return h.digest()
    else:
        raise NotSupportedError("Unsupported Authentication Code")

    h.update(data)
    return h.digest()


def key_exchange(cipher_key, peer_public_key, algorithm: Literal["ECDH", "DH"]):
    if not isinstance(cipher_key, _BASIC_KEYPAIR) or cipher_key.cipher_type != ASym:
        raise ValueError("Invalid key type for key exchange")

    if algorithm == "ECDH":
        if isinstance(peer_public_key, bytes):
            peer_public_key = ECC.import_key(peer_public_key)

        shared_secret = cipher_key.get_private_key().d * peer_public_key.pointQ
        shared_secret_bytes = shared_secret.x.to_bytes()

        # Use HKDF to derive a shared key from the shared secret
        shared_key = HKDF(shared_secret_bytes, 32, b'', SHA256)
        return shared_key
    else:
        raise NotSupportedError(f"Key exchange is not supported for the algorithm '{algorithm}'")


def sign(cipher_key, data, padding, strength):
    if not isinstance(cipher_key, _BASIC_KEYPAIR) or cipher_key.cipher_type != ASym:
        raise ValueError("Invalid key type for signing")

    hash_algo = (SHA256, SHA384, SHA512)[strength]

    if cipher_key.cipher == ASym.Cipher.RSA:
        warnings.warn("RSA is insecure and should be migrated away from.")
        return pkcs1_15.new(cipher_key.get_private_key()).sign(hash_algo.new(data))
    elif cipher_key.cipher == ASym.Cipher.ECC:
        return DSS.new(cipher_key.get_private_key(), 'fips-186-3').sign(hash_algo.new(data))
    elif cipher_key.cipher == ASym.Cipher.DSA:
        return DSS.new(cipher_key.get_private_key(), 'fips-186-3').sign(hash_algo.new(data))
    else:
        raise NotSupportedError("Unsupported signing algorithm")


def sign_verify(cipher_key, signature, data, padding, strength):
    if not isinstance(cipher_key, _BASIC_KEYPAIR) or cipher_key.cipher_type != ASym:
        raise ValueError("Invalid key type for signature verification")

    hash_algo = (SHA256, SHA384, SHA512)[strength]

    try:
        if cipher_key.cipher == ASym.Cipher.RSA:
            warnings.warn("RSA is insecure and should be migrated away from.")
            pkcs1_15.new(cipher_key.get_public_key()).verify(hash_algo.new(data), signature)
        elif cipher_key.cipher == ASym.Cipher.ECC:
            DSS.new(cipher_key.get_public_key(), 'fips-186-3').verify(hash_algo.new(data), signature)
        elif cipher_key.cipher == ASym.Cipher.DSA:
            DSS.new(cipher_key.get_public_key(), 'fips-186-3').verify(hash_algo.new(data), signature)
        else:
            raise NotSupportedError("Unsupported signing verification algorithm")
        return True
    except (ValueError, TypeError):
        return False
