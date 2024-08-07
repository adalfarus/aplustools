from aplustools.security.crypto._pycrypto.keys import _ChaCha20_KEY, encrypt_sym, decrypt_sym, Sym, ASym
from aplustools.security import Security, RiskLevel
from aplustools.security.crypto.algorithms import HashAlgorithm


print(f"{str(Sym.Padding.ANSIX923)}")
print(Security.BASIC)
print(RiskLevel.KNOWN_UNSAFE_NOT_RECOMMENDED.desc)
print(HashAlgorithm.SHA2.SHA512)
print(type(HashAlgorithm.ARGON2))


def tes_advanced_cryptography():
    cipher_key = _ChaCha20_KEY()
    plain_text = b"Your plaintext message"
    encrypted_data = encrypt_sym(plain_text, cipher_key, padding=Sym.Padding.ANSIX923, mode_id=Sym.Operation.CBC)

    decrypted_data = decrypt_sym(encrypted_data, cipher_key, padding=Sym.Padding.ANSIX923, mode_id=Sym.Operation.CBC)

    assert decrypted_data == plain_text


# Run the test
tes_advanced_cryptography()
