from aplustools.security.crypto.algorithms import _ECCCurve, MessageAuthenticationCode, KeyDerivation
from aplustools.security.crypto import AdvancedCryptography, Sym, ASym, algorithm_names
from aplustools.security.crypto.backends import Backend
from aplustools.security.crypto.exceptions import NotSupportedError
from aplustools.security import Security

from aplustools.security.crypto import DataEncryptor, DigitalSigner, PasswordManager


class TestCrypto:
    def test_advanced_cryptography(self):
        try:
            test_data = b"Hello World" * 4
            for backend, name in zip((Backend.cryptography, Backend.pycryptodomex), ("cryptography", "pycryptodomex")):
                length = int(((222 / 2) - (len(name) / 2) - 1) // 2)
                print("#" * 222, "\n", "# " * length, name, " #" * length, "\n")
                ac = AdvancedCryptography(backend=backend)

                for id, hash in algorithm_names.items():
                    for force_text_ids in (True, False):
                        val = False
                        try:
                            h = ac.hash(test_data, id, force_text_ids=force_text_ids)
                            v = ac.hash_verify(test_data, h, forced_text_ids=force_text_ids)
                        except NotSupportedError:
                            h, v = None, False
                            val = True
                        if v and not val:
                            message = 'PASSING'
                        elif not v and val:
                            message = 'NOT SUPPORTED'
                        else:
                            message = 'ERROR'
                        print(f"{hash}, [{message}] -> {h}")

                for kdf, kdf_name in zip(
                        (KeyDerivation.PBKDF2HMAC, KeyDerivation.HKDF, KeyDerivation.X963, KeyDerivation.Scrypt,
                         KeyDerivation.ConcatKDF, KeyDerivation.PBKDF1, KeyDerivation.KMAC128, KeyDerivation.KMAC256,
                         KeyDerivation.ARGON2, KeyDerivation.KKDF, KeyDerivation.BCRYPT),
                        ("PBKDF2HMAC", "HKDF", "X963", "Scrypt", "ConcatKDF", "PBKDF1", "KMAC128", "KMAC256", "ARGON2",
                         "KKDF",
                         "BCRYPT")):
                    for setting, setting_name in zip(
                            (Security.BASIC, Security.AVERAGE, Security.STRONG, Security.SUPER_STRONG),
                            ("BASIC", "AVERAGE", "STRONG", "SUPER STRONG")):
                        try:
                            key = ac.key_derivation(test_data, 64 if kdf_name != "PBKDF1" else 20, kdf_type=kdf,
                                                    strength=setting)
                            print(f"{kdf_name} [{setting_name}] {key}")
                        except NotSupportedError:
                            print(f"{kdf_name} [{setting_name}] UNSUPPORTED")

                for auth_code, auth_code_name in zip(
                        (MessageAuthenticationCode.HMAC, MessageAuthenticationCode.CMAC, MessageAuthenticationCode.KMAC128,
                         MessageAuthenticationCode.KMAC256, MessageAuthenticationCode.Poly1305),
                        ("HMAC", "CMAC", "KMAC128", "KMAC256", "Poly1305")):
                    for setting, setting_name in zip(
                            (Security.BASIC, Security.AVERAGE, Security.STRONG, Security.SUPER_STRONG),
                            ("BASIC", "AVERAGE", "STRONG", "SUPER STRONG")):
                        mac_key = Sym.Cipher.AES.key(256)
                        try:
                            auth_code_result = ac.generate_auth_code(auth_code, mac_key, test_data, setting)
                            print(f"{auth_code_name} [{setting_name}] {mac_key} -> {auth_code_result}")
                        except NotSupportedError as e:
                            print(f"{auth_code_name} [{setting_name}] UNSUPPORTED - {str(e)}")

                sym_ciphers = [
                    ("AES", Sym.Cipher.AES, [128, 192, 256]),
                    ("ChaCha20", Sym.Cipher.ChaCha20, [256]),
                    ("TripleDES", Sym.Cipher.TripleDES, [192]),
                    ("Blowfish", Sym.Cipher.Blowfish, [128, 256]),
                    ("CAST5", Sym.Cipher.CAST5, [40, 128]),
                    ("ARC4", Sym.Cipher.ARC4, [128]),
                    ("Camellia", Sym.Cipher.Camellia, [128, 192, 256]),
                    ("IDEA", Sym.Cipher.IDEA, [128]),
                    ("SEED", Sym.Cipher.SEED, [128]),
                    ("SM4", Sym.Cipher.SM4, [128]),
                    ("DES", Sym.Cipher.DES, [64]),
                    ("ARC2", Sym.Cipher.ARC2, [40, 64, 128]),
                    ("Salsa20", Sym.Cipher.Salsa20, [128, 256])
                ]
                for cipher_name, cipher_class, key_sizes in sym_ciphers:
                    print(f"-------------------------- {cipher_name} --------------------------", end="")
                    for key_size in key_sizes:
                        try:
                            sym_key = cipher_class.key(key_size) if len(key_sizes) > 1 else cipher_class.key()
                        except NotSupportedError:
                            print("\nUNSUPPORTED")
                            break
                        if cipher_name in {"ARC4", "ChaCha20", "ARC2"}:
                            # Stream ciphers do not use padding or modes like block ciphers
                            try:
                                cipher = ac.encrypt(test_data, sym_key, None, None)
                                plain = ac.decrypt(cipher, sym_key, None, None)
                                print(f"\n{key_size}B {sym_key} -> {cipher} -> {plain}", end="")
                            except NotSupportedError:
                                print(f"\n{key_size}B UNSUPPORTED", end="")
                        else:
                            for padding in (Sym.Padding.PKCS7, Sym.Padding.ANSIX923):
                                for mode in (Sym.Operation.CBC, Sym.Operation.CTR, Sym.Operation.ECB,
                                             Sym.Operation.OFB, Sym.Operation.GCM, Sym.Operation.CFB):
                                    try:
                                        sym_cipher = ac.encrypt(test_data, sym_key, padding, mode)
                                        sym_plain = ac.decrypt(sym_cipher, sym_key, padding, mode)
                                        print(f"\n{key_size}B [{padding, mode}] {sym_key} -> {sym_cipher} -> {sym_plain}",
                                              end="")
                                    except NotSupportedError:
                                        print(f"\n{key_size}B [{padding, mode}] UNSUPPORTED", end="")
                    print("\n----------------------------------------------------------------------------------")

                asym_ciphers = [
                    ("RSA", ASym.Cipher.RSA, [512, 768, 1024, 2048, 3072, 4096]),
                    ("DSA", ASym.Cipher.DSA, [1024, 2048, 3072]),
                    ("ECC ECDSA", ASym.Cipher.ECC,
                     [_ECCCurve.SECP192R1, _ECCCurve.SECP224R1, _ECCCurve.SECP256K1, _ECCCurve.SECP256R1,
                      _ECCCurve.SECP384R1,
                      _ECCCurve.SECP521R1]),
                    ("KYBER", ASym.Cipher.KYBER, [None]),
                    ("DILITHIUM", ASym.Cipher.DILITHIUM, [None])
                ]
                for cipher_name, cipher_class, key_params in asym_ciphers:
                    print(f"-------------------------- {cipher_name} --------------------------", end="")
                    for param in key_params:
                        try:
                            if cipher_name == "ECC ECDSA":
                                key = cipher_class.ecdsa_key(param)
                            elif cipher_name in ["KYBER", "DILITHIUM"]:
                                key = cipher_class.key()
                            else:
                                key = cipher_class.key(param)

                            peer_key = key  # For simplicity, use the same key as peer key for key exchange

                            # Key exchange (only for ECC and KYBER)
                            if cipher_name == "ECC ECDSA":
                                try:
                                    shared_secret = ac.key_exchange(key, peer_key.get_public_key())
                                    print(f"\nKey Exchange [{param}] -> {shared_secret.hex()}", end="")
                                except NotSupportedError as e:
                                    print(f"\nKey Exchange [{param}] UNSUPPORTED - {str(e)}", end="")

                            # Signing and verification (for all except KYBER)
                            if cipher_name != "KYBER":
                                for padding in (ASym.Padding.PKCShash1v15, ASym.Padding.OAEP, ASym.Padding.PSS) \
                                        if cipher_name == "RSA" else [None]:
                                    for strength in (
                                    Security.BASIC, Security.AVERAGE, Security.STRONG, Security.SUPER_STRONG):
                                        try:
                                            signature = ac.sign(test_data, key, padding, strength)
                                            verification = ac.sign_verify(test_data, signature, key, padding, strength)
                                            print(
                                                f"\n{param} [{padding, strength}] Signature -> {signature.hex()} Verification -> {verification}",
                                                end="")
                                        except NotSupportedError as e:
                                            print(f"\n{param} -- Signing [{padding, strength}] UNSUPPORTED - {str(e)}",
                                                  end="")

                            # Encryption and decryption (for RSA and ECC)
                            if cipher_name in ["RSA", "KYBER"]:
                                for strength in (Security.BASIC, Security.AVERAGE, Security.STRONG, Security.SUPER_STRONG):
                                    padding = ASym.Padding.OAEP if cipher_name == "RSA" else None
                                    try:
                                        ciphertext = ac.encrypt(test_data, key, padding, strength)
                                        plaintext = ac.decrypt(ciphertext, key, padding, strength)
                                        print(
                                            f"\n{param} [{padding, strength}] Encrypted -> {ciphertext.hex()} Decrypted -> {plaintext}",
                                            end="")
                                    except NotSupportedError as e:
                                        print(f"\n{param} [{padding, strength}] UNSUPPORTED - {str(e)}", end="")

                        except NotSupportedError as e:
                            print(f"\n{param} UNSUPPORTED - {str(e)}", end="")
                    print("\n--------------------------------------------------------------")

                print("#" * 222, "\n")
        except Exception as e:
            print(f"An error occurred while testing security.crypto, AdvancedCryptography {e}")
            assert False
        assert True

    def test_easy_api(self):
        try:
            # Initialize with generated key
            encryptor = DataEncryptor(256)
            encrypted_data = encryptor.encrypt_data(b"Hello World")
            decrypted_data = encryptor.decrypt_data(encrypted_data)
            print(f"Decrypted Data: {decrypted_data}")
            assert decrypted_data == b"Hello World"

            # Initialize with existing key
            key = Sym.Cipher.AES.key(256).get_key()
            encryptor_with_key = DataEncryptor(key)
            encrypted_data_with_key = encryptor_with_key.encrypt_data(b"Hello World")
            decrypted_data_with_key = encryptor_with_key.decrypt_data(encrypted_data_with_key)
            print(f"Decrypted Data with Key: {decrypted_data_with_key}")
            assert decrypted_data_with_key == b"Hello World"

            # Retrieve the key
            retrieved_key = encryptor_with_key.get_key()
            print(f"Retrieved Key: {retrieved_key}")
            assert key == retrieved_key

            # Initialize with generated key pair
            signer = DigitalSigner()
            signature = signer.sign_data(b"Hello World")
            verification = signer.verify_signature(b"Hello World", signature)
            print(f"Signature Verification: {verification}")
            assert verification

            # Retrieve the key pair
            retrieved_key_pair = signer.get_private_key()
            print(f"Retrieved Key Pair: {retrieved_key_pair}")

            signer_with_key_pair = DigitalSigner(retrieved_key_pair)
            signature_with_key_pair = signer_with_key_pair.sign_data(b"Hello World")
            verification_with_key_pair = signer_with_key_pair.verify_signature(b"Hello World", signature_with_key_pair)
            print(f"Signature Verification with Key Pair: {verification_with_key_pair}")
            assert verification_with_key_pair

            assert retrieved_key_pair == signer_with_key_pair.get_private_key()

            pm = PasswordManager(backend=Backend.pycryptodomex)
            hashed_pw = pm.hash_password("MySecretPassword", strength=Security.BASIC)
            pw_verification = pm.verify_password("MySecretPassword", hashed_pw, strength=Security.BASIC)
            print("Hashed Password:", hashed_pw)
            print("Verification:", pw_verification)
            assert pw_verification
        except Exception as e:
            print(f"An error occurred while testing security.crypto, easy api {e}")
            assert False
        assert True
