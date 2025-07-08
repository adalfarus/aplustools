from src.aplustools.security import crypto

crypt = crypto.CoreCrypt()
crypt.set_backend(crypto.backends.Backend.pycryptodomex)
key = crypto.algorithms.Sym.Cipher.Salsa20.key(b"\xa1\x07']\x9bX\xf5\x8d\x01.\x8b\xf4D\x7fF\xb4\x81\xddt\x8b(\xa4d\x86/>\x98\xd0_\x02b[")
plaintext = b"Hello from Salsa20"
ciphertext = crypt.encrypt(plaintext, key, 1, None)
decrypted = crypt.decrypt(ciphertext, key, 1, None)
print(decrypted)

crypt.hash(b"", crypto.algorithms.HashAlgorithm.MD2)
