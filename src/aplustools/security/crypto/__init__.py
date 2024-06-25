from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms
from .hash import HashAlgorithm, _SHA2, _SHA3, _BLAKE2
from .keys import _BASIC_KEY_TYPE, _BASIC_KEYPAIR_TYPE, Kyber, Argon2
from .algorithms import *
from .. import Security

from typing import Any
import warnings
import os

import bcrypt


class AdvancedCryptography:
    """Makes security easy.
    Remember that easy_hash appends one byte to the start of the hash for identification,
    except for argon2, which already has an identifier."""
    _hash_algorithm_map: dict[HashAlgorithm, type] = {
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
    def _create_digest(self, algo, digest_size: Optional[int] = None):
        if algo in (HashAlgorithm.SHA3.SHAKE128, HashAlgorithm.SHA3.SHAKE256):
            if digest_size is None:
                digest_size = 32  # default size in bytes (256 bits)
            digest = hashes.Hash(self._hash_algorithm_map[algo](digest_size))
        else:
            digest = hashes.Hash(self._hash_algorithm_map[algo]())
        return digest

    def hash(self, to_hash: bytes, algo: int) -> str | bytes:
        """
        Hashes to_hash using the provided algorithm and returns it.

        :param to_hash:
        :param algo:
        :return:
        """
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
        """
        Verifies that original_hash was generated from to_verify, optionally a specific algorithm can be specified.

        :param to_verify:
        :param original_hash:
        :param algo:
        :return:
        """
        if self._easy_hash and algo is not None:
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
                digest = hashes.Hash(self._hash_algorithm_map[algo]())

        digest.update(to_verify)
        return digest.finalize() == original_hash

    def encrypt(self, plain_bytes: bytes, cipher_key: _BASIC_KEY_TYPE | _BASIC_KEYPAIR_TYPE,
                padding: Optional[SymPadding | ASymPadding] = None,
                mode_or_strength: Optional[SymOperation] | Security = None) -> bytes | dict:
        """
        Encrypts the plain bytes using the configuration provided and returns it.

        :param plain_bytes:
        :param cipher_key:
        :param padding:
        :param mode_or_strength:
        :return:
        """
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
                warnings.warn(f"RSA is insecure and should be migrated away from, consider using other encryption "
                              f"algorithms or using ECC/DSA for Hybrid encryption and key exchange.")
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
                cipher_key: type[_BASIC_KEY_TYPE | _BASIC_KEYPAIR_TYPE], mode: Optional[SymOperation],
                padding: SymPadding | ASymPadding):
        if cipher_key.cipher == "RSA":
            warnings.warn(f"RSA is insecure and should be migrated away from, consider using other encryption "
                          f"algorithms or using ECC/DSA for Hybrid encryption and key exchange.")

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
        """Diffie Hellman key exchange"""
        if algorithm == DiffieHellmanAlgorithm.ECDH:
            return private_key.exchange(ec.ECDH(), peer_public_key)
        elif algorithm == DiffieHellmanAlgorithm.DH:
            return private_key.exchange(peer_public_key)
        else:
            raise ValueError(f"Key exchange is not supported for the algorithm index '{algorithm}'")

    @staticmethod
    def sign():
        if cipher_key.cipher == "RSA":
            warnings.warn(f"RSA is insecure and should be migrated away from, consider using other encryption "
                          f"algorithms or using ECC/DSA for Hybrid encryption and key exchange.")

    @staticmethod
    def sign_verify():
        if cipher_key.cipher == "RSA":
            warnings.warn(f"RSA is insecure and should be migrated away from, consider using other encryption "
                          f"algorithms or using ECC/DSA for Hybrid encryption and key exchange.")


if __name__ == "__main__":
    key = SymCipher.AES.key(128)
    print(key)
    ac = AdvancedCryptography()
    cipher = ac.encrypt("Hello World".encode(),
                        key, SymPadding.PKCS7,
                        SymOperation.CBC)
    print(cipher)

    rsa_key = ASymCipher.KYBER.key()
    cipher2 = ac.encrypt("HELL".encode(), rsa_key)
    print(cipher2)
    input()
