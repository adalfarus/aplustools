from ._keys import (_BASIC_KEY_TYPE, _BASIC_KEYPAIR_TYPE, Kyber, Argon2, _KYBER_KEYPAIR, _DILITHIUM_KEYPAIR,
                    KKDF as _KKDF)
from ._hashes import (HashAlgorithm as _HashAlgorithm, algorithm_names as _algorithm_names,
                      algorithm_ids as _algorithm_ids)
from .algorithms import (Sym as _Sym, ASym as _ASym, KeyDerivation as _KeyDerivation,
                         MessageAuthenticationCode as _MessageAuthenticationCode)
from .backends import Backend as _Backend
from .. import Security as _Security
from .exceptions import NotSupportedError as _NotSupportedError
from ...io.environment import strict as _strict

from typing import Optional as _Optional
import warnings as _warnings
import os as _os

import bcrypt as _bcrypt


class AdvancedCryptography:
    """
    Makes security easy.

    Remember that easy_hash appends one byte to the start of the hash for identification.

    We do not use human-readable ids because hackers can read too, if you want to find out what hash you have
    you can simply remember your settings or look for the hard coded values in aplustools.security.crypto.hashes"""

    def __init__(self, auto_pack: bool = True, easy_hash: bool = True,
                 backend: _Backend = _Backend.cryptography):
        self._auto_pack = auto_pack
        self._easy_hash = easy_hash

        if backend not in {_Backend.cryptography, _Backend.pycryptodomex}:
            raise _NotSupportedError(f"{backend} is not supported by AdvancedCryptography")
        self._backend = self._real_backend = None
        self.set_backend(backend)

    def set_backend(self, backend: _Backend):
        """Resets the backend to a new one"""
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

    def hash(self, to_hash: bytes, algo: int, force_text_ids: bool = False) -> bytes:
        """
        Hashes to_hash using the provided algorithm and returns it.

        :param to_hash:
        :param algo:
        :param force_text_ids:
        :return:
        """
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
            parts = self._real_backend[1].encrypt_sym(plain_bytes, cipher_key, padding, mode_or_strength)
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

        if self._auto_pack:
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
