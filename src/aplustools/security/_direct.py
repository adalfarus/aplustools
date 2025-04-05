"""TBA"""
from enum import Enum as _Enum

from ..package import enforce_hard_deps as _enforce_hard_deps

from typing_extensions import deprecated

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

__deps__: list[str] = []
__hard_deps__: list[str] = []
_enforce_hard_deps(__hard_deps__, __name__)


class GenericLabeledEnum(_Enum):
    value: _ty.Any
    label: str

    def __new__(cls, value: _ty.Any, label: str):
        # Construct a base instance based on value type
        obj = object.__new__(cls)  # <-- FIXED: safe for nested or complex types
        obj._value_ = value
        obj.label = label
        return obj

    def __str__(self) -> str:
        return self.label  # printed or str() shows label

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}({repr(self.value)}, {repr(self.label)})"

    def __int__(self) -> int:
        try:
            return int(self.value)
        except Exception as e:
            raise TypeError("Cannot convert non-int value to int") from e

    def __index__(self) -> int:
        print(f"Converting {self, type(self)} to int")
        return int(self)

    def __eq__(self, other: _ty.Any) -> bool:
        return self.value == other or super().__eq__(other)

    def __hash__(self) -> int:
        return hash(self.value)

    def __getattr__(self, attr):
        # 🔥 Here's the key: delegate missing attrs to `.value`
        try:
            return getattr(self.value, attr)
        except AttributeError:
            raise AttributeError(
                f"{self.__class__.__name__} object has no attribute '{attr}'"
            )

# @deprecated("Please use GenericLabeledEnum instead")
class EAN:
    def __init__(self, value: _ty.Any, info: str) -> None:
        self.value = value
        self.info = info

    def __repr__(self) -> str:
        return self.info


class Security:  # Changed to indices for easy selection from iterables
    """Baseclass for different security levels"""
    BASIC = EAN(0, "An attacker can reverse whatever if they have enough info on you pretty easily")
    AVERAGE = EAN(1, "A lot better than basic")
    STRONG = EAN(2, "Practically impossible to reverse or crack")
    SUPER_STRONG = EAN(3, "Great security, but at the cost of comfort features like readability and efficiency")

    check_not_available: bool = True


class RiskLevel(GenericLabeledEnum):
    """Risk assessment for various parts of security"""
    HARMLESS = (None, "Harmless: Considered secure, even with the threat of future quantum computers.")
    NOT_RECOMMENDED = (None, "Not recommended: Generally secure but there are better or more modern alternatives.")
    KNOWN_UNSAFE = (None, "Deprecated: Known vulnerabilities exist; should not be used.")
    KNOWN_UNSAFE_NOT_RECOMMENDED = (None, "Deprecated, Not recommended: Combination of known issues and better alternatives.")
    HIGHLY_DANGEROUS = (None, "Highly dangerous: Easily broken and should not be used under any circumstances.")
