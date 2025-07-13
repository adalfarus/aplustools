from quantcrypt.kem import MLKEM_512, MLKEM_768, MLKEM_1024
from quantcrypt.dss import MLDSA_44, MLDSA_65, MLDSA_87
from quantcrypt import errors


from .._definitions import _KYBER_KEYPAIRTYPE, _DILITHIUM_KEYPAIRTYPE, SymKeyEncoding
from ..exceptions import NotSupportedError as _NotSupportedError
from ..algos._asym import (
    KeyFormat as ASymKeyFormat,
    KeyEncoding as ASymKeyEncoding,
    Padding as ASymPadding,
)

import typing_extensions as _te
import typing as _ty


_KYBER_VARIANTS = {
    "kyber512": MLKEM_512,
    "kyber768": MLKEM_768,
    "kyber1024": MLKEM_1024,
}


class _KYBER_KEYPAIR(_KYBER_KEYPAIRTYPE):
    def __init__(self, mode: _ty.Literal["kyber512", "kyber768", "kyber1024"]) -> None:
        try:
            impl_cls = _KYBER_VARIANTS[mode]
        except KeyError:
            raise ValueError(f"Unsupported Kyber mode: {mode}")
        self._mode = mode
        self._impl = impl_cls()
        self._public_key: bytes | None
        self._private_key: bytes | None
        self._public_key, self._private_key = self._impl.keygen()

    @classmethod
    def decode(
        cls,
        mode: _ty.Literal["kyber512", "kyber768", "kyber1024"],
        *,
        public_key: bytes | None = None,
        private_key: bytes | None = None,
    ) -> _te.Self:
        """, encoding: SymKeyEncoding"""
        obj = cls(mode)
        obj._public_key = public_key
        obj._private_key = private_key
        return obj

    def encode_private_key(self) -> bytes | None:
        return self._private_key

    def encode_public_key(self) -> bytes | None:
        return self._public_key

    def encapsulate(self) -> tuple[bytes, bytes]:
        if self._public_key is None:
            raise ValueError("Cannot encaps without the public key")
        return self._impl.encaps(self._public_key)

    def decapsulate(self, ciphertext: bytes) -> bytes:
        if self._private_key is None:
            raise ValueError("Cannot encaps without the private key")
        return self._impl.decaps(self._private_key, ciphertext)

    def __repr__(self) -> str:
        return f"<KYBER mode={self._mode}>"


_DILITHIUM_VARIANTS = {
    "dilithium2": MLDSA_44,
    "dilithium3": MLDSA_65,
    "dilithium5": MLDSA_87,
}


class _DILITHIUM_KEYPAIR(_DILITHIUM_KEYPAIRTYPE):
    def __init__(
        self, mode: _ty.Literal["dilithium2", "dilithium3", "dilithium5"]
    ) -> None:
        try:
            impl_cls = _DILITHIUM_VARIANTS[mode]
        except KeyError:
            raise ValueError(f"Unsupported Dilithium mode: {mode}")
        self._mode = mode
        self._impl = impl_cls()
        self._public_key: bytes | None
        self._private_key: bytes | None
        self._public_key, self._private_key = self._impl.keygen()

    @classmethod
    def decode(
        cls,
        mode: _ty.Literal["dilithium2", "dilithium3", "dilithium5"],
        *,
        public_key: bytes | None = None,
        private_key: bytes | None = None,
    ) -> _te.Self:
        """, encoding: SymKeyEncoding"""
        obj = cls(mode)
        obj._public_key = public_key
        obj._private_key = private_key
        return obj

    def encode_private_key(self) -> bytes | None:
        return self._private_key

    def encode_public_key(self) -> bytes | None:
        return self._public_key

    def sign(self, data: bytes) -> bytes:
        if self._private_key is None:
            raise ValueError("Cannot sign without the private key")
        return self._impl.sign(self._private_key, data)

    def sign_verify(self, data: bytes, signature: bytes) -> bool:
        if self._public_key is None:
            raise ValueError("Cannot verify sign without the public key")
        return self._impl.verify(self._public_key, data, signature)

    def __repr__(self) -> str:
        return f"<DILITHIUM mode={self._mode}>"
