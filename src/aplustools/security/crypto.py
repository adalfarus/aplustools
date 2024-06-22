from comtypes.automation import _
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import rsa, padding as _padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.kdf.concatkdf import ConcatKDFHash
from cryptography.hazmat.primitives.kdf.x963kdf import X963KDF
from cryptography.hazmat.primitives import hmac, cmac
from typing import Literal, Tuple, Optional, IO, Union
from pathlib import Path
import warnings
import secrets
import bcrypt
import os


from aplustools.security.passwords import SpecificPasswordGenerator, PasswordFilter
from aplustools.io.environment import safe_remove, strict
from aplustools.data import enum_auto
from aplustools.package import EasyAttribute
from tempfile import mkdtemp

from traits.trait_types import self

try:
    from quantcrypt.kem import Kyber
    from quantcrypt.cipher import KryptonKEM
    from quantcrypt.kdf import Argon2
except ImportError:
    Kyber = KryptonKEM = Argon2 = None


class Security:
    """Baseclass for different security levels"""
    WEAK = enum_auto()
    AVERAGE = enum_auto()
    STRONG = enum_auto()
    SUPERSTRONG = enum_auto()


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


class _AESKEY:
    def __init__(self, key_size: Literal[128, 192, 256], key: Optional[bytes | str]):
        self._original_key = key if key is not None else secrets.token_hex(key_size // 8)
        if isinstance(self._original_key, bytes):
            if len(self._original_key) * 8 != float(key_size):
                raise ValueError(f"Key size of given key ({len(self._original_key) * 8}) "
                                 f"doesn't match the specified key size ({key_size})")
            self._key = self._original_key
        else:
            self._key = PBKDF2HMAC(algorithm=hashes.SHA3_512(), length=32, salt=os.urandom(64), iterations=800_000,
                                   backend=default_backend()).derive(self._original_key.encode())

    def get_key(self) -> bytes:
        return self._key

    def get_original_key(self) -> str:
        return self._original_key

    def __bytes__(self):
        return self._key

    def __str__(self):
        return self._key.hex()

    def __repr__(self):
        return str(self)


class _AES:  # Advanced Encryption Standard
    @staticmethod
    def key(key_size: Literal[128, 192, 256], key: Optional[bytes | str] = None):
        return _AESKEY(key_size, key)


def _create_aes_subclass(key_size: Literal[128, 192, 256]):
    """Helper method to create a subclass with a specific key size."""
    subclass_name = f"AES{key_size}"

    class SubClass(_AES):
        @classmethod
        def key(cls, key: Optional[bytes | str] = None):
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
    ECB = enum_auto()  # Electronic Codebook
    CBC = enum_auto()  # Cipher Block Chaining
    CFB = enum_auto()  # Cipher Feedback
    OFB = enum_auto()  # Output Feedback
    CTR = enum_auto()  # Counter
    GCM = enum_auto()  # Galois/Counter Mode
    OCB = enum_auto()  # Offset Codebook Mode


class SymPadding:
    """Padding Schemes"""
    PKCS7 = enum_auto()
    ANSIX923 = enum_auto()
    ISO7816 = enum_auto()


class _RSAKEYPAIR:
    """You need to give a pem private key if it's in bytes"""
    public_exponent = 65537

    def __init__(self, key_size: Literal[512, 768, 1024, 2048, 3072, 4096, 8192, 15360],
                 private_key: Optional[bytes | str | rsa.RSAPrivateKey] = None):
        self._private_key = self._load_pem_private_key(private_key) \
            if private_key is not None else rsa.generate_private_key(public_exponent=self.public_exponent,
                                                                     key_size=key_size)
        if self._private_key.key_size != key_size:
            raise ValueError(f"Key size of given private key ({self._private_key.key_size}) "
                             f"doesn't match the specified key size ({key_size})")
        self._public_key = self._private_key.public_key()

    @staticmethod
    def _load_pem_private_key(key_to_load: bytes | str | rsa.RSAPrivateKey) -> rsa.RSAPrivateKey:
        if isinstance(key_to_load, (bytes, str)):
            if isinstance(key_to_load, str):
                key_to_load = bytes(key_to_load, "utf-8")
            key_to_load = serialization.load_pem_private_key(key_to_load, None, default_backend())
        return key_to_load

    def get_private_key(self) -> rsa.RSAPrivateKey:
        return self._private_key

    def get_public_key(self) -> rsa.RSAPublicKey:
        return self._public_key

    def get_private_bytes(self) -> bytes:
        return self._private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )

    def get_public_bytes(self) -> bytes:
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


class _RSA:  # Rivest-Shamir-Adleman
    @staticmethod
    def key(key_size: Literal[512, 768, 1024, 2048, 3072, 4096, 8192, 15360],
            private_key: Optional[bytes | str | rsa.RSAPrivateKey] = None):
        return _RSAKEYPAIR(key_size, private_key)


def _create_rsa_subclass(key_size: Literal[512, 768, 1024, 2048, 3072, 4096, 8192, 15360]):
    """Helper method to create a subclass with a specific key size."""
    """Helper method to create a subclass with a specific key size."""
    subclass_name = f"RSA{key_size}"

    class SubClass(_RSA):
        @classmethod
        def key(cls, private_key: Optional[bytes | str | rsa.RSAPrivateKey] = None):
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


