from typing import Iterable, Iterator, Callable, Any
import socket
import errno
import time


def reverse_map(functions: Iterable[Callable], *args, **kwargs):
    return [func(*args, **kwargs) for func in functions]


def gen_map(functions: Iterable[Callable], args_iter: Iterator[Any], kwargs_iter: Iterator[dict]):
    for func, args, kwargs in zip(functions, args_iter, kwargs_iter):
        yield func(*args, **kwargs)


class PortUtils:
    @staticmethod
    def find_available_port():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))  # Bind to an available port provided by the OS
            return s.getsockname()[1]  # Return the allocated port

    @staticmethod
    def find_available_port_range(start_port, end_port):
        for port in range(start_port, end_port + 1):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
                    return port  # Port is available
            except OSError as e:
                if e.errno == errno.EADDRINUSE:  # Port is already in use
                    continue
                raise  # Reraise unexpected errors
        raise RuntimeError("No available ports in the specified range")

    @staticmethod
    def test_port(port, retries=5, delay=1):
        while retries > 0:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
                    return port
            except OSError as e:
                if e.errno == errno.EADDRINUSE:
                    retries -= 1
                    time.sleep(delay)
                else:
                    raise
        raise RuntimeError("Port is still in use after several retries")


class Sorters:
    @staticmethod
    def selection_sort(iterable: list):
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
    def insertion_sort(iterable: list):
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
    def switch_sort(iterable: list):
        iterable = iterable.copy()
        length = len(iterable)

        for i in range(length):
            for j in range(i + 1, length):
                if iterable[j] < iterable[i]:
                    iterable[i], iterable[j] = iterable[j], iterable[i]

        return iterable

    @staticmethod
    def bubble_sort(iterable: list):
        iterable = iterable.copy()
        length = len(iterable)

        for i in range(length):
            for j in range(0, length - i - 1):
                if iterable[j] > iterable[j + 1]:
                    iterable[j], iterable[j + 1] = iterable[j + 1], iterable[j]

        return iterable

    @classmethod
    def _quick_helper(cls, iterable: list, low: int, high: int):
        if low < high:
            pi = cls._partition(iterable, low, high)
            cls._quick_helper(iterable, low, pi - 1)
            cls._quick_helper(iterable, pi + 1, high)

    @classmethod
    def _partition(cls, iterable: list, low: int, high: int):
        pivot = iterable[high]
        i = low - 1
        for j in range(low, high):
            if iterable[j] <= pivot:
                i += 1
                iterable[i], iterable[j] = iterable[j], iterable[i]
        iterable[i + 1], iterable[high] = iterable[high], iterable[i + 1]
        return i + 1

    @classmethod
    def quick_sort(cls, iterable: list):
        iterable = iterable.copy()
        cls._quick_helper(iterable, 0, len(iterable) - 1)
        return iterable

    @classmethod
    def _merge(cls, iterable: list, help_arr: list, left: int, right: int):
        if left < right:
            mid = (left + right) // 2

            cls._merge(iterable, help_arr, left, mid)
            cls._merge(iterable, help_arr, mid + 1, right)

            cls._merge_halves(iterable, help_arr, left, mid, right)

    @classmethod
    def _merge_halves(cls, iterable: list, help_arr: list, left: int, mid: int, right: int):
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
    def merge_sort(cls, iterable: list):
        iterable = iterable.copy()
        help_arr = [0] * len(iterable)
        cls._merge(iterable, help_arr, 0, len(iterable) - 1)
        return iterable


if __name__ == "__main__":
    from src.aplustools import TimidTimer
    from src.aplustools import cutoff_iterable

    lst = [0, 1, 5, -1] * 10000
    timer = TimidTimer()
    try:
        print(f"MergeSort: {cutoff_iterable(Sorters.merge_sort(lst), max_elements_end=2)}")
        print(timer.tock())
    except RecursionError:
        print("Max recursion reached for MergeSort")
        timer.tock()
    try:
        print(f"QuickSort: {cutoff_iterable(Sorters.quick_sort(lst), max_elements_end=2)}")
        print(timer.tock())
    except RecursionError:
        print("Max recursion reached for QuickSort")
        timer.tock()
    print(f"SelSort: {cutoff_iterable(Sorters.selection_sort(lst), max_elements_end=2)}")
    print(timer.tock())
    print(f"BubbleSort: {cutoff_iterable(Sorters.bubble_sort(lst), max_elements_end=2)}")
    print(timer.tock())
    print(f"SwitchSort: {cutoff_iterable(Sorters.switch_sort(lst), max_elements_end=2)}")
    print(timer.tock())
    print(f"InsertionSort: {cutoff_iterable(Sorters.insertion_sort(lst), max_elements_end=2)}")
    print(timer.tock())
