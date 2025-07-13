"""TBA"""
from importlib import import_module as _import_module
import warnings as _warnings
import os as _os

# from .algos import (Sym as _Sym, ASym as _ASym, HashAlgorithm as _HashAlgorithm,
#                     KeyDerivationFunction as _KDF)
from ._definitions import _HASHER_BACKEND, _HASHER_WITH_LEN_BACKEND, _HASHID_TO_STRING, Backend
from .. import Security as _Security, RiskLevel as _RiskLevel
from .exceptions import NotSupportedError as _NotSupportedError

from ...io.env import suppress_warnings as _suppress_warnings
from ...package import enforce_hard_deps as _enforce_hard_deps, optional_import as _optional_import

# Standard typing imports for aps
import typing_extensions as _te
import collections.abc as _a
import typing as _ty
if _ty.TYPE_CHECKING:
    import _typeshed as _tsh
import types as _ts

__all__ = ["Backend", "set_backend", "MAXIMUM_RISK_LEVEL"]
__hard_deps__: list[str] = []
_enforce_hard_deps(__hard_deps__, __name__)


# if 1!=1:
#     safety_rating: dict[_ty.Any, tuple[_RiskLevel, str]] = {
#         # Symmetric Ciphers Ratings
#         _Sym.Cipher.AES: (_RiskLevel.HARMLESS, "AES is strong even against quantum threats with sufficient key length"),
#         _Sym.Cipher.ChaCha20: (_RiskLevel.HARMLESS, "ChaCha20 is a strong alternative to AES"),
#         _Sym.Cipher.TripleDES: (_RiskLevel.KNOWN_UNSAFE_NOT_RECOMMENDED, "TripleDES is vulnerable to meet-in-the-middle attacks"),
#         _Sym.Cipher.Blowfish: (_RiskLevel.NOT_RECOMMENDED, "Blowfish is outdated and slow"),
#         _Sym.Cipher.CAST5: (_RiskLevel.NOT_RECOMMENDED, "CAST5 has limited key size and is outdated"),
#         _Sym.Cipher.ARC4: (_RiskLevel.HIGHLY_DANGEROUS, "ARC4 has multiple vulnerabilities"),
#         _Sym.Cipher.Camellia: (_RiskLevel.HARMLESS, "Camellia is comparable to AES"),
#         _Sym.Cipher.IDEA: (_RiskLevel.NOT_RECOMMENDED, "IDEA has patent issues and is outdated"),
#         _Sym.Cipher.SEED: (_RiskLevel.NOT_RECOMMENDED, "SEED has limited adoption and is outdated"),
#         _Sym.Cipher.SM4: (_RiskLevel.HARMLESS, "SM4 is a modern cipher and is strong"),
#         _Sym.Cipher.DES: (_RiskLevel.HIGHLY_DANGEROUS, "DES is easily broken"),
#         _Sym.Cipher.ARC2: (_RiskLevel.HIGHLY_DANGEROUS, "ARC2 is weak and outdated"),
#         _Sym.Cipher.Salsa20: (_RiskLevel.NOT_RECOMMENDED, "Prefer ChaCha20 over Salsa20"),
#
#         # Symmetric Modes Ratings
#         _Sym.Operation.ECB: (_RiskLevel.HIGHLY_DANGEROUS, "ECB mode does not hide patterns"),
#         _Sym.Operation.CBC: (_RiskLevel.KNOWN_UNSAFE, "CBC mode is susceptible to padding oracle attacks without proper care"),
#         _Sym.Operation.CFB: (_RiskLevel.NOT_RECOMMENDED, "CFB mode is not as secure as newer modes"),
#         _Sym.Operation.OFB: (_RiskLevel.NOT_RECOMMENDED, "OFB mode is vulnerable to bit-flipping attacks"),
#         _Sym.Operation.CTR: (_RiskLevel.NOT_RECOMMENDED, "CTR mode must handle nonce correctly"),
#         _Sym.Operation.GCM: (_RiskLevel.HARMLESS, "GCM mode is strong and provides integrity"),
#
#         # Symmetric Padding Ratings
#         _Sym.Padding.PKCS7: (_RiskLevel.HARMLESS, "PKCS7 padding is widely used and safe when implemented correctly"),
#         _Sym.Padding.ANSIX923: (_RiskLevel.NOT_RECOMMENDED, "ANSIX923 padding is less common, prefer PKCS7"),
#
#         # Asymmetric Cipher Ratings
#         _ASym.Cipher.RSA: (_RiskLevel.NOT_RECOMMENDED, "RSA is vulnerable to quantum attacks"),
#         _ASym.Cipher.DSA: (_RiskLevel.NOT_RECOMMENDED, "DSA is outdated, replaced by ECDSA"),
#         _ASym.Cipher.ECC: (_RiskLevel.HARMLESS, "ECC is strong, with smaller keys, considering quantum threats in the future"),
#         _ASym.Cipher.KYBER: (_RiskLevel.HARMLESS, "KYBER is post-quantum secure"),
#         _ASym.Cipher.DILITHIUM: (_RiskLevel.HARMLESS, "DILITHIUM is post-quantum secure"),
#
#         # Asymmetric Paddings Ratings
#         _ASym.Padding.PKCShash1v15: (_RiskLevel.KNOWN_UNSAFE, "PKCShash1v15 is deprecated and susceptible to certain attacks"),
#         _ASym.Padding.OAEP: (_RiskLevel.HARMLESS, "OAEP is a secure padding scheme for RSA"),
#         _ASym.Padding.PSS: (_RiskLevel.HARMLESS, "PSS is a secure padding for RSA signatures"),
#
#         # Key Derivation Functions Ratings
#         _KeyDerivation.PBKDF2HMAC: (_RiskLevel.NOT_RECOMMENDED, "PBKDF2HMAC is secure, but better alternatives are available (e.g., Argon2)"),
#         _KeyDerivation.Scrypt: (_RiskLevel.HARMLESS, "Scrypt is stronger than PBKDF2"),
#         _KeyDerivation.HKDF: (_RiskLevel.HARMLESS, "HKDF is secure for key derivation"),
#         _KeyDerivation.X963: (_RiskLevel.NOT_RECOMMENDED, "X963 is outdated"),
#         _KeyDerivation.ConcatKDF: (_RiskLevel.NOT_RECOMMENDED, "ConcatKDF is less commonly used"),
#         _KeyDerivation.PBKDF1: (_RiskLevel.HIGHLY_DANGEROUS, "PBKDF1 is outdated and insecure"),
#         _KeyDerivation.KMAC128: (_RiskLevel.HARMLESS, "KMAC128 is secure"),
#         _KeyDerivation.KMAC256: (_RiskLevel.HARMLESS, "KMAC256 is secure"),
#         _KeyDerivation.ARGON2: (_RiskLevel.HARMLESS, "Argon2 is the best practice for password hashing"),
#         _KeyDerivation.KKDF: (_RiskLevel.NOT_RECOMMENDED, "KKDF is less commonly used"),
#         _KeyDerivation.BCRYPT: (_RiskLevel.NOT_RECOMMENDED, "BCRYPT is secure for password hashing, but better alternatives (e.g., Argon2) exist"),
#
#         # Message Authentication Codes Ratings
#         _MessageAuthenticationCode.HMAC: (_RiskLevel.HARMLESS, "HMAC is secure and widely used"),
#         _MessageAuthenticationCode.CMAC: (_RiskLevel.HARMLESS, "CMAC is secure and widely used"),
#         _MessageAuthenticationCode.KMAC128: (_RiskLevel.HARMLESS, "KMAC128 is secure"),
#         _MessageAuthenticationCode.KMAC256: (_RiskLevel.HARMLESS, "KMAC256 is secure"),
#         _MessageAuthenticationCode.Poly1305: (_RiskLevel.HARMLESS, "Poly1305 is secure"),
#
#         # Hash Ratings
#         _HashAlgorithm.SHA1: (_RiskLevel.KNOWN_UNSAFE, "SHA1 is vulnerable to collision attacks"),
#         _HashAlgorithm.SHA2.SHA224: (_RiskLevel.HARMLESS, "SHA224 is secure, but less common than SHA256"),
#         _HashAlgorithm.SHA2.SHA256: (_RiskLevel.HARMLESS, "SHA256 is secure and widely used"),
#         _HashAlgorithm.SHA2.SHA384: (_RiskLevel.HARMLESS, "SHA384 is secure and widely used"),
#         _HashAlgorithm.SHA2.SHA512: (_RiskLevel.HARMLESS, "SHA512 is secure and widely used"),
#         _HashAlgorithm.SHA2.SHA512_244: (_RiskLevel.HARMLESS, "SHA512_244 is secure, but a lesser-known variant"),
#         _HashAlgorithm.SHA2.SHA512_256: (_RiskLevel.HARMLESS, "SHA512_256 is secure, but a lesser-known variant"),
#         _HashAlgorithm.SHA3.SHA224: (_RiskLevel.HARMLESS, "SHA3-224 is secure"),
#         _HashAlgorithm.SHA3.SHA256: (_RiskLevel.HARMLESS, "SHA3-256 is secure"),
#         _HashAlgorithm.SHA3.SHA384: (_RiskLevel.HARMLESS, "SHA3-384 is secure"),
#         _HashAlgorithm.SHA3.SHA512: (_RiskLevel.HARMLESS, "SHA3-512 is secure"),
#         _HashAlgorithm.SHA3.SHAKE128: (_RiskLevel.HARMLESS, "SHAKE128 is secure with variable output length"),
#         _HashAlgorithm.SHA3.SHAKE256: (_RiskLevel.HARMLESS, "SHAKE256 is secure with variable output length"),
#         _HashAlgorithm.SHA3.TurboSHAKE128: (_RiskLevel.HARMLESS, "TurboSHAKE128 is secure with variable output length"),
#         _HashAlgorithm.SHA3.TurboSHAKE256: (_RiskLevel.HARMLESS, "TurboSHAKE256 is secure with variable output length"),
#         _HashAlgorithm.SHA3.KangarooTwelve: (_RiskLevel.HARMLESS, "KangarooTwelve is secure and more efficient than SHA3"),
#         _HashAlgorithm.SHA3.TupleHash128: (_RiskLevel.HARMLESS, "TupleHash128 is secure and used for hashing tuples"),
#         _HashAlgorithm.SHA3.TupleHash256: (_RiskLevel.HARMLESS, "TupleHash256 is secure and used for hashing tuples"),
#         _HashAlgorithm.SHA3.keccak: (_RiskLevel.HARMLESS, "Keccak is secure and the original SHA3 winner"),
#         _HashAlgorithm.BLAKE2.BLAKE2b: (_RiskLevel.HARMLESS, "BLAKE2b is secure and faster than SHA2"),
#         _HashAlgorithm.BLAKE2.BLAKE2s: (_RiskLevel.HARMLESS, "BLAKE2s is secure and faster than SHA2"),
#         _HashAlgorithm.MD2: (_RiskLevel.HIGHLY_DANGEROUS, "MD2 is obsolete and easily broken"),
#         _HashAlgorithm.MD4: (_RiskLevel.HIGHLY_DANGEROUS, "MD4 is obsolete and easily broken"),
#         _HashAlgorithm.MD5: (_RiskLevel.HIGHLY_DANGEROUS, "MD5 is vulnerable to collision attacks"),
#         _HashAlgorithm.SM3: (_RiskLevel.NOT_RECOMMENDED, "SM3 is secure but less studied outside of China"),
#         _HashAlgorithm.RIPEMD160: (_RiskLevel.NOT_RECOMMENDED, "RIPEMD160 is secure but less common"),
#         _HashAlgorithm.BCRYPT: (_RiskLevel.NOT_RECOMMENDED, "BCRYPT is secure for password hashing, but better alternatives (e.g., Argon2) exist"),
#         _HashAlgorithm.ARGON2: (_RiskLevel.HARMLESS, "Argon2 is the best practice for password hashing"),
#     }
#     def check_unsafe(*to_check: _ty.Any, max_unsafe_rating: _RiskLevel = _RiskLevel.HARMLESS, auto_raise: bool = True
#                      ) -> list[Exception | Warning] | None:
#         """Checks the rating of multiple items and returns appropriate Exceptions/Warnings"""
#         returns = []
#         checker = {
#             _RiskLevel.HARMLESS: 0,
#             _RiskLevel.NOT_RECOMMENDED: 1,
#             _RiskLevel.KNOWN_UNSAFE: 2,
#             _RiskLevel.KNOWN_UNSAFE_NOT_RECOMMENDED: 3,
#             _RiskLevel.HIGHLY_DANGEROUS: 4
#         }
#
#         for check in to_check:
#             rating, expl = safety_rating.get(check, (None, None))
#             if rating is not None:
#                 if checker[rating] > checker[max_unsafe_rating]:
#                     returns.append(
#                         {_RiskLevel.NOT_RECOMMENDED: Warning,
#                          _RiskLevel.KNOWN_UNSAFE: Warning,
#                          _RiskLevel.KNOWN_UNSAFE_NOT_RECOMMENDED: Exception,
#                          _RiskLevel.HIGHLY_DANGEROUS: Exception}[rating](expl)
#                     )
#
#         if auto_raise:
#             for ret in returns:
#                 if isinstance(ret, Exception) and not isinstance(ret, Warning):
#                     raise ret
#                 _warnings.warn(ret)
#             return None
#
#         return returns

