"""Test"""
from aplustools.security.crypto.algos import Sym, ASym, HashAlgorithm
from aplustools.security.crypto import set_backend, Backend, hash

set_backend(Backend.cryptography)

key1 = Sym.Cipher.Salsa20.key((256, "mypassword"))
key2 = Sym.Cipher.Salsa20.key(b"\xa1\x07']\x9bX\xf5\x8d\x01.\x8b\xf4D\x7fF\xb4\x81\xddt\x8b(\xa4d\x86/>\x98\xd0_\x02b[")

plaintext = b"Hello from Salsa20"
ciphertext = key2.encrypt(plaintext, key, 1, None)
decrypted = key2.decrypt(ciphertext, key, 1, None)
print(decrypted)

hash(b"", HashAlgorithm.MD2)

# OR
HashAlgorithm.MD2.hash( ... )  # Pass more advanced values
