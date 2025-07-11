from cryptography.x509 import Name as XName, Certificate as XCertificate
from cryptography.hazmat.primitives import serialization

import enum

class CertificateEncoding(enum.Enum):
    PEM = "pem"             # Text format (recommended)
    DER = "der"             # Binary format


class Certificate:
    def __init__(self, name: XName, cert: XCertificate) -> None:
        self.name: XName = name
        self._impl: XCertificate = cert

    def encode(self, encoding: CertificateEncoding) -> bytes:
        if encoding.name.lower() == "pem":
            return self._impl.public_bytes(encoding=serialization.Encoding.PEM)
        elif encoding.name.lower() == "der":
            return self._impl.public_bytes(encoding=serialization.Encoding.DER)
        else:
            raise ValueError(f"Unsupported encoding: {encoding}")
