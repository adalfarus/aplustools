"""Functions and classes directly accessible from aplustools.security"""
from aplustools.data import enum_auto as _enum_auto


class Security:
    """Baseclass for different security levels"""
    WEAK = _enum_auto()  # An attacker can reverse whatever if they have enough info on you pretty easily
    AVERAGE = _enum_auto()  # A lot better than weak
    STRONG = _enum_auto()  # Practically impossible to reverse or crack
    SUPER_STRONG = _enum_auto()  # Great security, but at the cost of comfort features like readability and efficiency
