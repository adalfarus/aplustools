import warnings

from ._keys import (_BASIC_KEY_TYPE, _BASIC_KEYPAIR_TYPE, Kyber, Argon2, _KYBER_KEYPAIR, _DILITHIUM_KEYPAIR,
                    KKDF as _KKDF)
from ._hashes import (HashAlgorithm as _HashAlgorithm, algorithm_names as _algorithm_names,
                      algorithm_ids as _algorithm_ids)
from .algorithms import (Sym as _Sym, ASym as _ASym, KeyDerivationFunction as _KeyDerivation,
                         MessageAuthenticationCode as _MessageAuthenticationCode)
from .backends import Backend as _Backend
from .. import Security as _Security, RiskLevel as _RiskLevel
from .exceptions import NotSupportedError as _NotSupportedError
from ...io.environment import strict as _strict, suppress_warnings as _suppress_warnings
from ...data import adv_check_types as _adv_check_types

from typing import Optional as _Optional
import warnings as _warnings
import os as _os

import bcrypt as _bcrypt


unsafe: dict[int, tuple[str, str]] = {
    # Symmetric Ciphers Ratings
    _Sym.Cipher.AES: (_RiskLevel.HARMLESS, "AES is strong even against quantum threats with sufficient key length"),
    _Sym.Cipher.ChaCha20: (_RiskLevel.HARMLESS, "ChaCha20 is a strong alternative to AES"),
    _Sym.Cipher.TripleDES: (_RiskLevel.KNOWN_UNSAFE_NOT_RECOMMENDED, "TripleDES is vulnerable to meet-in-the-middle attacks"),
    _Sym.Cipher.Blowfish: (_RiskLevel.NOT_RECOMMENDED, "Blowfish is outdated and slow"),
    _Sym.Cipher.CAST5: (_RiskLevel.NOT_RECOMMENDED, "CAST5 has limited key size and is outdated"),
    _Sym.Cipher.ARC4: (_RiskLevel.HIGHLY_DANGEROUS, "ARC4 has multiple vulnerabilities"),
    _Sym.Cipher.Camellia: (_RiskLevel.HARMLESS, "Camellia is comparable to AES"),
    _Sym.Cipher.IDEA: (_RiskLevel.NOT_RECOMMENDED, "IDEA has patent issues and is outdated"),
    _Sym.Cipher.SEED: (_RiskLevel.NOT_RECOMMENDED, "SEED has limited adoption and is outdated"),
    _Sym.Cipher.SM4: (_RiskLevel.HARMLESS, "SM4 is a modern cipher and is strong"),
    _Sym.Cipher.DES: (_RiskLevel.HIGHLY_DANGEROUS, "DES is easily broken"),
    _Sym.Cipher.ARC2: (_RiskLevel.HIGHLY_DANGEROUS, "ARC2 is weak and outdated"),
    _Sym.Cipher.Salsa20: (_RiskLevel.NOT_RECOMMENDED, "Prefer ChaCha20 over Salsa20"),

    # Symmetric Modes Ratings
    _Sym.Operation.ECB: (_RiskLevel.HIGHLY_DANGEROUS, "ECB mode does not hide patterns"),
    _Sym.Operation.CBC: (_RiskLevel.KNOWN_UNSAFE, "CBC mode is susceptible to padding oracle attacks without proper care"),
    _Sym.Operation.CFB: (_RiskLevel.NOT_RECOMMENDED, "CFB mode is not as secure as newer modes"),
    _Sym.Operation.OFB: (_RiskLevel.NOT_RECOMMENDED, "OFB mode is vulnerable to bit-flipping attacks"),
    _Sym.Operation.CTR: (_RiskLevel.NOT_RECOMMENDED, "CTR mode must handle nonce correctly"),
    _Sym.Operation.GCM: (_RiskLevel.HARMLESS, "GCM mode is strong and provides integrity"),

    # Symmetric Padding Ratings
    _Sym.Padding.PKCS7: (_RiskLevel.HARMLESS, "PKCS7 padding is widely used and safe when implemented correctly"),
    _Sym.Padding.ANSIX923: (_RiskLevel.NOT_RECOMMENDED, "ANSIX923 padding is less common, prefer PKCS7"),

    # Asymmetric Cipher Ratings
    _ASym.Cipher.RSA: (_RiskLevel.NOT_RECOMMENDED, "RSA is vulnerable to quantum attacks"),
    _ASym.Cipher.DSA: (_RiskLevel.NOT_RECOMMENDED, "DSA is outdated, replaced by ECDSA"),
    _ASym.Cipher.ECC: (_RiskLevel.HARMLESS, "ECC is strong, with smaller keys, considering quantum threats in the future"),
    _ASym.Cipher.KYBER: (_RiskLevel.HARMLESS, "KYBER is post-quantum secure"),
    _ASym.Cipher.DILITHIUM: (_RiskLevel.HARMLESS, "DILITHIUM is post-quantum secure"),

    # Asymmetric Paddings Ratings
    _ASym.Padding.PKCShash1v15: (_RiskLevel.KNOWN_UNSAFE, "PKCShash1v15 is deprecated and susceptible to certain attacks"),
    _ASym.Padding.OAEP: (_RiskLevel.HARMLESS, "OAEP is a secure padding scheme for RSA"),
    _ASym.Padding.PSS: (_RiskLevel.HARMLESS, "PSS is a secure padding for RSA signatures"),

    # Key Derivation Functions Ratings
    _KeyDerivation.PBKDF2HMAC: (_RiskLevel.NOT_RECOMMENDED, "PBKDF2HMAC is secure, but better alternatives are available (e.g., Argon2)"),
    _KeyDerivation.Scrypt: (_RiskLevel.HARMLESS, "Scrypt is stronger than PBKDF2"),
    _KeyDerivation.HKDF: (_RiskLevel.HARMLESS, "HKDF is secure for key derivation"),
    _KeyDerivation.X963: (_RiskLevel.NOT_RECOMMENDED, "X963 is outdated"),
    _KeyDerivation.ConcatKDF: (_RiskLevel.NOT_RECOMMENDED, "ConcatKDF is less commonly used"),
    _KeyDerivation.PBKDF1: (_RiskLevel.HIGHLY_DANGEROUS, "PBKDF1 is outdated and insecure"),
    _KeyDerivation.KMAC128: (_RiskLevel.HARMLESS, "KMAC128 is secure"),
    _KeyDerivation.KMAC256: (_RiskLevel.HARMLESS, "KMAC256 is secure"),
    _KeyDerivation.ARGON2: (_RiskLevel.HARMLESS, "Argon2 is the best practice for password hashing"),
    _KeyDerivation.KKDF: (_RiskLevel.NOT_RECOMMENDED, "KKDF is less commonly used"),
    _KeyDerivation.BCRYPT: (_RiskLevel.NOT_RECOMMENDED, "BCRYPT is secure for password hashing, but better alternatives (e.g., Argon2) exist"),

    # Message Authentication Codes Ratings
    _MessageAuthenticationCode.HMAC: (_RiskLevel.HARMLESS, "HMAC is secure and widely used"),
    _MessageAuthenticationCode.CMAC: (_RiskLevel.HARMLESS, "CMAC is secure and widely used"),
    _MessageAuthenticationCode.KMAC128: (_RiskLevel.HARMLESS, "KMAC128 is secure"),
    _MessageAuthenticationCode.KMAC256: (_RiskLevel.HARMLESS, "KMAC256 is secure"),
    _MessageAuthenticationCode.Poly1305: (_RiskLevel.HARMLESS, "Poly1305 is secure"),

    # Hash Ratings
    _HashAlgorithm.SHA1: (_RiskLevel.KNOWN_UNSAFE, "SHA1 is vulnerable to collision attacks"),
    _HashAlgorithm.SHA2.SHA224: (_RiskLevel.HARMLESS, "SHA224 is secure, but less common than SHA256"),
    _HashAlgorithm.SHA2.SHA256: (_RiskLevel.HARMLESS, "SHA256 is secure and widely used"),
    _HashAlgorithm.SHA2.SHA384: (_RiskLevel.HARMLESS, "SHA384 is secure and widely used"),
    _HashAlgorithm.SHA2.SHA512: (_RiskLevel.HARMLESS, "SHA512 is secure and widely used"),
    _HashAlgorithm.SHA2.SHA512_244: (_RiskLevel.HARMLESS, "SHA512_244 is secure, but a lesser-known variant"),
    _HashAlgorithm.SHA2.SHA512_256: (_RiskLevel.HARMLESS, "SHA512_256 is secure, but a lesser-known variant"),
    _HashAlgorithm.SHA3.SHA224: (_RiskLevel.HARMLESS, "SHA3-224 is secure"),
    _HashAlgorithm.SHA3.SHA256: (_RiskLevel.HARMLESS, "SHA3-256 is secure"),
    _HashAlgorithm.SHA3.SHA384: (_RiskLevel.HARMLESS, "SHA3-384 is secure"),
    _HashAlgorithm.SHA3.SHA512: (_RiskLevel.HARMLESS, "SHA3-512 is secure"),
    _HashAlgorithm.SHA3.SHAKE128: (_RiskLevel.HARMLESS, "SHAKE128 is secure with variable output length"),
    _HashAlgorithm.SHA3.SHAKE256: (_RiskLevel.HARMLESS, "SHAKE256 is secure with variable output length"),
    _HashAlgorithm.SHA3.TurboSHAKE128: (_RiskLevel.HARMLESS, "TurboSHAKE128 is secure with variable output length"),
    _HashAlgorithm.SHA3.TurboSHAKE256: (_RiskLevel.HARMLESS, "TurboSHAKE256 is secure with variable output length"),
    _HashAlgorithm.SHA3.KangarooTwelve: (_RiskLevel.HARMLESS, "KangarooTwelve is secure and more efficient than SHA3"),
    _HashAlgorithm.SHA3.TupleHash128: (_RiskLevel.HARMLESS, "TupleHash128 is secure and used for hashing tuples"),
    _HashAlgorithm.SHA3.TupleHash256: (_RiskLevel.HARMLESS, "TupleHash256 is secure and used for hashing tuples"),
    _HashAlgorithm.SHA3.keccak: (_RiskLevel.HARMLESS, "Keccak is secure and the original SHA3 winner"),
    _HashAlgorithm.BLAKE2.BLAKE2b: (_RiskLevel.HARMLESS, "BLAKE2b is secure and faster than SHA2"),
    _HashAlgorithm.BLAKE2.BLAKE2s: (_RiskLevel.HARMLESS, "BLAKE2s is secure and faster than SHA2"),
    _HashAlgorithm.MD2: (_RiskLevel.HIGHLY_DANGEROUS, "MD2 is obsolete and easily broken"),
    _HashAlgorithm.MD4: (_RiskLevel.HIGHLY_DANGEROUS, "MD4 is obsolete and easily broken"),
    _HashAlgorithm.MD5: (_RiskLevel.HIGHLY_DANGEROUS, "MD5 is vulnerable to collision attacks"),
    _HashAlgorithm.SM3: (_RiskLevel.NOT_RECOMMENDED, "SM3 is secure but less studied outside of China"),
    _HashAlgorithm.RIPEMD160: (_RiskLevel.NOT_RECOMMENDED, "RIPEMD160 is secure but less common"),
    _HashAlgorithm.BCRYPT: (_RiskLevel.NOT_RECOMMENDED, "BCRYPT is secure for password hashing, but better alternatives (e.g., Argon2) exist"),
    _HashAlgorithm.ARGON2: (_RiskLevel.HARMLESS, "Argon2 is the best practice for password hashing"),
}


