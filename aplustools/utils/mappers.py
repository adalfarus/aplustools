from typing import Iterable, Iterator, Callable, Any


def reverse_map(functions: Iterable[Callable], *args, **kwargs):
    return [func(*args, **kwargs) for func in functions]


def gen_map(functions: Iterable[Callable], args_iter: Iterator[Any], kwargs_iter: Iterator[dict]):
    for func, args, kwargs in zip(functions, args_iter, kwargs_iter):
        yield func(*args, **kwargs)


def local_test():
    try:
        reverse_map([print, print], "Hello World")
    except Exception as e:
        print(f"Exception occurred {e}.")
        return False
    else:
        print("Test completed successfully.")
        return True


if __name__ == "__main__":
    local_test()
