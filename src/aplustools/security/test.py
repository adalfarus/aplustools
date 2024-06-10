import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

def encrypt_seed(seed, key):
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_seed = padder.update(seed) + padder.finalize()
    encrypted_seed = iv + encryptor.update(padded_seed) + encryptor.finalize()

    return encrypted_seed

def decrypt_seed(encrypted_seed, key):
    iv = encrypted_seed[:16]
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_seed = decryptor.update(encrypted_seed[16:]) + decryptor.finalize()

    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    seed = unpadder.update(padded_seed) + unpadder.finalize()

    return seed

# Test the encryption and decryption
def test_encryption_decryption():
    key = os.urandom(32)  # 256-bit key
    seed = os.urandom(32)  # 256-bit seed

    encrypted_seed = encrypt_seed(seed, key)
    decrypted_seed = decrypt_seed(encrypted_seed, key)

    assert seed == decrypted_seed, "Decryption did not return the original seed"
    print("Encryption and decryption test passed!")

if __name__ == "__main__":
    test_encryption_decryption()
