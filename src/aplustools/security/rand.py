"""TBA"""
import secrets as _secrets
import random as _random
import math as _math
import os as _os

from numpy import random as _np_random, ndarray as _ndarray

from ..package import enforce_hard_deps as _enforce_hard_deps

# Standard typing imports for aps
from abc import abstractmethod
import collections.abc as _a
import typing as _ty
import types as _ts

__deps__: list[str] = []
__hard_deps__: list[str] = ["numpy"]
_enforce_hard_deps(__hard_deps__, __name__)


class _SupportsLenAndGetItem(_ty.Protocol):
    def __len__(self) -> int:
        ...

    def __getitem__(self, index: int) -> _ty.Any:
        ...


class ModularRandom:
    @staticmethod
    @abstractmethod
    def random() -> float:
        """The random method powering all others. Has to be implemented.
        float between 0 and 1, inclusive"""
        ...

    @classmethod
    def uniform(cls, a: float, b: float) -> float:
        """A uniform random value between a and b, inclusive, float"""
        return a + (b - a) * cls.random()

    @classmethod
    def randint(cls, a: int, b: int) -> int:
        """A uniform random value between a and b, inclusive, int"""
        return int(round(cls.uniform(a, b), 0))

    @classmethod
    def randbelow(cls, b: int) -> int:
        """A uniform random value between 0 and b, inclusive, int"""
        return cls.randint(0, b)

    @classmethod
    def choice(cls, seq: _SupportsLenAndGetItem) -> _ty.Any:
        """Randomly choose a single element from a SupportsLenAndGetItem and
        returns the element"""
        if not len(seq):
            raise IndexError("Cannot choose from an empty sequence")
        if isinstance(seq, dict):
            return seq[cls.choice(list(seq.keys()))]
        return seq[cls.randint(0, len(seq) - 1)]

    @classmethod
    def choices(cls, seq: _SupportsLenAndGetItem, k: int) -> _ty.Any:
        """Randomly choose a k elements from a SupportsLenAndGetItem and
        returns the elements. Elements can be chosen more than once"""
        return [cls.choice(seq) for _ in range(k)]

    @classmethod
    def shuffle(cls, s: list[_ty.Any]) -> None:
        """Implements the fisher yates shuffle, works on the list, meaning no copy"""
        # Perform the Fisher-Yates shuffle
        n = len(s)
        for i in range(n - 1, 0, -1):
            j = cls.randint(0, i)
            s[i], s[j] = s[j], s[i]

    @classmethod
    def sample(cls, s: list[_ty.Any], k: int) -> list[_ty.Any]:
        """Samples k unique elements from s. Shuffels a copy of s
        and then takes the first k elements.
        Meaning it scales horribly for larger lists, but stays consistent
        no matter the amount of k"""
        ss = s.copy()
        cls.shuffle(ss)
        return ss[:k]

    @classmethod
    def string_sample(cls, s: str, k: int) -> str:
        return ''.join(cls.sample(list(s), k))

    @classmethod
    def generate_random_string(cls, length: int, char_set: str = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~') -> str:
        return ''.join(cls.choice(char_set) for _ in range(length))


class OSRandom(ModularRandom):
    @staticmethod
    def random() -> float:
        """Return a random float from os.urandom"""
        return int.from_bytes(_os.urandom(7), "big") / (1 << 56)


class SecretsRandom(ModularRandom):
    @staticmethod
    def random() -> float:
        """Return a random float from secrets.randbits"""
        return _secrets.randbits(56) / (1 << 56)


class NumPyRandom:
    _generator = _np_random.default_rng()

    @staticmethod
    def random() -> float:
        return NumPyRandomGenerator._generator.random()

    @classmethod
    def uniform(cls, a: float, b: float) -> float:
        return cls._generator.uniform(a, b)

    @classmethod
    def randint(cls, a: int, b: int) -> int:
        return cls._generator.integers(a, b + 1)

    @classmethod
    def randbelow(cls, b: int) -> int:
        return cls.randint(0, b)

    @classmethod
    def choice(cls, seq: list[_ty.Any] | tuple[_ty.Any] | _ndarray) -> _ty.Any:
        if isinstance(seq, str):
            return ''.join(cls._generator.choice(list(seq)))
        return cls._generator.choice(seq)

    @classmethod
    def choices(cls, seq: list[_ty.Any] | tuple[_ty.Any] | _ndarray, k: int) -> list | tuple | _ndarray:
        if isinstance(seq, str):
            return ''.join(cls._generator.choice(list(seq), size=k, replace=True).tolist())
        return cls._generator.choice(seq, size=k, replace=True).tolist()

    @classmethod
    def gauss(cls, mu: float, sigma: float) -> float:
        return cls._generator.normal(mu, sigma)

    @classmethod
    def expovariate(cls, lambd: float) -> float:
        return cls._generator.exponential(1 / lambd)

    @classmethod
    def gammavariate(cls, alpha: float, beta: float) -> float:
        return cls._generator.gamma(alpha, beta)

    @classmethod
    def betavariate(cls, alpha: float, beta: float) -> float:
        return cls._generator.beta(alpha, beta)

    @classmethod
    def lognormvariate(cls, mean: float, sigma: float) -> float:
        return cls._generator.lognormal(mean, sigma)

    @classmethod
    def shuffle(cls, s: list) -> None:
        cls._generator.shuffle(s)

    @classmethod
    def sample(cls, s: list, k: int) -> list:
        return cls._generator.choice(s, size=k, replace=False).tolist()

    @classmethod
    def binomialvariate(cls, n: int, p: float) -> int:
        return cls._generator.binomial(n, p)

    @classmethod
    def vonmisesvariate(cls, mu: float, kappa: float) -> float:
        return cls._generator.vonmises(mu, kappa)

    @classmethod
    def normalvariate(cls, mu: float, sigma: float) -> float:
        return cls._generator.normal(mu, sigma)

    @classmethod
    def paretovariate(cls, alpha: float) -> float:
        return cls._generator.pareto(alpha)

    @classmethod
    def weibullvariate(cls, alpha: float, beta: float) -> float:
        return cls._generator.weibull(beta) * alpha


def generator(name: _ty.Literal["random", "np_random", "os", "sys_random", "secrets"] = "sys_random") -> ModularRandom | _secrets.SystemRandom:
    return {
        "random": _random,
        "np_random": NumPyRandom,
        "os": OSRandom,
        "sys_random": _secrets.SystemRandom(),
        "secrets": SecretsRandom}[name]
