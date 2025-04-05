"""TBA"""
import sys as _sys

from ..package import enforce_hard_deps as _enforce_hard_deps

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

__deps__: list[str] = []
__hard_deps__: list[str] = []
_enforce_hard_deps(__hard_deps__, __name__)


class DummyBase:
    """
    A dummy base class that overrides many dunder methods with basic implementations
    that return default values or 'self'. This can be used as a placeholder or mock object
    in contexts where these methods need to be called without meaningful behavior.
    """

    def __init__(self, *args: _ty.Any, **kwargs: _ty.Any) -> None:
        """Initialize the DummyBase object with any arguments."""
        pass

    # Attribute dunder methods
    def __call__(self, *args: _ty.Any, **kwargs: _ty.Any) -> 'DummyBase':
        """Return self when called."""
        return self

    def __getattr__(self, *args: _ty.Any, **kwargs: _ty.Any) -> 'DummyBase':
        """Return self when an undefined attribute is accessed."""
        return self

    def __setattr__(self, key: str, value: _ty.Any) -> None:
        """Do nothing when an attribute is set."""
        return

    def __delattr__(self, item: str) -> None:
        """Do nothing when an attribute is deleted."""
        return None

    # Iter, index and with keyword dunder Methods
    def __iter__(self) -> _a.Generator[None, None, None]:
        """Return an empty generator."""
        yield

    def __enter__(self) -> 'DummyBase':
        """Enter a context and return self."""
        return self

    def __exit__(self, exc_type: _ty.Any, exc_val: _ty.Any, exc_tb: _ty.Any) -> bool:
        """Exit a context and always suppress exceptions."""
        return True

    def __getitem__(self, item: _ty.Any) -> 'DummyBase':
        """Return self when an item is accessed."""
        return self

    def __setitem__(self, key: _ty.Any, new_value: _ty.Any) -> None:
        """Do nothing when an item is set."""
        return

    def __delitem__(self, key: _ty.Any) -> None:
        """Do nothing when an item is deleted."""
        return None

    # Type dunder methods
    def __int__(self) -> int:
        """Return 0 when cast to an integer."""
        return int()

    def __float__(self) -> float:
        """Return 0.0 when cast to a float."""
        return float()

    # Function dunder methods
    def __len__(self) -> int:
        """Return 0 for the length."""
        return int()

    def __abs__(self) -> 'DummyBase':
        """Return self when absolute value is requested."""
        return self

    def __invert__(self) -> 'DummyBase':
        """Return self when bitwise inversion is requested."""
        return self

    def __round__(self, ndigits: int = 0) -> 'DummyBase':
        """Return self when rounding is requested."""
        return self

    def __trunc__(self) -> 'DummyBase':
        """Return self when truncation is requested."""
        return self

    # Unary operators (-x, +x, ~x)
    def __pos__(self) -> 'DummyBase':
        """Return self for unary positive."""
        return self

    def __neg__(self) -> 'DummyBase':
        """Return self for unary negation."""
        return self

    # Operators (+, -, /, *, //, %, &, |, ^, <<, >>, etc.)
    def __add__(self, other: _ty.Any) -> 'DummyBase':
        """Return self for addition."""
        return self

    def __radd__(self, other: _ty.Any) -> 'DummyBase':
        """Return self for reverse addition."""
        return self

    def __sub__(self, other: _ty.Any) -> 'DummyBase':
        """Return self for subtraction."""
        return self

    def __rsub__(self, other: _ty.Any) -> 'DummyBase':
        """Return self for reverse subtraction."""
        return self

    def __mul__(self, other: _ty.Any) -> 'DummyBase':
        """Return self for multiplication."""
        return self

    def __rmul__(self, other: _ty.Any) -> 'DummyBase':
        """Return self for reverse multiplication."""
        return self

    def __div__(self, other: _ty.Any) -> 'DummyBase':
        """Return self for division (Python 2 compatibility)."""
        return self

    def __rdiv__(self, other: _ty.Any) -> 'DummyBase':
        """Return self for reverse division (Python 2 compatibility)."""
        return self

    def __floordiv__(self, other: _ty.Any) -> 'DummyBase':
        """Return self for floor division."""
        return self

    def __rfloordiv__(self, other: _ty.Any) -> 'DummyBase':
        """Return self for reverse floor division."""
        return self

    def __truediv__(self, other: _ty.Any) -> 'DummyBase':
        """Return self for true division."""
        return self

    def __rtruediv__(self, other: _ty.Any) -> 'DummyBase':
        """Return self for reverse true division."""
        return self

    def __mod__(self, other: _ty.Any) -> 'DummyBase':
        """Return self for modulo operation."""
        return self

    def __rmod__(self, other: _ty.Any) -> 'DummyBase':
        """Return self for reverse modulo operation."""
        return self

    def __divmod__(self, other: _ty.Any) -> 'DummyBase':
        """Return self for divmod operation."""
        return self

    def __rdivmod__(self, other: _ty.Any) -> 'DummyBase':
        """Return self for reverse divmod operation."""
        return self

    def __pow__(self, n: _ty.Any) -> 'DummyBase':
        """Return self for power operation."""
        return self

    def __rpow__(self, n: _ty.Any) -> 'DummyBase':
        """Return self for reverse power operation."""
        return self

    def __lshift__(self, other: _ty.Any) -> 'DummyBase':
        """Return self for left shift."""
        return self

    def __rlshift__(self, other: _ty.Any) -> 'DummyBase':
        """Return self for reverse left shift."""
        return self

    def __rshift__(self, other: _ty.Any) -> 'DummyBase':
        """Return self for right shift."""
        return self

    def __rrshift__(self, other: _ty.Any) -> 'DummyBase':
        """Return self for reverse right shift."""
        return self

    def __and__(self, other: _ty.Any) -> 'DummyBase':
        """Return self for bitwise and."""
        return self

    def __rand__(self, other: _ty.Any) -> 'DummyBase':
        """Return self for reverse bitwise and."""
        return self

    def __or__(self, other: _ty.Any) -> 'DummyBase':
        """Return self for bitwise or."""
        return self

    def __ror__(self, other: _ty.Any) -> 'DummyBase':
        """Return self for reverse bitwise or."""
        return self

    def __xor__(self, other: _ty.Any) -> 'DummyBase':
        """Return self for bitwise xor."""
        return self

    def __rxor__(self, other: _ty.Any) -> 'DummyBase':
        """Return self for reverse bitwise xor."""
        return self

    def __format__(self, format_str: str = "") -> str:
        """Return an empty string for formatting."""
        return ""


