from cryptography.x509 import Name as XName, NameAttribute
from cryptography.x509.oid import NameOID

import typing as _ty


class Name:
    def __init__(self, common_name: str, organization: str | None = None, country: str | None = None) -> None:
        self.common_name: str = common_name
        self.organization: str | None = organization
        self.country: str | None = country

    def to_x509_name(self) -> XName:
        attributes = [
            NameAttribute(NameOID.COMMON_NAME, self.common_name)
        ]
        if self.organization:
            attributes.append(NameAttribute(NameOID.ORGANIZATION_NAME, self.organization))
        if self.country:
            attributes.append(NameAttribute(NameOID.COUNTRY_NAME, self.country))
        return XName(attributes)
