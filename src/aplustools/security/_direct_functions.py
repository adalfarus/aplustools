"""Functions and classes directly accessible from aplustools.security"""
from aplustools.data import enum_auto as _enum_auto


class Security:
    """Baseclass for different security levels"""
    WEAK = _enum_auto()
    AVERAGE = _enum_auto()
    STRONG = _enum_auto()
    SUPER_STRONG = _enum_auto()