class _ECC:  # Elliptic Curve Cryptography
    ECDSA = enum_auto()  # Elliptic Curve Digital Signature Algorithm
    ECDH = enum_auto()  # Elliptic Curve Diffie-Hellman
    Ed25519 = enum_auto()
    Ed448 = enum_auto()


class ASymCipher:
    """Asymmetric Encryption"""
    RSA = _RSA
    DSA = enum_auto()  # Digital Signature Algorithm
    ECC = _ECC
    KYBER = enum_auto()


class ASymPadding:
    """Asymmetric Encryption Padding Schemes"""
    PKCShash1v1dot5 = enum_auto()  # Older padding scheme for RSA
    OAEP = enum_auto()  # Optimal Asymmetric Encryption Padding
    PSS = enum_auto()  # Probabilistic Signature Scheme


class KeyDevivation:
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

    def __init__(self, auto_pack: bool = True, easy_hash: bool = True):
        self._auto_pack = auto_pack
        self._easy_hash = easy_hash

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

    def encrypt(self, plain_bytes: bytes, cipher: SymCipher | ASymCipher, mode: Optional[SymOperation],
                padding: SymPadding | ASymPadding):
        match cipher:
            case ASymCipher.RSA.RSA512:
                return

    def decrypt(self, cipher_bytes: bytes, cipher: SymCipher | ASymCipher, mode: Optional[SymOperation],
                padding: SymPadding | ASymPadding):
        pass

    def KDF(self, password: bytes, length: int, salt: bytes = None, key_dev_type: KeyDevivation = KeyDevivation.PBKDF2HMAC,
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
            case key_dev_type.PBKDF2HMAC:
                iter_mult = {"weak": 1, "average": 4, "strong": 8}[strength]
                kdf = PBKDF2HMAC(
                    algorithm=hash_type(),
                    length=length,
                    salt=salt,
                    iterations=100_000 * iter_mult,
                    backend=default_backend()
                )
            case KeyDevivation.Scrypt:
                n, r, p = {
                    "weak": (2 ** 14, 8, 1),
                    "average": (2**16, 8, 2),
                    "strong": (2**18, 8, 4)
                }[strength]
                kdf = Scrypt(
                    salt=salt,
                    length=length,
                    n=n,
                    r=r,
                    p=p,
                    backend=default_backend()
                )
            case KeyDevivation.HKDF:
                kdf = HKDF(
                    algorithm=hash_type(),
                    length=length,
                    salt=salt,
                    info=b"",
                    backend=default_backend()
                )
            case KeyDevivation.X963:
                kdf = X963KDF(
                    algorithm=hash_type(),
                    length=length,
                    sharedinfo=None,
                    backend=default_backend()
                )
            case KeyDevivation.ConcatKDF:
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


# AC = AdvancedCryptography()
# HA = HashAlgorithm
# print(AC.hash("HelloWorld".encode(), HA.SHA3.SHAKE128))
# input(AC.hash_verify("HELL".encode(), AC.hash("HELL".encode(), HA.SHA3.SHA224)))
# print(AC.hash_verify("Hello World".encode(), AC.hash("Hello World".encode(), HA.SHA3.SHA224), HA.SHA3.SHA224))
# print(AC.hash_verify("Hello World".encode(), AC.hash("Hello World".encode(), HA.BCRYPT), HA.BCRYPT))
# print(AC.hash_verify("Zel".encode(), AC.hash("Zel".encode(), HA.ARGON2), HA.ARGON2))
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

        tag_len = int.from_bytes(data[iv_end:iv_end+1])
        tag_start = iv_end+1
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
                _padding.OAEP(
                    mgf=_padding.MGF1(algorithm=hashes.SHA256()),
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
            _padding.OAEP(
                mgf=_padding.MGF1(algorithm=hashes.SHA256()),
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
    def kyber_encrypt(public_key: bytes, plaintext_path_or_file: Union[bytes, IO, Path],
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
        krypton.encrypt(public_key, plaintext_file, ciphertext_file)

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

    @staticmethod
    def kyber_decrypt(secret_key: bytes, ciphertext_path_or_file: Union[bytes, IO, Path],
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
        krypton.decrypt_to_file(secret_key, ciphertext_file, plaintext_file)

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

    @staticmethod
    def generate_secure_password(length: int = 24):
        return SpecificPasswordGenerator().generate_ratio_based_password_v3(length, filter_=PasswordFilter(exclude_similar=True))

    @staticmethod
    def hash(password: str, hash_type: Literal["argon2"] = "argon2") -> str:
        """
        Hashes a password using Argon2.
        """
        return Argon2.Hash(password).public_hash

    @staticmethod
    def hash_verify(password: str, hash: str, hash_type: Literal["argon2"] = "argon2") -> bool:
        """
        Verifies a password against an Argon2 hash.
        """
        if Kyber is None:
            raise EnvironmentError("Module QuantCrypt is not installed.")
        try:
            Argon2.Hash(password, hash)
            return True
        except Exception as e:
            print(f"Exception occurred: {e}")
            return False


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
