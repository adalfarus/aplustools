"""TBA"""
import json as _json
import re as _re

from ..package import enforce_hard_deps as _enforce_hard_deps
from ..package.argumint import analyze_function as _analyze_function

# Standard typing imports for aps
import typing_extensions as _te
import collections.abc as _a
import typing as _ty
if _ty.TYPE_CHECKING:
    import _typeshed as _tsh
import types as _ts

__deps__: list[str] = []
__hard_deps__: list[str] = []
_enforce_hard_deps(__hard_deps__, __name__)


def align_to_next(value: int, alignment: int) -> int:
    """
    Align a value to the next multiple of the given alignment.

    This function rounds the input `value` up to the nearest multiple of `alignment`.
    Zero counts as a multiple.

    Parameters:
    value : int
        The value to be aligned.
    alignment : int
        The alignment boundary to which the value should be aligned.

    Returns:
    int
        The next multiple of `alignment` that is greater than or equal to `value`.

    Example:
    >>> align_to_next(37, 8)
    40
    >>> align_to_next(0, 8)
    0
    >>> align_to_next(0, 8) or 8 # If you don't want 0 as a result
    8
    """
    return ((value + alignment - 1) // alignment) * alignment


def align_to_previous(value: int, alignment: int) -> int:
    """
    Align a value to the previous multiple of the given alignment.

    This function rounds the input `value` down to the nearest multiple of `alignment`.
    Zero counts as a multiple.

    Parameters:
    value : int
        The value to be aligned.
    alignment : int
        The alignment boundary to which the value should be aligned.

    Returns:
    int
        The largest multiple of `alignment` that is less than or equal to `value`.

    Example:
    >>> align_to_previous(37, 8)
    32
    >>> align_to_previous(4, 8)
    0
    >>> align_to_previous(4, 8) or 8 # If you don't want 0 as a result
    8
    """
    return (value // alignment) * alignment


class SingletonMeta(type):
    """
    Metaclass to make UnifiedRequestHandlerAdvanced a Singleton.
    """
    _instances: dict[_ty.Type[_ty.Any], _ty.Any] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


@_te.deprecated("Unused function")
def reverse_map(functions: _a.Iterable[_a.Callable[..., _ty.Any]], *args: _ty.Any, **kwargs: _ty.Any) -> list[_ty.Any]:
    """
    Applies each function in the given iterable `functions` to the provided arguments and keyword arguments.

    Args:
        functions (Iterable[Callable[..., Any]]): An iterable of callable objects (functions) to be applied.
        *args (Any): Positional arguments passed to each function.
        **kwargs (Any): Keyword arguments passed to each function.

    Returns:
        list[Any]: A list of results, where each element is the result of applying a function from `functions`
        to the provided arguments and keyword arguments.
    """
    return [func(*args, **kwargs) for func in functions]


@_te.deprecated("Unused function")
def gen_map(functions: _a.Iterable[_a.Callable[..., _ty.Any]], args_iter: _a.Iterable[tuple[_ty.Any, ...]],
            kwargs_iter: _a.Iterable[dict[str, _ty.Any]]) -> _a.Iterator[_ty.Any]:
    """
    Applies each function in the given iterable `functions` to corresponding arguments and keyword arguments
    from `args_iter` and `kwargs_iter`, yielding the results one by one.

    Args:
        functions (Iterable[Callable[..., Any]]): An iterable of callable objects (functions) to be applied.
        args_iter (Iterator[Any]): An iterator of positional argument tuples for each function.
        kwargs_iter (Iterator[Dict[str, Any]]): An iterator of keyword argument dictionaries for each function.

    Yields:
        Iterator[Any]: A generator yielding the results of applying each function to its corresponding arguments
        and keyword arguments.
    """
    for func, args, kwargs in zip(functions, args_iter, kwargs_iter):
        yield func(*args, **kwargs)
    return None


_T = _ty.TypeVar('_T')


class Sorters(_ty.Generic[_T]):
    """
    A utility class that implements various sorting algorithms for lists of comparable elements.

    The class provides static and class methods for commonly used sorting techniques,
    including selection sort, insertion sort, bubble sort, switch sort, quicksort, and
    merge sort. Each method returns a new sorted list without modifying the original list.

    Sorting Algorithms:
        - selection_sort: Sorts using selection sort.
        - insertion_sort: Sorts using insertion sort.
        - switch_sort: Sorts by swapping any unordered elements (similar to bubble sort).
        - bubble_sort: Sorts using bubble sort.
        - quick_sort: Sorts using the quicksort algorithm.
        - merge_sort: Sorts using the merge sort algorithm.

    Quicksort and merge sort utilize recursive helper methods (_quick_helper and _merge)
    and partition/merge functions to efficiently sort the list.

    All sorting methods operate on a copy of the input list, ensuring that the original 
    list remains unchanged.

    This class works with any elements that support comparison operations (e.g., <, >, <=, >=).
    """

    @staticmethod
    def selection_sort(iterable: list[_T]) -> list[_T]:
        """
        Performs selection sort on a list of comparable elements.

        Args:
            iterable (list[T]): The list to be sorted.

        Returns:
            list[T]: A new list with the elements sorted in ascending order.
        """
        iterable = iterable.copy()
        length = len(iterable)

        for i in range(length):
            min_index = i
            for j in range(i + 1, length):
                if iterable[j] < iterable[min_index]:
                    min_index = j
            if min_index != i:
                iterable[i], iterable[min_index] = iterable[min_index], iterable[i]

        return iterable

    @staticmethod
    def insertion_sort(iterable: list[_T]) -> list[_T]:
        """
        Performs insertion sort on a list of comparable elements.

        Args:
            iterable (list[T]): The list to be sorted.

        Returns:
            list[T]: A new list with the elements sorted in ascending order.
        """
        iterable = iterable.copy()
        length = len(iterable)

        for i in range(1, length):
            key = iterable[i]
            j = i - 1
            while j >= 0 and key < iterable[j]:
                iterable[j + 1] = iterable[j]
                j -= 1
            iterable[j + 1] = key

        return iterable

    @staticmethod
    def switch_sort(iterable: list[_T]) -> list[_T]:
        """
        Performs a basic sort by comparing and swapping elements (similar to bubble sort).

        Args:
            iterable (list[T]): The list to be sorted.

        Returns:
            list[T]: A new list with the elements sorted in ascending order.
        """
        iterable = iterable.copy()
        length = len(iterable)

        for i in range(length):
            for j in range(i + 1, length):
                if iterable[j] < iterable[i]:
                    iterable[i], iterable[j] = iterable[j], iterable[i]

        return iterable

    @staticmethod
    def bubble_sort(iterable: list[_T]) -> list[_T]:
        """
        Performs bubble sort on a list of comparable elements.

        Args:
            iterable (list[T]): The list to be sorted.

        Returns:
            list[T]: A new list with the elements sorted in ascending order.
        """
        iterable = iterable.copy()
        length = len(iterable)

        for i in range(length):
            for j in range(0, length - i - 1):
                if iterable[j] > iterable[j + 1]:
                    iterable[j], iterable[j + 1] = iterable[j + 1], iterable[j]

        return iterable

    @classmethod
    def _quick_helper(cls, iterable: list[_T], low: int, high: int) -> None:
        """
        Recursively sorts sublists in quicksort.

        Args:
            iterable (list[T]): The list to be sorted.
            low (int): The starting index of the sublist to sort.
            high (int): The ending index of the sublist to sort.
        """
        if low < high:
            pi = cls._partition(iterable, low, high)
            cls._quick_helper(iterable, low, pi - 1)
            cls._quick_helper(iterable, pi + 1, high)

    @classmethod
    def _partition(cls, iterable: list[_T], low: int, high: int) -> int:
        """
        Partitions the list for quicksort by selecting a pivot and arranging elements.

        Args:
            iterable (list[T]): The list to be partitioned.
            low (int): The starting index of the partition.
            high (int): The ending index of the partition.

        Returns:
            int: The partition index where the pivot element is placed.
        """
        pivot = iterable[high]
        i = low - 1
        for j in range(low, high):
            if iterable[j] <= pivot:
                i += 1
                iterable[i], iterable[j] = iterable[j], iterable[i]
        iterable[i + 1], iterable[high] = iterable[high], iterable[i + 1]
        return i + 1

    @classmethod
    def quick_sort(cls, iterable: list[_T]) -> list[_T]:
        """
        Performs quicksort on a list of comparable elements.

        Args:
            iterable (list[T]): The list to be sorted.

        Returns:
            list[T]: A new list with the elements sorted in ascending order.
        """
        iterable = iterable.copy()
        cls._quick_helper(iterable, 0, len(iterable) - 1)
        return iterable

    @classmethod
    def _merge(cls, iterable: list[_T], help_arr: list[_T], left: int, right: int) -> None:
        """
        Recursively splits and merges the list in merge sort.

        Args:
            iterable (list[T]): The list to be sorted.
            help_arr (list[T]): A helper array to assist with merging.
            left (int): The starting index of the sublist to merge.
            right (int): The ending index of the sublist to merge.
        """
        if left < right:
            mid = (left + right) // 2

            cls._merge(iterable, help_arr, left, mid)
            cls._merge(iterable, help_arr, mid + 1, right)

            cls._merge_halves(iterable, help_arr, left, mid, right)

    @classmethod
    def _merge_halves(cls, iterable: list[_T], help_arr: list[_T], left: int, mid: int, right: int) -> None:
        """
        Merges two halves of a list during merge sort.

        Args:
            iterable (list[T]): The list to be merged.
            help_arr (list[T]): A helper array with copied elements.
            left (int): The starting index of the left half.
            mid (int): The middle index of the list.
            right (int): The ending index of the right half.
        """
        for i in range(left, right + 1):
            help_arr[i] = iterable[i]

        left_start = left
        right_start = mid + 1
        current = left

        while left_start <= mid and right_start <= right:
            if help_arr[left_start] <= help_arr[right_start]:
                iterable[current] = help_arr[left_start]
                left_start += 1
            else:
                iterable[current] = help_arr[right_start]
                right_start += 1
            current += 1

        remaining = mid - left_start
        for i in range(remaining + 1):
            iterable[current + i] = help_arr[left_start + i]

    @classmethod
    def merge_sort(cls, iterable: list[_T]) -> list[_T]:
        """
        Performs merge sort on a list of comparable elements.

        Args:
            iterable (list[T]): The list to be sorted.

        Returns:
            list[T]: A new list with the elements sorted in ascending order.
        """
        iterable = iterable.copy()
        help_arr = [None] * len(iterable)  # Helper array of the same length
        cls._merge(iterable, help_arr, 0, len(iterable) - 1)
        return iterable


def _custom_serializer(obj: _ty.Any) -> str:
    """
    Custom serializer function for handling non-serializable objects.

    Args:
        obj (any): The object to be serialized.

    Returns:
        str: The serialized object as a string.
    """
    try:
        return str(obj)
    except Exception:
        raise TypeError(f"Type {type(obj)} not serializable")


def beautify_json(data_dict: dict[str, _ty.Any]) -> str:
    """
    Beautifies a dictionary by converting it to a pretty-printed JSON string.

    Args:
        data_dict (dict): The dictionary to be beautified.

    Returns:
        str: The beautified JSON string.
    """
    # Convert dictionary to a pretty-printed JSON string using custom serializer
    pretty_json = _json.dumps(data_dict, indent=4, sort_keys=False, default=_custom_serializer)
    pretty_json = _re.sub(
        r'\[\s+([^][]+?)\s+]',
        lambda m: f"[{', '.join(item.strip() for item in m.group(1).split(','))}]",
        pretty_json
    )
    return pretty_json


if _ty.TYPE_CHECKING:
    def minmax(to_reduce: _tsh.SupportsRichComparisonT, min_val: _tsh.SupportsRichComparisonT,
               max_val: _tsh.SupportsRichComparisonT) -> _tsh.SupportsRichComparisonT:
        ...
else:
    def minmax(to_reduce, min_val,
               max_val) -> _ty.Any:
        """Clamp a value within a specified minimum and maximum range.

        Args:
            to_reduce (SupportsRichComparisonsT): The value to clamp.
            min_val (SupportsRichComparisonsT): The minimum allowable value.
            max_val (SupportsRichComparisonsT): The maximum allowable value.

        Returns:
            SupportsRichComparisonsT: The clamped value, ensuring it falls within [min_val, max_val].
        """
        return max(min_val, min(max_val, to_reduce))


def isEvenInt(x: int) -> int:
    """Determine if an integer is even.

    Args:
        x (int): The integer to check.

    Returns:
        int: 1 if the integer is even, otherwise 0.
    """
    return not x & 1


def isOddInt(x: int) -> int:
    """Determine if an integer is odd.

    Args:
        x (int): The integer to check.

    Returns:
        int: 1 if the integer is odd, otherwise 0.
    """
    return x & 1


def isEvenFloat(x: float | str) -> tuple[bool, bool]:
    """Check if a floating-point number has an even integer and fractional part.

    Args:
        x (float | str): The floating-point number or its string representation.

    Returns:
        tuple[bool, bool]: Tuple containing two booleans; the first indicates if the integer
                           part is even, the second indicates if the fractional part is even.
    """
    if x != x:  # Check for NaN
        return False, False
    if x in [float('inf'), float('-inf')]:  # Check for infinities
        return False, False
    if x == 0.0:  # Zero is even by conventional definition
        return True, True

    expo, dec = str(x).split(".")

    return isEvenInt(int(expo)) == 1, isEvenInt(int(dec)) == 1


def isOddFloat(x: float | str) -> tuple[bool, bool]:
    """Check if a floating-point number has an odd integer and fractional part.

    Args:
        x (float | str): The floating-point number or its string representation.

    Returns:
        tuple[bool, bool]: Tuple containing two booleans; the first indicates if the integer
                           part is odd, the second indicates if the fractional part is odd.
    """
    if x != x:  # Check for NaN
        return False, False
    if x in [float('inf'), float('-inf')]:  # Check for infinities
        return False, False
    if x == 0.0:  # Zero is even by conventional definition
        return False, False

    expo, dec = str(x).split(".")

    return isOddInt(int(expo)) == 1, isOddInt(int(dec)) == 1


class StdList(list):
    """A list with extended behavior for setting defaults and flexible indexing.

    Supports:
    - Default value generation for out-of-bounds indices.
    - Tuple indexing for retrieving multiple elements.
    - Custom default values for non-existent indices.
    """
    def __init__(self, default_factory=None, *args) -> None:
        super().__init__(*args)
        self.default_factory = default_factory

    def __getitem__(self, key: _ty.Union[int, slice, tuple]) -> _ty.Any:
        # Handle tuple access: (i1, i2, ...), (slice1, slice2, ...), or (index, default)
        if isinstance(key, tuple):
            if len(key) == 2 and not isinstance(key[0], slice) and not isinstance(key[1], slice):
                idx, default = key
                return super().__getitem__(idx) if idx < len(self) else default

            # Handle slices or multiple indices
            result = []
            for part in key:
                if isinstance(part, slice):
                    result.extend(self[part])
                else:
                    result.append(self[part])
            return tuple(x for x in result)
        elif isinstance(key, slice):
            result = []
            for part in range(key.start or 0, key.stop or len(self), key.step or 1):
                result.append(self[part])
            return tuple(result)

        # Normal list indexing, auto-expand if needed
        if isinstance(key, int) and key >= len(self) and self.default_factory is not None:
            self.extend(self.default_factory() for _ in range(len(self), key + 1))
        return super().__getitem__(key)

    def __setitem__(self, key: _ty.Union[int, slice, tuple], value: _ty.Any) -> None:
        if isinstance(key, tuple):
            if isinstance(value, (list, tuple)) and len(value) != len(key):
                raise ValueError("Value must match length of keys when assigning with tuple.")

            for i, part in enumerate(key):
                val = value[i] if isinstance(value, (list, tuple)) else value
                if isinstance(part, slice):
                    indices = range(part.start or 0, part.stop or len(self), part.step or 1)
                    for j, idx in enumerate(indices):
                        if idx >= len(self) and self.default_factory is not None:
                            self.extend(self.default_factory() for _ in range(len(self), idx + 1))
                        self[idx] = val[j] if isinstance(val, (list, tuple)) else val
                else:
                    if part >= len(self) and self.default_factory is not None:
                        self.extend(self.default_factory() for _ in range(len(self), part + 1))
                    super().__setitem__(part, val)
            return
        elif isinstance(key, slice):
            indices = range(key.start or 0, key.stop or len(self), key.step or 1)
            if isinstance(value, (list, tuple)) and len(value) != len(indices):
                raise ValueError("Value must match length of slice range.")
            for i, idx in enumerate(indices):
                val = value[i] if isinstance(value, (list, tuple)) else value
                if idx >= len(self) and self.default_factory is not None:
                    self.extend(self.default_factory() for _ in range(len(self), idx + 1))
                super().__setitem__(idx, val)
            return
        if isinstance(key, int) and key >= len(self) and self.default_factory is not None:
            self.extend(self.default_factory() for _ in range(len(self), key + 1))
        super().__setitem__(key, value)

    def get(self, key: int, default_factory=None) -> _ty.Any:
        if key >= len(self):
            self.extend(default_factory() for _ in range(len(self), key + 1))
        return super().__getitem__(key)


def unnest_iterable(iterable: _a.Iterable, max_depth: int = 4) -> list[_ty.Any]:
    """Flatten a nested iterable structure up to a specified depth.

    Args:
        iterable (Any): The nested structure to flatten.
        max_depth (int): Maximum depth to flatten.

    Returns:
        list: A flattened list of elements up to `max_depth`.
    """
    def _lod_helper(curr_lod: list[_ty.Any | list], big_lster: list[_ty.Any], depth: int) -> list[_ty.Any]:
        for x in curr_lod:
            if isinstance(x, list) and depth > 0:
                _lod_helper(x, big_lster, depth - 1)
            else:
                big_lster.append(x)
        return big_lster
    return _lod_helper(list(iterable), [], max_depth)


def cutoff_iterable(iterable: list | tuple | dict | set, start: int = 0, max_elements_right: int = 3,
                    max_elements_left: int = 0, show_hidden_elements_num: bool = False, return_lst: bool = False
                    ) -> str | list:
    """Truncate and format an iterable with optional placeholders for hidden elements.

    Args:
        iterable (list | tuple | dict | set): The iterable to format.
        start (int): Starting index for visible elements.
        max_elements_right (int): Max elements to show to the right.
        max_elements_left (int): Max elements to show to the left.
        show_hidden_elements_num (bool): Show count of hidden elements.
        return_lst (bool): If True, return as a list. Otherwise, return a formatted string.

    Returns:
        str | list: Formatted string or list with truncated elements.
    """
    if not isinstance(iterable, (list, tuple, set, dict)):
        return f"The class '{type(iterable).__name__}' is not a supported iterable."

    braces = {"tuple": "()", "list": "[]", "set": "{}", "dict": "{}"}[type(iterable).__name__]

    if isinstance(iterable, (tuple, set)):
        iterable = list(iterable)
    elif isinstance(iterable, dict):
        iterable = [f"{key}: {value}" for key, value in iterable.items()]

    n = len(iterable)
    max_elements_right, max_elements_left = abs(max_elements_right), abs(max_elements_left)
    elements_shown = max_elements_right + max_elements_left + 1
    elements_start = max_elements_left
    show_lst: list[_ty.Any | None] = [None] * elements_shown

    if start < max_elements_left:  # Adjusting for left overspill
        elements_start = start
    elif start + max_elements_right >= n:  # Adjusting for right overspill
        elements_start = (n - start) * -1

    for i in range(max_elements_right):
        show_lst[(elements_start + i + 1) % elements_shown] = iterable[(start + i + 1) % n]

    for i in range(max_elements_left + 1, 1, -1):
        show_lst[(elements_start - i + 1) % elements_shown] = iterable[(start - i + 1) % n]

    show_lst[elements_start] = iterable[start]

    left_hidden, right_hidden = start - max_elements_left, (n - 1) - start - max_elements_right

    if start < max_elements_left:  # Handle overflow from left to right
        right_hidden -= max_elements_left - start  # Reduce right_hidden by the number of overflowed elements
    if start + max_elements_right >= n:  # Handle overflow from right to left
        left_hidden -= (start + max_elements_right) - (n - 1)  # Reduce left_hidden by the number of overflowed elements

    left_hide = right_hide = "..."
    if show_hidden_elements_num:
        left_hide, right_hide = f"..[{left_hidden}]..", f"..[{right_hidden}].."

    if right_hidden > 0:
        show_lst.insert((elements_start + max_elements_right + 1), right_hide)
    if left_hidden > 0:
        show_lst.insert((elements_start - (max_elements_left + 1) + 1), left_hide)

    return braces[0] + ', '.join(str(x) for x in show_lst) + braces[1] if not return_lst else show_lst


def cutoff_string(string: str, max_chars_start: int = 4, max_chars_end: int = 0,
                  show_hidden_chars_num: bool = False) -> str:
    """Truncate a string with optional placeholders for hidden characters.

    Args:
        string (str): The string to truncate.
        max_chars_start (int): Max characters to show at the start.
        max_chars_end (int): Max characters to show at the end.
        show_hidden_chars_num (bool): Show count of hidden characters.

    Returns:
        str: Formatted truncated string.
    """
    truncated_list = cutoff_iterable(list(string), 0, max_chars_start, max_chars_end, show_hidden_chars_num, True)
    return "".join(truncated_list)


def what_func(func: _ts.FunctionType, type_names: bool = False, print_def: bool = True) -> str:
    """
    Analyzes the passed function, formats it into a nice string and optionally prints it.

    :param func:
    :param type_names:
    :param print_def:
    :return:
    """
    analysis = _analyze_function(func)

    def _get_type_name(t: _ty.Any) -> str | None:
        if hasattr(t, '__origin__') and t.__origin__ is _ty.Union or type(t) is _ty.Union and type(None) in t.__args__:  # type: ignore
            non_none_types = [arg for arg in t.__args__ if arg is not type(None)]
            return f"{t.__name__}[{', '.join(_get_type_name(arg) for arg in non_none_types)}]"  # type: ignore
        return t.__name__ if hasattr(t, '__name__') else (type(t).__name__ if t is not None else None)

    arguments_str = ''.join([f"{argument['name']}: "  # type: ignore 
                             f"{(_get_type_name(argument['type']) or type(argument['default']).__name__) if type_names else _get_type_name(argument['type']) or type(argument['default'])}"  # type: ignore 
                             f" = {argument['default']}, " for argument in analysis["arguments"]])[:-2]  # type: ignore
    definition = f"{func.__module__}.{analysis['name']}({arguments_str}){(' -> ' + str(analysis['return_type'])) if analysis['return_type'] is not None else ''}"
    if print_def:
        print(definition)
    return definition


def what_class(cls: _ty.Type[_ty.Any], type_names: bool = False, print_def: bool = True) -> str:
    """
    Analyzes the passed class, formats it into a string, and optionally prints it.

    :param cls:
    :param type_names:
    :param print_def:
    :return:
    """
    class_name = cls.__name__
    methods = [attr for attr in dir(cls) if callable(getattr(cls, attr)) and (not attr.startswith("_") or
                                                                              (attr == "__init__"))]

    class_def = [f"{class_name}:"]
    where = "???"
    for method in methods:
        where, method_def = what_func(getattr(cls, method), type_names=type_names,
                                      print_def=False).split(".", maxsplit=1)
        class_def.append(f"    {method_def}\n")

    class_def[0] = "class " + where + "." + class_def[0]
    result = "\n".join(class_def)

    if print_def:
        print(result)
    return result
