# adultswork.py, aims to replace python standard classes with enhanced versions that are easier and more consistent
import datetime
import warnings


class ExperimentalError(Warning):
    pass

warnings.warn("This module is still experimental. Please use with caution", 
              ExperimentalError, 
              stacklevel=2)

class EnhancedString(str):
    """
    Enhanced string class with additional methods for ease of use.
    """
    
    def remove(self, substring: str) -> str:
        if not isinstance(substring, str):
            raise ValueError("The substring must be a string.")
        return self.replace(substring, '')

    def insert(self, substring):
        pass

    def __add__(self, other: str) -> str:
        if not isinstance(other, str):
            raise TypeError(f"can only concatenate str (not '{type(other).__name__}') to str")
        return EnhancedString(super().__add__(other))


class EnhancedDict(dict):
    """
    Enhanced dictionary class with additional methods for ease of use.
    """
    
    def add_item(self, key, value):
        self[key] = value
        
    def add(self, dic: dict):
        self.update(dic)
        
    def insert(self, key_or_dict, value=None):
        if isinstance(key_or_dict, dict):
            self.add(key_or_dict)
        elif value is not None:
            self.add_item(key_or_dict, value)
        else:
            raise ValueError("Invalid arguments: if the first argument is not a dictionary, a value must be provided")

    def __add__(self, other: dict):
        if not isinstance(other, dict):
            raise TypeError(f"unsupported operand type(s) for +: '{type(self).__name__}' and '{type(other).__name__}'")
        new_dict = EnhancedDict(self)
        new_dict.update(other)
        return new_dict


class EnhancedList(list):
    """
    Enhanced list class with additional methods for ease of use.
    """
    
    def remove_duplicates(self):
        no_duplicates = list(set(self))
        self.clear()
        self.extend(no_duplicates)

    def __add__(self, other: list):
        if not isinstance(other, list):
            raise TypeError(f"can only concatenate list (not '{type(other).__name__}') to list")
        return EnhancedList(super().__add__(other))

class EnhancedInteger(int):
    """
    Enhanced integer class with additional methods for ease of use.
    """

    def to_binary(self) -> str:
        return bin(self)[2:]

    def to_hex(self) -> str:
        return hex(self)[2:]

    
class EnhancedFloat(float):
    """
    Enhanced float class with additional methods for ease of use.
    """

    def to_string(self, decimal_places: int) -> str:
        return f"{self:.{decimal_places}f}"

    
class EnhancedSet(set):
    """
    Enhanced set class with additional methods for ease of use.
    """

    def power_set(self):
        from itertools import chain, combinations
        return EnhancedSet(chain.from_iterable(combinations(self, r) for r in range(len(self)+1)))

class EnhancedFile:
    """
    Enhanced file class with additional methods for ease of use.
    """

    def __init__(self, file_name, mode):
        self.file = open(file_name, mode)
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.file.close()

    def write_list(self, items):
        for item in items:
            self.file.write(str(item) + '\n')

    def read_list(self):
        return [line.strip() for line in self.file.readlines()]


class EnhancedDateTime(datetime.datetime):
    """
    Enhanced datetime class with additional methods for ease of use.
    """

    def add_days(self, days):
        return self + datetime.timedelta(days=days)

    def subtract_days(self, days):
        return self - datetime.timedelta(days=days)

    def to_string(self, format: str):
        return self.strftime(format)


class EnhancedTuple(tuple):
    """
    Enhanced tuple class with additional methods for ease of use.
    """

    def count_occurrences(self, value):
        return self.count(value)

    def index_of(self, value):
        return self.index(value)
    
def local_test():
    # EnhancedString
    string = EnhancedString("Hello beautiful world!")
    print(string.remove("beautiful"))  # Output: "Hello  world!"

    # EnhancedDict
    dict = EnhancedDict({0: "Hello", 1: "world"})
    dict2 = {1: "dark", 2: "world!"}
    print(dict + dict2)  # Output: {0: "Hello", 1: "dark", 2: "world!"}

    # EnhancedList
    list = EnhancedList([0, 1, 0, 2, 3, 1])
    list.remove_duplicates()
    print(list)  # Output: [0, 1, 2, 3]

    # EnhancedInteger
    integer = EnhancedInteger(7)
    print(integer.to_binary(), integer.to_hex())  # Output: "111" "7"

    # EnhancedFloat
    floating_point = EnhancedFloat(7.2)
    print(floating_point.to_string(2))  # Output: "7.20"

    # EnhancedSet
    boring_set = EnhancedSet({"hell", "no"})
    print(boring_set.power_set())  # Output: All possible subsets

    # EnhancedFile
    #with EnhancedFile("./test.txt", "r") as f:
    #    print(f.read_list())  # Output: List of lines from test.txt

    # EnhancedDateTime
    time = EnhancedDateTime.now()
    print(time.add_days(7).to_string("%Y-%m-%d"))  # Output: Date 7 days from now

    # EnhancedTuple
    tup = EnhancedTuple((1, 1, 3, 4, 1, 2))
    print(tup.count_occurrences(1), tup.index_of(2))  # Output: 3 5

if __name__ == "__main__":
    local_test()