MAXIMUM_RISK_LEVEL: _RiskLevel = _RiskLevel.HARMLESS
BACKENDS: list[Backend] = []

# _ISSUED_KEYS: list[_BASIC_KEYTYPE | _BASIC_KEYPAIRTYPE] = []

def set_backend(backends: list[Backend] | None = None) -> None:
    """Sets a new backend for the crypt submodule"""
    from .algos import (Sym as _Sym, Asym as _Asym, HashAlgorithm as _H,
                        KeyDerivationFunction as _KDF)
    global BACKENDS
    if backends is None:
        backends = [Backend.std_lib]

    backend_modules: list[_ts.ModuleType] = []
    for backend in backends:
        if not isinstance(backend, Backend):
            raise _NotSupportedError(f"Backend '{repr(backend)}' is not supported by aplustools.crypt")
        try:
            backend_modules.append(_import_module(backend.value[0]))
        except ImportError:
            raise _NotSupportedError(f"The {backend.value[1]} is not yet supported by aplustools.crypt")

    BACKENDS = backends
    with _suppress_warnings():
        # Dynamically set hashes
        _HASHER_BACKEND._MAPPING.clear()  # Clear previous mapping
        for hasher in {_H.SHA1, _H.SHA2.SHA224, _H.SHA2.SHA256, _H.SHA2.SHA384, _H.SHA2.SHA512, _H.SHA2.SHA512_244,
                       _H.SHA2.SHA512_256, _H.SHA3.SHA224, _H.SHA3.SHA256, _H.SHA3.SHA384, _H.SHA3.SHA512,
                       _H.SHA3.SHAKE128, _H.SHA3.SHAKE256, _H.SHA3.TurboSHAKE128, _H.SHA3.TurboSHAKE256,
                       _H.SHA3.KangarooTwelve, _H.SHA3.TupleHash128, _H.SHA3.TupleHash256, _H.SHA3.CSHAKE128,
                       _H.SHA3.CSHAKE256, _H.MD2, _H.MD4, _H.MD5, _H.SM3, _H.RIPEMD160, _H.BCRYPT, _H.ARGON2,
                       _H.BLAKE2.BLAKE2b, _H.BLAKE2.BLAKE2s}:
            found_hasher: bool = False
            for module in backend_modules:
                hash_func = getattr(module, f"hash_{hasher.algorithm}", None)
                verify_func = getattr(module, f"hash_verify_{hasher.algorithm}", None)

                if not (isinstance(hash_func, _ts.FunctionType) or isinstance(verify_func, _ts.FunctionType)):
                    continue

                if isinstance(hasher, (_HASHER_BACKEND, _HASHER_WITH_LEN_BACKEND)):
                    if not hasher.algorithm in _HASHER_BACKEND._MAPPING:
                        _HASHER_BACKEND._MAPPING[hasher.algorithm] = (hash_func, verify_func)
                else:
                    hasher._IMPLS = (hash_func, verify_func)
                found_hasher = True
                break
            if not found_hasher:
                hasher._IMPLS = None
        # Dynamically set kdfs
        for kdf_to_set in (_KDF.PBKDF2HMAC, _KDF.Scrypt, _KDF.HKDF, _KDF.X963, _KDF.ConcatKDF, _KDF.PBKDF1,
                           _KDF.KMAC128, _KDF.KMAC256, _KDF.ARGON2, _KDF.KKDF, _KDF.BCRYPT):
            name = f"derive_{str(kdf_to_set()).lower()}"
            found_kdf: bool = False
            for module in backend_modules:
                if hasattr(module, name):
                    kdf_to_set._IMPL = getattr(module, name)
                    found_kdf = True
                    break
            if not found_kdf:
                kdf_to_set._IMPL = None
        # Dynamically set keys
        for sym_to_set in {_Sym.Cipher.AES, _Sym.Cipher.ChaCha20, _Sym.Cipher.TripleDES, _Sym.Cipher.Blowfish,
                           _Sym.Cipher.CAST5, _Sym.Cipher.ARC4, _Sym.Cipher.Camellia, _Sym.Cipher.IDEA,
                           _Sym.Cipher.SEED, _Sym.Cipher.SM4, _Sym.Cipher.DES, _Sym.Cipher.ARC2,
                           _Sym.Cipher.Salsa20}:
            key = f"_{sym_to_set()}_KEY"
            found_sym_key: bool = False
            for module in backend_modules:
                if hasattr(module, key):
                    sym_to_set.key = getattr(module, key)
                    sym_to_set.key.__concrete__ = True
                    found_sym_key = True
                    break
            if not found_sym_key:
                sym_to_set.key = _ty.get_type_hints(sym_to_set)["key"].__args__[0]
        for asym_to_set in {_Asym.Cipher.RSA, _Asym.Cipher.DSA, _Asym.Cipher.ECC, _Asym.Cipher.KYBER,
                            _Asym.Cipher.DILITHIUM, _Asym.Cipher.SPHINCS, _Asym.Cipher.FRODOKEM,
                            _Asym.Cipher.BIKE}:
            keypair = f"_{asym_to_set()}_KEYPAIR"
            found_asym_keypair: bool = False
            for module in backend_modules:
                if hasattr(module, keypair):
                    asym_to_set.keypair = getattr(module, keypair)
                    asym_to_set.keypair.__concrete__ = True
                    found_asym_keypair = True
                    break
            if not found_asym_keypair:
                asym_to_set.keypair = _ty.get_type_hints(asym_to_set)["keypair"].__args__[0]


