from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, ec
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import UnsupportedAlgorithm
from cryptography import x509
from datetime import datetime, timedelta, UTC

from ._name import Name
from ._certificate import Certificate

import typing as _ty


class PublicKey:
    def __init__(self, public_key) -> None:
        self._impl = public_key


class Key:
    def __init__(self, private_key):
        self._impl = private_key  # the real private key object

    @classmethod
    def from_bytes(cls, data: bytes, password: bytes | None = None):
        try:
            key = serialization.load_pem_private_key(data, password=password, backend=default_backend())
        except ValueError:
            # Might be DER instead
            key = serialization.load_der_private_key(data, password=password, backend=default_backend())
        return cls(key)

    def public_key(self) -> PublicKey:
        return PublicKey(self._impl.public_key())

    def default_hash(self):
        return hashes.SHA256()


class CertificateAuthority:
    def __init__(self, name: Name, key, cert: x509.Certificate) -> None:
        self.name: Name = name
        self.key = key
        self.cert: x509.Certificate = cert

    @classmethod
    def self_signed(cls, name: Name, key) -> _ty.Self:
        subject = name.to_x509_name()
        builder = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            subject
        ).public_key(
            key.public_key()._impl
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.now(UTC)
        ).not_valid_after(
            datetime.now(UTC) + timedelta(days=365)
        ).add_extension(
            x509.BasicConstraints(ca=True, path_length=None), critical=True,
        )

        certificate = builder.sign(private_key=key._impl, algorithm=key.default_hash())
        return cls(name, key, certificate)

    def issue(self, name: Name, key) -> Certificate:
        subject = name.to_x509_name()
        builder = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            self.cert.subject
        ).public_key(
            key._impl
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.now(UTC)
        ).not_valid_after(
            datetime.now(UTC) + timedelta(days=365)
        )
        cert = builder.sign(private_key=self.key._impl, algorithm=self.key.default_hash())
        return Certificate(subject, cert)
