"""TBA"""

from .package import enforce_hard_deps as _enforce_hard_deps

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

__deps__: list[str] = []
__hard_deps__: list[str] = []
_enforce_hard_deps(__hard_deps__, __name__)


def dynamic_cls(name: str, inheritors: tuple[_ty.Type, ...], methods: dict[str, _a.Callable] | None) -> _ty.Type:
    """
    Dynamically creates a new class with the specified name, base classes, and methods.

    Args:
        name (str): The name of the new class.
        inheritors (tuple[type, ...]): A tuple of base classes that the new class will inherit from.
        methods (dict[str, callable] | None): A dictionary where keys are method names and values are callables
            (functions) to be used as methods for the new class. If `None`, no methods are added.

    Returns:
        type: The newly created class.

    Example:
        >>> class Base:
        ...     def greet(self):
        ...         return "Hello from Base"
        >>> new_class = dynamic_cls(
        ...     "MyClass",
        ...     (Base,),
        ...     {"say_hello": lambda self: "Hello from MyClass"}
        ... )
        >>> obj = new_class()
        >>> print(obj.greet())  # Output: Hello from Base
        >>> print(obj.say_hello())  # Output: Hello from MyClass
    """
    return type(name, inheritors, methods or {})