# if 1!=1:
#     class CoreCrypt:
#         """
#         Makes security easy. Remember that easy_hash appends one byte to the start of the hash for identification.
#         If you want text use force_text_ids.
#
#         We do not recommend human-readable ids as hackers can read too, if you want to find out what hash you have
#         in another program, look for the hard-coded values in aplustools.security.crypto.hashes.
#         """
#
#         def __init__(self, auto_pack: bool = True, easy_hash: bool = True,
#                      maximum_risk_level: _RiskLevel = _RiskLevel.HARMLESS, backend: Backend | None = None) -> None:
#             self._backend: Backend | None = None
#             self._real_backend: tuple[_ts.ModuleType, _ts.ModuleType] | None = None
#             self.auto_pack: bool = auto_pack
#             self.easy_hash: bool = easy_hash
#             self.maximum_risk_level: _RiskLevel = maximum_risk_level
#
#             self.issued_keys: list[_BASIC_KEYTYPE | _BASIC_KEYPAIRTYPE] = []
#
#             if backend is not None:
#                 self.set_backend(backend)
#
#         def hash(self, to_hash: bytes, algo: int, force_text_ids: bool = False) -> bytes:
#             """
#             Hashes to_hash using the provided algorithm and returns it.
#
#             :param to_hash:
#             :param algo:
#             :param force_text_ids:
#             :return:
#             """
#             if self._backend is None or self._real_backend is None:
#                 raise ValueError("Please set a Backend before usage")
#             self.check_unsafe(algo, max_unsafe_rating=self.maximum_risk_level)
#             result: bytes
#             match algo:
#                 case _HashAlgorithm.BCRYPT:
#                     try:
#                         result = self._real_backend[0].hash(to_hash, algo)
#                     except _NotSupportedError:
#                         if _bcrypt is None:
#                             raise RuntimeError("bcrypt is not installed")
#                         result = _bcrypt.hashpw(to_hash, _bcrypt.gensalt())
#                 case _HashAlgorithm.ARGON2:
#                     _warnings.warn("Argon2 is still not perfectly supported, expect bugs or other mishaps.",
#                                   category=UserWarning, stacklevel=2)
#                     if Kyber is None or Argon2 is None:
#                         raise EnvironmentError("Module QuantCrypt is not installed.")
#                     result = Argon2.Hash(to_hash).public_hash.encode()  # .split("$", maxsplit=2)[-1].encode()
#                 case _:
#                     result = self._real_backend[0].hash(to_hash, algo)
#             final_hash_id: bytes = b""
#             if self.easy_hash:
#                 if force_text_ids:
#                     final_hash_id = b"$" + _algorithm_names[algo].encode() + b"$"
#                 else:
#                     final_hash_id = algo.to_bytes(1, "big")
#             return final_hash_id + result
#
#         def hash_verify(self, to_verify: bytes, original_hash: bytes, algo: int | None = None,
#                         forced_text_ids: bool = False) -> bool:
#             """
#             Verifies that original_hash was generated from to_verify, optionally a specific algorithm can be specified.
#
#             :param to_verify:
#             :param original_hash:
#             :param algo:
#             :param forced_text_ids:
#             :return:
#             """
#             if self._backend is None or self._real_backend is None:
#                 raise ValueError("Please set a Backend before usage")
#             if self.easy_hash and algo is None:
#                 if forced_text_ids:
#                     _, algo_name, original_hash = original_hash.split(b"$", maxsplit=2)
#                     algo = _algorithm_ids[algo_name.decode()]
#                 elif isinstance(original_hash, bytes):
#                     algo = original_hash[0]
#                     original_hash = original_hash[1:]
#             match algo:
#                 case _HashAlgorithm.BCRYPT:
#                     try:
#                         return self._real_backend[0].hash(to_verify, algo, original_hash)
#                     except _NotSupportedError:
#                         return _bcrypt.checkpw(to_verify, original_hash)
#                 case _HashAlgorithm.ARGON2:
#                     _warnings.warn("Argon2 is still not perfectly supported, expect bugs or other mishaps.",
#                                   category=UserWarning, stacklevel=2)
#                     if Kyber is None:
#                         raise EnvironmentError("Module QuantCrypt is not installed.")
#                     try:
#                         Argon2.Hash(to_verify, original_hash.decode())
#                         return True
#                     except Exception as e:
#                         print(f"Exception occurred: {e}")
#                         return False
#                 case _:
#                     result = self._real_backend[0].hash(to_verify, algo)
#             return result == original_hash
#
#         def encrypt(self, plain_bytes: bytes, cipher_key: _BASIC_KEYTYPE | _BASIC_KEYPAIRTYPE,
#                     padding: _ty.Union[_Sym.Padding, _ASym.Padding, None] = None,
#                     mode_or_strength: _ty.Optional[_Sym.Operation] | _Security = None) -> bytes | dict[_ty.Any, _ty.Any]:
#             """
#             Encrypts the plain bytes using the configuration provided and returns it.
#
#             :param plain_bytes:
#             :param cipher_key:
#             :param padding:
#             :param mode_or_strength:
#             :return:
#             """
#             if self._backend is None or self._real_backend is None:
#                 raise ValueError("Please set a Backend before usage")
#
#             parts = {}
#
#             if cipher_key.cipher_type == _Sym:
#                 if padding and 1:  # isinstance(mode_or_strength, _Security):  # _Sym.Operation
#                     parts = self._real_backend[1].encrypt_sym(plain_bytes, cipher_key, padding, mode_or_strength)
#                 else:
#                     raise ValueError("Please pass a correct padding and mode to use Symmetric encryption.")
#             elif cipher_key.cipher_type == _ASym:
#                 if cipher_key.cipher == _ASym.Cipher.RSA:
#                     parts = self._real_backend[1].encrypt_asym(plain_bytes, cipher_key, padding, mode_or_strength)
#                 elif cipher_key.cipher == _ASym.Cipher.KYBER:
#                     _warnings.warn("Kyber is still not perfectly supported, expect bugs or other mishaps.",
#                                   category=UserWarning, stacklevel=2)
#                     if Kyber is None:
#                         raise EnvironmentError("Module QuantCrypt is not installed.")
#                     parts["ciphertext"] = cipher_key.encrypt(plain_bytes)
#                 else:
#                     raise _NotSupportedError(f"The algorithm '{cipher_key.cipher_type}' cannot be used for encryption")
#
#             if self.auto_pack:
#                 outputs = b''.join(v for k, v in parts.items())
#             else:
#                 outputs = parts
#
#             return outputs
#
#         def decrypt(self, cipher_bytes: bytes | dict, cipher_key: _BASIC_KEYTYPE | _BASIC_KEYPAIRTYPE,
#                     padding: _ty.Union[_Sym.Padding, _ASym.Padding, None] = None,
#                     mode: _ty.Optional[_Sym.Operation] | _Security = None) -> bytes:
#             """
#             Encrypts the cipher bytes using the configuration provided and returns it.
#
#             :param cipher_bytes:
#             :param cipher_key:
#             :param padding:
#             :param mode:
#             :return:
#             """
#             if self._backend is None or self._real_backend is None:
#                 raise ValueError("Please set a Backend before usage")
#
#             result: bytes
#             if repr(cipher_key.cipher_type) == "<class 'aplustools.security.crypto.algorithms.Sym'>":# cipher_key.cipher_type == _Sym:
#                 result = self._real_backend[1].decrypt_sym(cipher_bytes, cipher_key, padding, mode)
#             elif repr(cipher_key.cipher_type) == "<class 'aplustools.security.crypto.algorithms.ASym'>":# cipher_key.cipher_type == _ASym:
#                 if cipher_key.cipher == _ASym.Cipher.RSA:
#                     result = self._real_backend[1].decrypt_asym(cipher_bytes, cipher_key, padding, mode)
#                 elif cipher_key.cipher == _ASym.Cipher.KYBER:
#                     _warnings.warn("Kyber is still not perfectly supported, expect bugs or other mishaps.",
#                                   category=UserWarning, stacklevel=2)
#                     if Kyber is None:
#                         raise EnvironmentError("Module QuantCrypt is not installed.")
#                     result = cipher_key.decrypt(cipher_bytes)
#                 else:
#                     raise _NotSupportedError("DSA and ECC cannot be used for encryption")
#             else:
#                 raise RuntimeError(f"'{cipher_key.cipher_type}' is an invalid cipher type.")
#             return result
#
#         def key_derivation(self, password: bytes, length: int, salt: bytes | None = None,
#                            kdf_type: _KeyDerivation = _KeyDerivation.PBKDF2HMAC,
#                            strength: int = _Security.STRONG) -> bytes:
#             """
#             Derives a key from a password
#
#             :param password:
#             :param length:
#             :param salt:
#             :param kdf_type:
#             :param strength:
#             """
#             if self._backend is None or self._real_backend is None:
#                 raise ValueError("Please set a Backend before usage")
#
#             if kdf_type == _KeyDerivation.ARGON2:
#                 _warnings.warn("Argon2 is still not perfectly supported, expect bugs or other mishaps.",
#                               category=UserWarning, stacklevel=2)
#                 if Kyber is None or Argon2 is None:
#                     raise EnvironmentError("Module QuantCrypt is not installed.")
#                 return Argon2.Key(password).secret_key
#             elif kdf_type == _KeyDerivation.KKDF:
#                 _warnings.warn("KKDF is still not perfectly supported, expect bugs or other mishaps.",
#                               category=UserWarning, stacklevel=2)
#                 if Kyber is None or _KKDF is None:
#                     raise EnvironmentError("Module QuantCrypt is not installed.")
#                 return _KKDF(master=password, key_len=length, num_keys=1)[0]
#             elif kdf_type == _KeyDerivation.BCRYPT:
#                 if salt is None:
#                     salt = _os.urandom([16, 32, 64, 128][strength])
#                 rounds = (100, 400, 800, 1600, 3200)[strength]
#                 if _bcrypt is None:
#                     raise RuntimeError("bcrypt is not installed")
#                 return _bcrypt.kdf(  # type: ignore
#                     password=password,
#                     salt=salt,
#                     desired_key_bytes=length,
#                     rounds=rounds)
#             return self._real_backend[1].key_derivation(password, length, salt, kdf_type, strength)  # type: ignore
#
#         def generate_auth_code(self, auth_type: _MessageAuthenticationCode, cipher_key: _BASIC_KEYTYPE,
#                                data: bytes, strength: int = _Security.STRONG) -> bytes:
#             if self._backend is None or self._real_backend is None:
#                 raise ValueError("Please set a Backend before usage")
#
#             return self._real_backend[1].generate_auth_code(auth_type, cipher_key, data, strength)  # type: ignore
#
#         def key_exchange(self, cipher_key: _BASIC_KEYPAIRTYPE, peer_public_key: bytes | _ty.Any) -> bytes:
#             """Diffie Hellman key exchange"""
#             if self._backend is None or self._real_backend is None:
#                 raise ValueError("Please set a Backend before usage")
#
#             return self._real_backend[1].key_exchange(cipher_key, peer_public_key, "ECDH" if cipher_key.cipher == _ASym.Cipher.ECC else "DH")  # type: ignore
#
#         def sign(self, data: bytes, cipher_key: _BASIC_KEYPAIRTYPE, padding: _ASym.Padding | None = None,
#                  strength: int = _Security.STRONG) -> bytes:
#             if self._backend is None or self._real_backend is None:
#                 raise ValueError("Please set a Backend before usage")
#
#             if cipher_key.cipher == _ASym.Cipher.DILITHIUM:
#                 _warnings.warn("DILITHIUM is still not perfectly supported, expect bugs or other mishaps.",
#                               category=UserWarning, stacklevel=2)
#                 return cipher_key.sign(data)  # type: ignore
#             return self._real_backend[1].sign(data, cipher_key, padding, strength)  # type: ignore
#
#         def sign_verify(self, data: bytes, signature: bytes, cipher_key: _BASIC_KEYPAIRTYPE,
#                         padding: _ASym.Padding | None = None, strength: int = _Security.STRONG) -> bool:
#             if self._backend is None or self._real_backend is None:
#                 raise ValueError("Please set a Backend before usage")
#
#             if cipher_key.cipher == _ASym.Cipher.DILITHIUM:
#                 _warnings.warn("DILITHIUM is still not perfectly supported, expect bugs or other mishaps.",
#                               category=UserWarning, stacklevel=2)
#                 return cipher_key.verify(data, signature)  # type: ignore
#             return self._real_backend[1].sign_verify(data, signature, cipher_key, padding, strength)  # type: ignore
#
#
#     class PasswordManager:
#         """
#         Uses Scrypt as it's hashing function due to its stronger resistance to GPU and ASIC attacks and to better protect
#         against evolving attack vectors.
#         """
#         def __init__(self, backend: Backend) -> None:
#             self._crypt: CoreCrypt = CoreCrypt(backend=backend)
#
#         def hash_password(self, password: str, kdf: _KeyDerivation = _KeyDerivation.Scrypt, strength: int = _Security.STRONG) -> bytes:
#             salt = _os.urandom((16, 32, 64, 128)[strength])
#             return salt + self._crypt.key_derivation(password.encode(), 64, salt=salt, kdf_type=kdf, strength=strength)
#
#         def verify_password(self, password: str, hashed_password: bytes, kdf: _KeyDerivation = _KeyDerivation.Scrypt, strength: int = _Security.STRONG) -> bool:
#             salt_length = (16, 32, 64, 128)[strength]
#             salt, hashed_password = hashed_password[:salt_length], hashed_password[salt_length:]
#             derived_key = self._crypt.key_derivation(password.encode(), 64, salt=salt, kdf_type=kdf, strength=strength)
#             return derived_key == hashed_password
#
#
#     class DataEncryptor:
#         """
#         Uses AES X-bit encryption which is very secure if used with a sufficient key size like 256.
#         """
#         def __init__(self, password_key_or_key_size: _ty.Literal[128, 192, 256] | bytes | tuple[_ty.Literal[128, 192, 256], str] = 256,
#                      backend: Backend = Backend.cryptography) -> None:
#             self._crypt: CoreCrypt = CoreCrypt(backend=backend)
#             self._key: _BASIC_KEYTYPE = _Sym.Cipher.AES.new_key(password_key_or_key_size)
#
#         def get_key(self) -> bytes:
#             return self._key.get_key()
#
#         def encrypt_data(self, data: bytes, padding: _Sym.Padding = _Sym.Padding.PKCS7, mode: _Sym.Operation = _Sym.Operation.CBC) -> bytes:
#             encrypted_data: bytes = self._crypt.encrypt(data, self._key, padding, mode)
#             return encrypted_data
#
#         def decrypt_data(self, encrypted_data: bytes, padding: _Sym.Padding = _Sym.Padding.PKCS7, mode: _Sym.Operation = _Sym.Operation.CBC) -> bytes:
#             return self._crypt.decrypt(encrypted_data, self._key, padding, mode)
#
#
#     class DigitalSigner:
#         """
#         Uses ECC signatures with the SECP256R1 curve, as it provides strong security against potential future threats
#         from quantum computers.
#         """
#         def __init__(self, private_key: bytes | None = None, backend: Backend = Backend.cryptography) -> None:
#             self._crypt: CoreCrypt = CoreCrypt(backend=backend)
#             self._key_pair: _BASIC_KEYPAIRTYPE = _ASym.Cipher.ECC.ecdsa_key(_ASym.Cipher.ECC.Curve.SECP256R1, private_key)
#
#         def get_private_key(self) -> bytes:
#             return self._key_pair.get_private_bytes()
#
#         def sign_data(self, data: bytes, padding: _ty.Union[_ASym.Padding, None] = _ASym.Padding.PSS, strength: int = _Security.STRONG) -> bytes:
#             return self._crypt.sign(data, self._key_pair, padding, strength)
#
#         def verify_signature(self, data: bytes, signature: bytes, padding: _ty.Union[_ASym.Padding, None] = _ASym.Padding.PSS, strength: int = _Security.STRONG) -> bool:
#             return self._crypt.sign_verify(data, signature, self._key_pair, padding, strength)
