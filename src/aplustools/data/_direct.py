"""TBA"""

from ..package import enforce_hard_deps as _enforce_hard_deps

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

__deps__ = []
__hard_deps__ = []
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
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


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


def gen_map(functions: _a.Iterable[_a.Callable[..., _ty.Any]], args_iter: _a.Iterator[_ty.Any],
            kwargs_iter: _a.Iterator[_ty.Any]) -> _a.Iterator[_ty.Any]:
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