class AdvancedCryptography:
    """
    Makes security easy.

    Remember that easy_hash appends one byte to the start of the hash for identification.

    We do not use human-readable ids because hackers can read too, if you want to find out what hash you have
    you can simply remember your settings or look for the hard coded values in aplustools.security.crypto.hashes"""
    _instance = None
    auto_pack = easy_hash = True
    _backend = _real_backend = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(AdvancedCryptography, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        raise ValueError("You can't instance this class, please use AdvancedCryptography.get() instead")

    @classmethod
    def get(cls):
        """Get the singleton instance."""
        try:
            cls._instance = cls()
        except ValueError:
            return cls._instance

    def set_backend(self, backend: _Backend):
        """Resets the backend to a new one"""
        if backend not in {_Backend.cryptography, _Backend.pycryptodomex}:
            raise _NotSupportedError(f"{backend.name} is not supported by AdvancedCryptography")

        with _suppress_warnings():
            self._backend = backend
            if backend == _Backend.cryptography:
                from ._crypto import hashes, keys
            else:
                from ._pycrypto import hashes, keys
            self._real_backend = (hashes, keys)
            _Sym.Cipher.AES._AES_KEY = keys._AES_KEY
            _Sym.Cipher.ChaCha20._ChaCha20_KEY = keys._ChaCha20_KEY
            _Sym.Cipher.TripleDES._TripleDES_KEY = keys._TripleDES_KEY
            _Sym.Cipher.Blowfish._Blowfish_KEY = keys._Blowfish_KEY
            _Sym.Cipher.CAST5._CAST5_KEY = keys._CAST5_KEY
            _Sym.Cipher.ARC4._ARC4_KEY = keys._ARC4_KEY
            _Sym.Cipher.Camellia._Camellia_KEY = keys._Camellia_KEY
            _Sym.Cipher.IDEA._IDEA_KEY = keys._IDEA_KEY
            _Sym.Cipher.SEED._SEED_KEY = keys._SEED_KEY
            _Sym.Cipher.SM4._SM4_KEY = keys._SM4_KEY
            _Sym.Cipher.DES._DES_KEY = keys._DES_KEY
            _Sym.Cipher.ARC2._ARC2_KEY = keys._ARC2_KEY
            _Sym.Cipher.Salsa20._Salsa20_KEY = keys._Salsa20_KEY
            _ASym.Cipher.RSA._RSA_KEYPAIR = keys._RSA_KEYPAIR
            _ASym.Cipher.DSA._DSA_KEYPAIR = keys._DSA_KEYPAIR
            _ASym.Cipher.ECC._ECC_KEYPAIR = keys._ECC_KEYPAIR
            _ASym.Cipher.KYBER._KYBER_KEYPAIR = _KYBER_KEYPAIR
            _ASym.Cipher.DILITHIUM._DILITHIUM_KEYPAIR = _DILITHIUM_KEYPAIR

    @staticmethod
    def check_unsafe(*to_check, max_unsafe_rating: _RiskLevel = _RiskLevel.HARMLESS, force_hand: bool = True
                     ) -> _Optional[list[Exception | Warning]]:
        """Checks the rating of multiple items and returns appropriate Exceptions/Warnings"""
        returns = []
        checker = {
            _RiskLevel.HARMLESS: 0,
            _RiskLevel.NOT_RECOMMENDED: 1,
            _RiskLevel.KNOWN_UNSAFE: 2,
            _RiskLevel.KNOWN_UNSAFE_NOT_RECOMMENDED: 3,
            _RiskLevel.HIGHLY_DANGEROUS: 4
        }

        for check in to_check:
            rating, expl = unsafe.get(check, (None, None))
            if rating is not None:
                if checker[rating] > checker[max_unsafe_rating]:
                    returns.append(
                        {_RiskLevel.NOT_RECOMMENDED: Warning,
                         _RiskLevel.KNOWN_UNSAFE: Warning,
                         _RiskLevel.KNOWN_UNSAFE_NOT_RECOMMENDED: Exception,
                         _RiskLevel.HIGHLY_DANGEROUS: Exception}[rating](expl)
                    )

        if force_hand:
            for ret in returns:
                if isinstance(ret, Exception) and not isinstance(ret, Warning):
                    raise ret
                warnings.warn(ret)
            return

        return returns

    @classmethod
    def check_backend(cls):
        """Checks for an empty backend"""
        if cls._backend is _Backend.cryptography:
            return
        elif cls._backend is _Backend.pycryptodomex:
            warnings.warn("PyCryptodomeX is not fully compatible yet")
        raise ValueError("Please set a Backend before usage")

    @_adv_check_types(strict_args={'to_hash': True, 'algo': True, 'force_text_ids': False, 'maximum_risk_level': True})
    def hash(self, to_hash: bytes, algo: _HashAlgorithm, force_text_ids: bool = False,
             maximum_risk_level: _RiskLevel = _RiskLevel.HARMLESS) -> bytes:
        """
        Hashes to_hash using the provided algorithm and returns it.

        :param to_hash:
        :param algo:
        :param force_text_ids:
        :param maximum_risk_level:
        :return:
        """
        self.check_backend()
        self.check_unsafe(algo, maximum_risk_level)
        match algo:
            case _HashAlgorithm.BCRYPT:
                try:
                    result = self._real_backend[0].hash(to_hash, algo)
                except _NotSupportedError:
                    result = _bcrypt.hashpw(to_hash, _bcrypt.gensalt())
            case _HashAlgorithm.ARGON2:
                _warnings.warn("Argon2 is still not perfectly supported, expect bugs or other mishaps.",
                              category=UserWarning, stacklevel=2)
                if Kyber is None:
                    raise EnvironmentError("Module QuantCrypt is not installed.")
                result = Argon2.Hash(to_hash).public_hash.encode()  # .split("$", maxsplit=2)[-1].encode()
            case _:
                result = self._real_backend[0].hash(to_hash, algo)
        final_hash_id = b""
        if self._easy_hash:
            if force_text_ids:
                final_hash_id = b"$" + _algorithm_names[algo].encode() + b"$"
            else:
                final_hash_id = algo.to_bytes(1, "big")
        return final_hash_id + result

    @_adv_check_types(strict_args={'to_verify': True, 'original_hash': True, 'algo': True, 'forced_text_ids': True})
    def hash_verify(self, to_verify: bytes, original_hash: bytes, algo: _Optional[int] = None,
                    forced_text_ids: bool = False):
        """
        Verifies that original_hash was generated from to_verify, optionally a specific algorithm can be specified.

        :param to_verify:
        :param original_hash:
        :param algo:
        :param forced_text_ids:
        :return:
        """
        if self._easy_hash and algo is None:
            if forced_text_ids:
                _, algo_name, original_hash = original_hash.split(b"$", maxsplit=2)
                algo = _algorithm_ids[algo_name.decode()]
            elif isinstance(original_hash, bytes):
                algo = original_hash[0]
                original_hash = original_hash[1:]
        match algo:
            case _HashAlgorithm.BCRYPT:
                try:
                    return self._real_backend[0].hash(to_verify, algo, original_hash)
                except _NotSupportedError:
                    return _bcrypt.checkpw(to_verify, original_hash)
            case _HashAlgorithm.ARGON2:
                _warnings.warn("Argon2 is still not perfectly supported, expect bugs or other mishaps.",
                              category=UserWarning, stacklevel=2)
                if Kyber is None:
                    raise EnvironmentError("Module QuantCrypt is not installed.")
                try:
                    Argon2.Hash(to_verify, original_hash.decode())
                    return True
                except Exception as e:
                    print(f"Exception occurred: {e}")
                    return False
            case _:
                result = self._real_backend[0].hash(to_verify, algo)
        return result == original_hash

    @_adv_check_types(strict_args={'plain_bytes': True, 'cipher_key': False, 'padding': True, 'mode_or_strength': True})
    def encrypt(self, plain_bytes: bytes, cipher_key: _BASIC_KEY_TYPE | _BASIC_KEYPAIR_TYPE,
                padding: _Optional[_Sym.Padding | _ASym.Padding] = None,
                mode_or_strength: _Optional[_Sym.Operation] | _Security = None) -> bytes | dict:
        """
        Encrypts the plain bytes using the configuration provided and returns it.

        :param plain_bytes:
        :param cipher_key:
        :param padding:
        :param mode_or_strength:
        :return:
        """
        parts = {}

        if cipher_key.cipher_type == _Sym:
            if padding and isinstance(mode_or_strength, _Sym.Operation):
                parts = self._real_backend[1].encrypt_sym(plain_bytes, cipher_key, padding, mode_or_strength)
            else:
                raise ValueError("Please pass a correct padding and mode to use Symmetric encryption.")
        elif cipher_key.cipher_type == _ASym:
            if cipher_key.cipher == _ASym.Cipher.RSA:
                parts = self._real_backend[1].encrypt_asym(plain_bytes, cipher_key, padding, mode_or_strength)
            elif cipher_key.cipher == _ASym.Cipher.KYBER:
                _warnings.warn("Kyber is still not perfectly supported, expect bugs or other mishaps.",
                              category=UserWarning, stacklevel=2)
                if Kyber is None:
                    raise EnvironmentError("Module QuantCrypt is not installed.")
                parts["ciphertext"] = cipher_key.encrypt(plain_bytes)
            else:
                raise _NotSupportedError(f"The algorithm '{cipher_key.cipher_type}' cannot be used for encryption")

        if self.auto_pack:
            outputs = b''.join(v for k, v in parts.items())
        else:
            outputs = parts

        return outputs

    def decrypt(self, cipher_bytes: bytes | dict, cipher_key: type[_BASIC_KEY_TYPE | _BASIC_KEYPAIR_TYPE],
                padding: _Optional[_Sym.Padding | _ASym.Padding] = None,
                mode: _Optional[_Sym.Operation] | _Security = None) -> bytes:
        if cipher_key.cipher_type == _Sym:
            result = self._real_backend[1].decrypt_sym(cipher_bytes, cipher_key, padding, mode)
        elif cipher_key.cipher_type == _ASym:
            if cipher_key.cipher == _ASym.Cipher.RSA:
                result = self._real_backend[1].decrypt_asym(cipher_bytes, cipher_key, padding, mode)
            elif cipher_key.cipher == _ASym.Cipher.KYBER:
                _warnings.warn("Kyber is still not perfectly supported, expect bugs or other mishaps.",
                              category=UserWarning, stacklevel=2)
                if Kyber is None:
                    raise EnvironmentError("Module QuantCrypt is not installed.")
                result = cipher_key.decrypt(cipher_bytes)
            else:
                raise _NotSupportedError("DSA and ECC cannot be used for encryption")
        return result

    def key_derivation(self, password: bytes, length: int, salt: bytes = None,
                       kdf_type: _KeyDerivation = _KeyDerivation.PBKDF2HMAC, strength: _Security = _Security.STRONG):
        """

        :param password:
        :param length:
        :param salt:
        :param kdf_type:
        :param strength:
        """
        if kdf_type == _KeyDerivation.ARGON2:
            _warnings.warn("Argon2 is still not perfectly supported, expect bugs or other mishaps.",
                          category=UserWarning, stacklevel=2)
            if Kyber is None:
                raise EnvironmentError("Module QuantCrypt is not installed.")
            return Argon2.Key(password).secret_key
        elif kdf_type == _KeyDerivation.KKDF:
            _warnings.warn("KKDF is still not perfectly supported, expect bugs or other mishaps.",
                          category=UserWarning, stacklevel=2)
            if Kyber is None:
                raise EnvironmentError("Module QuantCrypt is not installed.")
            return _KKDF(master=password, key_len=length, num_keys=1)[0]
        elif kdf_type == _KeyDerivation.BCRYPT:
            if salt is None:
                salt = _os.urandom([16, 32, 64, 128][strength])
            rounds = (100, 400, 800, 1600, 3200)[strength]
            return _bcrypt.kdf(
                password=password,
                salt=salt,
                desired_key_bytes=length,
                rounds=rounds)
        return self._real_backend[1].key_derivation(password, length, salt, kdf_type, strength)

    def generate_auth_code(self, auth_type: _MessageAuthenticationCode, cipher_key, data: bytes,
                           strength: _Security = _Security.STRONG) -> bytes:
        return self._real_backend[1].generate_auth_code(auth_type, cipher_key, data, strength)

    def key_exchange(self, cipher_key, peer_public_key):
        """Diffie Hellman key exchange"""
        return self._real_backend[1].key_exchange(cipher_key, peer_public_key, "ECDH" if cipher_key.cipher ==
                                                                                         _ASym.Cipher.ECC else "DH")

    def sign(self, data, cipher_key, padding=None, strength=None):
        if cipher_key.cipher == _ASym.Cipher.DILITHIUM:
            _warnings.warn("DILITHIUM is still not perfectly supported, expect bugs or other mishaps.",
                          category=UserWarning, stacklevel=2)
            return cipher_key.sign(data)
        return self._real_backend[1].sign(data, cipher_key, padding, strength)

    def sign_verify(self, data, signature, cipher_key, padding=None, strength=None):
        if cipher_key.cipher == _ASym.Cipher.DILITHIUM:
            _warnings.warn("DILITHIUM is still not perfectly supported, expect bugs or other mishaps.",
                          category=UserWarning, stacklevel=2)
            return cipher_key.verify(data, signature)
        return self._real_backend[1].sign_verify(data, signature, cipher_key, padding, strength)


class PasswordManager:
    """
    Uses Scrypt as it's hashing function due to its stronger resistance to GPU and ASIC attacks and to better protect
    against evolving attack vectors.
    """
    def __init__(self, backend):
        self._ac = AdvancedCryptography(backend=backend)

    def hash_password(self, password: str, kdf: _KeyDerivation = _KeyDerivation.Scrypt, strength: _Security = _Security.STRONG) -> bytes:
        salt = _os.urandom((16, 32, 64, 128)[strength])
        return salt + self._ac.key_derivation(password.encode(), 64, salt=salt, kdf_type=kdf, strength=strength)

    def verify_password(self, password: str, hashed_password: bytes, kdf: _KeyDerivation = _KeyDerivation.Scrypt, strength: _Security = _Security.STRONG) -> bool:
        salt_length = (16, 32, 64, 128)[strength]
        salt, hashed_password = hashed_password[:salt_length], hashed_password[salt_length:]
        derived_key = self._ac.key_derivation(password.encode(), 64, salt=salt, kdf_type=kdf, strength=strength)
        return derived_key == hashed_password


@_strict(mark_class_as_cover_or_cls=False)
class DataEncryptor:
    """
    Uses AES X-bit encryption which is very secure if used with a sufficient key size like 256.
    """
    def __init__(self, password_key_or_key_size: bytes | str | int = 256, backend=_Backend.cryptography):
        self._ac = AdvancedCryptography(backend=backend)
        self._key = _Sym.Cipher.AES.key(password_key_or_key_size)

    def get_key(self) -> bytes:
        return self._key.get_key()

    def encrypt_data(self, data: bytes, padding: _Sym.Padding = _Sym.Padding.PKCS7, mode: _Sym.Operation = _Sym.Operation.CBC) -> bytes:
        encrypted_data = self._ac.encrypt(data, self._key, padding, mode)
        return encrypted_data

    def decrypt_data(self, encrypted_data: bytes, padding: _Sym.Padding = _Sym.Padding.PKCS7, mode: _Sym.Operation = _Sym.Operation.CBC) -> bytes:
        return self._ac.decrypt(encrypted_data, self._key, padding, mode)


@_strict(mark_class_as_cover_or_cls=False)
class DigitalSigner:
    """
    Uses ECC signatures with the SECP256R1 curve, as it provides strong security against potential future threats
    from quantum computers.
    """
    def __init__(self, private_key: _Optional[bytes] = None, backend=_Backend.cryptography):
        self._ac = AdvancedCryptography(backend=backend)
        self._key_pair = _ASym.Cipher.ECC.ecdsa_key(_ASym.Cipher.ECC.Curve.SECP256R1, private_key)

    def get_private_key(self) -> bytes:
        return self._key_pair.get_private_bytes()

    def sign_data(self, data: bytes, padding: _Optional[_ASym.Padding] = _ASym.Padding.PSS, strength: _Security = _Security.STRONG) -> bytes:
        return self._ac.sign(data, self._key_pair, padding, strength)

    def verify_signature(self, data: bytes, signature: bytes, padding: _Optional[_ASym.Padding] = _ASym.Padding.PSS, strength: _Security = _Security.STRONG) -> bool:
        return self._ac.sign_verify(data, signature, self._key_pair, padding, strength)
