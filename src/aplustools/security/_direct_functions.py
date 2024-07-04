"""Functions and classes directly accessible from aplustools.security"""
from ..data import enum_auto as _enum_auto


class Security:  # Changed to indices for easy selection from iterables
    """Baseclass for different security levels"""
    BASIC = 0  # An attacker can reverse whatever if they have enough info on you pretty easily
    AVERAGE = 1  # A lot better than basic
    STRONG = 2  # Practically impossible to reverse or crack
    SUPER_STRONG = 3  # Great security, but at the cost of comfort features like readability and efficiency

    check_not_available = True


class RiskLevel:
    """Risk assessment for various parts of security"""
    HARMLESS = "Harmless: Considered secure, even with the threat of future quantum computers."
    NOT_RECOMMENDED = "Not recommended: Generally secure but there are better or more modern alternatives."
    KNOWN_UNSAFE = "Deprecated: Known vulnerabilities exist; should not be used."
    KNOWN_UNSAFE_NOT_RECOMMENDED = "Deprecated, Not recommended: Combination of known issues and better alternatives."
    HIGHLY_DANGEROUS = "Highly dangerous: Easily broken and should not be used under any circumstances."