class Dummy2(DummyBase):
    """
    A dummy class designed for Python 2 compatibility, raising an error if used in Python 3.
    """

    def __init__(self, *args: _ty.Any, **kwargs: _ty.Any) -> None:
        """Initialize the Dummy2 class and raise an error if not used in Python 2."""
        if _sys.version[0] != "2":
            raise RuntimeError("Please only use Dummy2 for Python 2")

    def __long__(self) -> 'Dummy2':
        """Return self when cast to a long integer (Python 2 compatibility)."""
        return self

    def __oct__(self) -> 'Dummy2':
        """Return self when octal conversion is requested."""
        return self

    def __hex__(self) -> 'Dummy2':
        """Return self when hexadecimal conversion is requested."""
        return self

    def __coerce__(self, other: _ty.Any) -> 'Dummy2':
        """Return self for coercion (Python 2 compatibility)."""
        return self

    def __unicode__(self) -> str:
        """Return an empty Unicode string."""
        return u''

    def __nonzero__(self) -> bool:
        """Return False for the nonzero check (Python 2 compatibility)."""
        return False

    def next(self) -> None:
        """Raise StopIteration for the next method (Python 2 compatibility)."""
        raise StopIteration


class Dummy3(DummyBase):
    """
    A dummy class designed for Python 3 compatibility, raising an error if used in Python 2.
    """

    def __init__(self, *args: _ty.Any, **kwargs: _ty.Any) -> None:
        """Initialize the Dummy3 class and raise an error if not used in Python 3."""
        if _sys.version[0] != "3":
            raise RuntimeError("Please only use Dummy3 for Python 3")

    def __index__(self) -> int:
        """Return 0 for index conversion."""
        return int()

    def __hash__(self) -> int:
        """Return 0 for the hash value."""
        return int()
