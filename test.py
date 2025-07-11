"""Test"""
from aplustools.security.crypto.algos import Sym, Asym, HashAlgorithm, KeyDerivationFunction
from aplustools.security.crypto import set_backend, Backend
import os

from aplustools.security.crypto.exceptions import NotSupportedError

set_backend()  # Uses Backend.std_lib

# MD5
h = HashAlgorithm.MD5.hash(b"hello world")
print("MD5:", h.hex())
print("Verify:", HashAlgorithm.MD5.verify(b"hello world", h))
print("Std-Verify:", HashAlgorithm.std_verify(b"hello world", h))

# SHA1
h = HashAlgorithm.SHA1.hash(b"hello world")
print("SHA1:", h.hex())
print("Verify:", HashAlgorithm.SHA1.verify(b"hello world", h))
print("Std-Verify:", HashAlgorithm.std_verify(b"hello world", h))

# SHA256
h = HashAlgorithm.SHA2.SHA256.hash(b"hello world")
print("SHA256:", h.hex())
print("Verify:", HashAlgorithm.SHA2.SHA256.verify(b"hello world", h))
print("Std-Verify:", HashAlgorithm.std_verify(b"hello world", h))

# SHA3-256
h = HashAlgorithm.SHA3.SHA256.hash(b"hello world")
print("SHA3-256:", h.hex())
print("Verify:", HashAlgorithm.SHA3.SHA256.verify(b"hello world", h))
print("Std-Verify:", HashAlgorithm.std_verify(b"hello world", h))

# SHAKE128 (8 bytes)
h = HashAlgorithm.SHA3.SHAKE128.hash(b"hello", 8)
print("SHAKE128:", h.hex())
print("Verify:", HashAlgorithm.SHA3.SHAKE128.verify(b"hello", h))
print("Std-Verify:", HashAlgorithm.std_verify(b"hello", h))

# BLAKE2s (8 bytes)
h = HashAlgorithm.BLAKE2.BLAKE2s.hash(b"hello", 8)
print("BLAKE2s:", h.hex())
print("Verify:", HashAlgorithm.BLAKE2.BLAKE2s.verify(b"hello", h))
print("Std-Verify:", HashAlgorithm.std_verify(b"hello", h))

# RIPEMD160 (if emulated)
try:
    h = HashAlgorithm.RIPEMD160.hash(b"hello")
    print("RIPEMD160:", h.hex())
    print("Verify:", HashAlgorithm.RIPEMD160.verify(b"hello", h))
    print("Std-Verify:", HashAlgorithm.std_verify(b"hello", h))
except Exception as e:
    print("RIPEMD160 unsupported in std_lib:", e)

password = b"my-password"
salt = os.urandom(16)

print("PBKDF2HMAC:", KeyDerivationFunction.PBKDF2HMAC.derive(password, salt=salt).hex())
print("PBKDF1    :", KeyDerivationFunction.PBKDF1.derive(password, salt=salt, length=16).hex())
print("Scrypt    :", KeyDerivationFunction.Scrypt.derive(password, salt=salt, length=16).hex())
print("HKDF      :", KeyDerivationFunction.HKDF.derive(password, salt=salt).hex())
print("ConcatKDF :", KeyDerivationFunction.ConcatKDF.derive(password, otherinfo=b"my-info").hex())


set_backend([
    Backend.cryptography_alpha,  # Currently only hashes like SHA3
    Backend.quantcrypt,          # To enable post-quantum cryptography
    Backend.argon2_cffi,         # Required for Argon2
    Backend.bcrypt,              # Required for BCrypt
    Backend.std_lib              # Fallback
])


# Hash a password/message using Argon2
hashed = HashAlgorithm.ARGON2.hash(b"Ha", os.urandom(16))
print("\nArgon2 Hash:", hashed.decode())

# Verify the hash
is_valid = HashAlgorithm.ARGON2.verify(b"Ha", hashed)
print("Argon2 Valid:", is_valid)

try:
    print("Std-Verify", HashAlgorithm.std_verify(b"Ha", hashed, fallback_algorithm="argon2", text_ids=False))  # Std-Verify can't decode special algos like argon2 or bcrypt
except NotSupportedError:
    print("Std-Verify failed")

# Hash a password with BCrypt
bcrypt_hash = HashAlgorithm.BCRYPT.hash(b"my-secret-password")
print("BCrypt Hash:", bcrypt_hash.decode())

# Verify the password against the hash
is_valid = HashAlgorithm.BCRYPT.verify(b"my-secret-password", bcrypt_hash)
print("BCrypt Valid:", is_valid)

# Derive a key using Argon2 KDF
derived_key = KeyDerivationFunction.ARGON2.derive(b"my-password", salt=os.urandom(16))
print("Argon2 Derived Key:", derived_key.hex())

# Derive a key using BCrypt KDF
bcrypt_key = KeyDerivationFunction.BCRYPT.derive(b"my-password", salt=os.urandom(16))
print("BCrypt Derived Key:", bcrypt_key.hex())


# Recipient generates a keypair
recipient_key = Asym.Cipher.KYBER.keypair.new("kyber1024")

# Extract public key from recipient and share it with the sender
pub_key_bytes = recipient_key.encode_public_key()
if pub_key_bytes is None:  # Keys can't be regenerated and try: except: takes more space; Can only happen if you do not pass one of the keys when using .decode( ... )
    raise ValueError("recipient_key has no public key")

# Sender receives the public key and creates a key object with only the public key
sender_key = Asym.Cipher.KYBER.keypair.decode("kyber1024", public_key=pub_key_bytes)
# Sender encapsulates a shared secret for the recipient
ciphertext, shared_secret_sender = sender_key.encapsulate()

# Recipient decapsulates to recover the shared secret
shared_secret_recipient = recipient_key.decapsulate(ciphertext)

print("\n=== Kyber KEM Flow ===")
print(f"Ciphertext             : {ciphertext.hex()}")
print(f"Sender Shared Secret   : {shared_secret_sender.hex()}")
print(f"Recipient Shared Secret: {shared_secret_recipient.hex()}")
assert shared_secret_sender == shared_secret_recipient, "Shared secrets do not match!"


# Generate the signing keypair (private + public)
sign_key = Asym.Cipher.DILITHIUM.keypair.new("dilithium5")

# Sign a message using the private key
message = b"Hello World"
signature = sign_key.sign(message)

# Extract and share only the public key
pub_key_bytes = sign_key.encode_public_key()
if pub_key_bytes is None:  # Keys can't be regenerated and try: except: takes more space; Can only happen if you do not pass one of the keys when using .decode( ... )
    raise ValueError("sign_key has no public key")

# Create a new key object with only the public key for verification
verify_key = Asym.Cipher.DILITHIUM.keypair.decode("dilithium5", public_key=pub_key_bytes)
# Verify the signature using the public key
is_valid = verify_key.sign_verify(message, signature)

print("\n=== Dilithium Signature Flow ===")
print(f"Signature     : {signature.hex()}")
print(f"Signature Valid? {is_valid}")
assert is_valid, "Signature verification failed!"
