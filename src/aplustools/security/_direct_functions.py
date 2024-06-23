"""Functions and classes directly accessible from aplustools.security"""


class Security:  # Changed to indices for easy selection from iterables
    """Baseclass for different security levels"""
    WEAK = 0  # An attacker can reverse whatever if they have enough info on you pretty easily
    AVERAGE = 1  # A lot better than weak
    STRONG = 2  # Practically impossible to reverse or crack
    SUPER_STRONG = 3  # Great security, but at the cost of comfort features like readability and efficiency
