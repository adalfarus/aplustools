from enum import Enum, Flag, auto

class KeyDev(Enum):
    PBKDF2 = "PBKDF2"  # Password-Based Key Derivation Function 2
    Scrypt = "Scrypt"
    HKDF = "HKDF"  # HMAC-based Extract-and-Expand Key Derivation Function
    X9dot63 = "X9.63"
    X9dot42 = "X9.42"

class AuthCodes(Enum):
    HMAC = "HMAC"  # Hash-based Message Authentication Code
    CMAC = "CMAC"  # Cipher-based Message Authentication Code

class CryptoMethod(Flag):
    PBKDF2 = auto()
    Scrypt = auto()
    HKDF = auto()
    X9dot63 = auto()
    X9dot42 = auto()
    HMAC = auto()
    CMAC = auto()

    def describe(self):
        descriptions = []
        if self & CryptoMethod.PBKDF2:
            descriptions.append(KeyDev.PBKDF2.value)
        if self & CryptoMethod.Scrypt:
            descriptions.append(KeyDev.Scrypt.value)
        if self & CryptoMethod.HKDF:
            descriptions.append(KeyDev.HKDF.value)
        if self & CryptoMethod.X9dot63:
            descriptions.append(KeyDev.X9dot63.value)
        if self & CryptoMethod.X9dot42:
            descriptions.append(KeyDev.X9dot42.value)
        if self & CryptoMethod.HMAC:
            descriptions.append(AuthCodes.HMAC.value)
        if self & CryptoMethod.CMAC:
            descriptions.append(AuthCodes.CMAC.value)
        return "-".join(descriptions)

# Example functions to demonstrate usage
def generate_key(method: CryptoMethod):
    print(f"Generating key using {method.describe()}")

def authenticate(method: CryptoMethod):
    print(f"Authenticating using {method.describe()}")

# Example usage
generate_key(CryptoMethod.PBKDF2 | CryptoMethod.HMAC)
authenticate(CryptoMethod.Scrypt | CryptoMethod.CMAC)
