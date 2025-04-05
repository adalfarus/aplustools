from aplustools import security

ac = security.crypto.AdvancedCryptography()
ac.set_backend(security.crypto.backends.Backend.pycryptodomex)
key = security.crypto.algorithms.Sym.Cipher.Salsa20.key(b"\xa1\x07']\x9bX\xf5\x8d\x01.\x8b\xf4D\x7fF\xb4\x81\xddt\x8b(\xa4d\x86/>\x98\xd0_\x02b[")
plaintext = b"Hello from Salsa20"
ciphertext = ac.encrypt(plaintext, key, 1, None)
decrypted = ac.decrypt(ciphertext, key, 1, None)
print(decrypted)
