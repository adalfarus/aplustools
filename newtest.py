import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from aplustools.security.crypto import set_backend, Backend
from aplustools.security.crypto.algos import Asym

# Set up backends (important!)
set_backend([
    Backend.quantcrypt,   # ✅ correct
    Backend.std_lib
])

# --- Key Exchange using Kyber ---
# Recipient creates keypair
recipient_keypair = Asym.Cipher.KYBER.keypair.new("kyber1024")
recipient_public = recipient_keypair.encode_public_key()

# Sender uses recipient's public key to generate shared secret
sender_key = Asym.Cipher.KYBER.keypair.decode("kyber1024", public_key=recipient_public)
ciphertext, shared_key_sender = sender_key.encapsulate()

# Recipient decapsulates ciphertext to recover the shared key
shared_key_recipient = recipient_keypair.decapsulate(ciphertext)

assert shared_key_sender == shared_key_recipient, "Key exchange failed!"

# --- Encrypt Message using AES-GCM ---
aes_key = shared_key_sender[:32]  # AES-256
aesgcm = AESGCM(aes_key)

nonce = os.urandom(12)  # Required 96-bit nonce for AES-GCM
message = b"hello quantum world"

ciphertext = aesgcm.encrypt(nonce, message, associated_data=None)
print(f"\nEncrypted message: {ciphertext.hex()}")

# --- Decrypt on recipient side ---
aesgcm_recipient = AESGCM(shared_key_recipient[:32])
decrypted = aesgcm_recipient.decrypt(nonce, ciphertext, associated_data=None)
print(f"Decrypted message: {decrypted.decode()}")



from cryptography.hazmat.primitives.asymmetric import rsa
from scrapped.cert import Key, Name, CertificateAuthority

# Generate an RSA key and wrap it
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
wrapped_key = Key(private_key)

# Create CA and issue a cert
ca_name = Name("QuantumCA", organization="Aplus Labs", country="US")
ca = CertificateAuthority.self_signed(ca_name, wrapped_key)

user_key = Key(rsa.generate_private_key(public_exponent=65537, key_size=2048)).public_key()
user_name = Name("user@example.com", organization="Aplus Users", country="US")
cert = ca.issue(user_name, user_key)

print(f"User certificate issued to: {cert.name}")  # .subject.rfc4514_string()
