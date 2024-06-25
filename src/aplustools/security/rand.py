from typing import Callable, Type, Protocol, Union, Any, List, Literal, Optional
from numpy import random as _np_random, ndarray as _ndarray
import secrets
import random
import math
import os

from aplustools.data import minmax


class _SupportsLenAndGetItem(Protocol):
    def __len__(self) -> int:
        ...

    def __getitem__(self, index: int) -> Union[str, list]:
        ...


class CustomRandomGenerator:
    @staticmethod
    def random() -> float:
        return 0.0

    @classmethod
    def setup_random_func(cls, func: Callable) -> Type["CustomRandomGenerator"]:
        NewClass = type('CustomRandomGeneratorModified', (cls,), {
            'random': func
        })
        return NewClass

    @classmethod
    def uniform(cls, a: float, b: float) -> float:
        return a + (b - a) * cls.random()

    @classmethod
    def randint(cls, a: int, b: int) -> int:
        return math.floor(cls.uniform(a, b + 1))

    @classmethod
    def randbelow(cls, b: int) -> int:
        return cls.randint(0, b)

    @classmethod
    def choice(cls, seq: _SupportsLenAndGetItem) -> Any:
        if not isinstance(seq, dict):
            return seq[cls.randint(0, len(seq) - 1)]
        return seq[tuple(seq.keys())[cls.randint(0, len(seq) - 1)]]

    @classmethod
    def choices(cls, seq: _SupportsLenAndGetItem, k: int) -> Any:
        if not isinstance(seq, dict):
            return [seq[cls.randint(0, len(seq) - 1)] for _ in range(k)]
        keys = list(seq.keys())
        return [seq[keys[cls.randint(0, len(keys) - 1)]] for _ in range(k)]

    @classmethod
    def gauss(cls, mu: float, sigma: float) -> float:
        # Using Box-Muller transform for generating Gaussian distribution
        u1 = cls.random()
        u2 = cls.random()
        z0 = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
        return mu + z0 * sigma

    @classmethod
    def expovariate(cls, lambd: float) -> float:
        u = cls.random()
        return -math.log(1 - u) / lambd

    @classmethod
    def gammavariate(cls, alpha: float, beta: float) -> float:
        # Uses Marsaglia and Tsang’s method for generating Gamma variables
        if alpha > 1:
            d = alpha - 1/3
            c = 1/math.sqrt(9*d)
            while True:
                x = cls.gauss(0, 1)
                v = (1 + c*x)**3
                u = cls.random()
                if u < 1 - 0.0331*(x**2)**2:
                    return d*v / beta
                if math.log(u) < 0.5*x**2 + d*(1 - v + math.log(v)):
                    return d*v / beta
        elif alpha == 1.0:
            return -math.log(cls.random()) / beta
        else:
            while True:
                u = cls.random()
                b = (math.e + alpha)/math.e
                p = b*u
                if p <= 1:
                    x = p**(1/alpha)
                else:
                    x = -math.log((b-p)/alpha)
                u1 = cls.random()
                if p > 1:
                    if u1 <= x**(alpha - 1):
                        return x / beta
                elif u1 <= math.exp(-x):
                    return x / beta

    @classmethod
    def betavariate(cls, alpha: float, beta: float) -> float:
        """
        Generate a random number based on the Beta distribution with parameters alpha and beta.

        :param alpha: Alpha parameter of the Beta distribution.
        :param beta: Beta parameter of the Beta distribution.
        :return: Random number from the Beta distribution.
        """
        y1 = cls.gammavariate(alpha, 1.0)
        y2 = cls.gammavariate(beta, 1.0)
        return y1 / (y1 + y2)

    @classmethod
    def lognormvariate(cls, mean: float, sigma: float) -> float:
        """
        Generate a random number based on the log-normal distribution with specified mean and sigma.

        :param mean: Mean of the underlying normal distribution.
        :param sigma: Standard deviation of the underlying normal distribution.
        :return: Random number from the log-normal distribution.
        """
        normal_value = cls.gauss(mean, sigma)
        return math.exp(normal_value)

    @classmethod
    def shuffle(cls, s: Union[str, list]) -> Union[str, list]:
        """fisher_yates_shuffle"""
        # Convert the string to a list of characters
        inp_type, char_list = list, s
        if not isinstance(s, list):
            char_list = list(s)
            inp_type = str

        # Perform the Fisher-Yates shuffle
        n = len(char_list)
        for i in range(n - 1, 0, -1):
            j = cls.randint(0, i)
            char_list[i], char_list[j] = char_list[j], char_list[i]

        if inp_type == str:
            # Convert the list of characters back to a string
            shuffled_string = ''.join(char_list)
            return shuffled_string
        return char_list

    @classmethod
    def sample(cls, s: Union[str, list], k: int) -> List:
        if isinstance(s, str):
            char_list = list(s)
        else:
            char_list = s

        n = len(char_list)
        if k > n:
            raise ValueError("Sample size k cannot be greater than the length of the input sequence.")

        sampled_indices = random.sample(range(n), k)
        sample = [char_list[i] for i in sampled_indices]
        return sample

    @classmethod
    def string_sample(cls, s: Union[str, list], k: int) -> str:
        return ''.join(cls.sample(s, k))

    @classmethod
    def generate_random_string(cls, length: int, char_set: str = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~') -> str:
        return ''.join(cls.choice(char_set) for _ in range(length))

    @classmethod
    def binomialvariate(cls, n: int, p: float) -> int:
        successes = 0
        for _ in range(n):
            if cls.random() < p:
                successes += 1
        return successes

    @classmethod
    def vonmisesvariate(cls, mu: float, kappa: float) -> float:
        if kappa <= 1e-6:
            return cls.uniform(0, 2 * math.pi)

        a = 1 + math.sqrt(1 + 4 * kappa ** 2)
        b = (a - math.sqrt(2 * a)) / (2 * kappa)
        r = (1 + b ** 2) / (2 * b)

        while True:
            u1 = cls.random()
            z = math.cos(math.pi * u1)
            f = (1 + r * z) / (r + z)
            c = kappa * (r - f)

            u2 = cls.random()
            if u2 < c * (2 - c) or u2 <= c * math.exp(1 - c):
                u3 = cls.random()
                theta = mu if u3 < 0.5 else mu + math.pi
                return (theta + math.acos(f)) % (2 * math.pi)

    @classmethod
    def normalvariate(cls, mu: float, sigma: float) -> float:
        return cls.gauss(mu, sigma)

    @classmethod
    def paretovariate(cls, alpha: float) -> float:
        u = cls.random()
        return 1 / (u ** (1 / alpha))

    @classmethod
    def weibullvariate(cls, alpha: float, beta: float) -> float:
        """
        Generate a random number based on the Weibull distribution with specified shape (alpha) and scale (beta).

        :param alpha: Shape parameter of the Weibull distribution.
        :param beta: Scale parameter of the Weibull distribution.
        :return: Random number from the Weibull distribution.
        """
        u = cls.random()
        return alpha * (-math.log(1 - u)) ** (1 / beta)

    @classmethod
    def cauchyvariate(cls, median: float, scale: float) -> float:
        """
        Generate a random number based on the Cauchy distribution with specified median and scale.

        :param median: Median of the Cauchy distribution.
        :param scale: Scale parameter of the Cauchy distribution.
        :return: Random number from the Cauchy distribution.
        """
        u = cls.random()
        return median + scale * math.tan(math.pi * (u - 0.5))

    @classmethod
    def standard_cauchy(cls) -> float:
        """
        Generate a random number based on the standard Cauchy distribution (median=0, scale=1).

        :return: Random number from the standard Cauchy distribution.
        """
        return cls.cauchyvariate(0, 1)


def os_random() -> float:
    return int.from_bytes(os.urandom(7), "big") / (1 << 56)


def secrets_random() -> float:
    return secrets.randbits(56) / (1 << 56)


OSRandomGenerator = CustomRandomGenerator.setup_random_func(os_random)
SecretsRandomGenerator = CustomRandomGenerator.setup_random_func(secrets_random)


class NumPyRandomGenerator:
    _generator = _np_random.default_rng()

    @staticmethod
    def random() -> float:
        return NumPyRandomGenerator._generator.random()

    @classmethod
    def setup_random_func(cls, func: Callable) -> Type["NumPyRandomGenerator"]:
        NewClass = type('NumPyRandomGeneratorModified', (cls,), {
            'random': staticmethod(func)
        })
        return NewClass

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
    def choice(cls, seq: Union[str, list, tuple, _ndarray]) -> Any:
        if isinstance(seq, str):
            return ''.join(cls._generator.choice(list(seq)))
        return cls._generator.choice(seq)

    @classmethod
    def choices(cls, seq: Union[str, list, tuple, _ndarray], k: int) -> Union[str, List]:
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
    def shuffle(cls, s: Union[str, list]) -> Union[str, list]:
        if isinstance(s, str):
            s_list = list(s)
            cls._generator.shuffle(s_list)
            return ''.join(s_list)
        else:
            cls._generator.shuffle(s)
            return s

    @classmethod
    def sample(cls, s: Union[str, list], k: int) -> Union[str, List]:
        if isinstance(s, str):
            return ''.join(cls._generator.choice(list(s), size=k, replace=False).tolist())
        return cls._generator.choice(s, size=k, replace=False).tolist()

    @classmethod
    def string_sample(cls, s: Union[str, list], k: int) -> str:
        return ''.join(cls.sample(s, k))

    @classmethod
    def generate_random_string(cls, length: int, char_set: str = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~') -> str:
        return ''.join(cls.choice(list(char_set)) for _ in range(length))

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


class WeightedRandom:
    def __init__(self, generator: Literal["random", "np_random", "os", "sys_random", "secrets"] = "sys_random"):
        self._generator = {"random": random, "np_random": NumPyRandomGenerator, "os": OSRandomGenerator,
                           "sys_random": secrets.SystemRandom(), "secrets": SecretsRandomGenerator}[generator]

    def random(self) -> float:
        """
        Returns the generators default random functions result.

        :return:
        """
        return self._generator.random()

    def uniform(self, lower_bound: Union[float, int] = 0.0, upper_bound: Union[float, int] = 1.0) -> float:
        """
        Generate a random number based on the uniform distribution.

        :param lower_bound: Lower bound of the uniform distribution.
        :param upper_bound: Upper bound of the uniform distribution.
        :return: Random number from the uniform distribution.
        """
        return self._generator.uniform(lower_bound, upper_bound)

    def randint(self, lower_bound: int, upper_bound: int) -> int:
        """
        Generate a random integer between lower_bound and upper_bound (inclusive).

        :param lower_bound: Lower bound of the range.
        :param upper_bound: Upper bound of the range.
        :return: Random integer between lower_bound and upper_bound.
        """
        return self._generator.randint(lower_bound, upper_bound)

    def choice(self, seq) -> Any:
        """
        Choose a random element from a non-empty sequence.

        :param seq: Sequence to choose from.
        :return: Randomly selected element from the sequence.
        """
        return self._generator.choice(seq)

    def choices(self, seq, k: int) -> Any:
        """
        Choose a random element from a non-empty sequence.

        :param seq: Sequence to choose from.
        :param k: Number of choices.
        :return: Randomly selected element from the sequence.
        """
        return self._generator.choices(seq, k=k)

    def shuffle(self, seq):
        """
        Randomly change the order of elements in a sequence.

        :param seq: Sequence to change.
        :return: Randomly selected element from the sequence.
        """
        return self._generator.shuffle(seq)

    def sample(self, s: Union[str, list, range], k: int = 1):
        """
        Samples k unique elements from s.

        :param s: A datatype that supports len and get item.
        :param k: The number of unique items to get.
        :return:
        """
        return self._generator.sample(s, k)

    def _transform_and_scale(self, x: float, transform_func: Callable[[float], float], lower_bound: Union[float, int],
                             upper_bound: Union[float, int]) -> Optional[float]:
        """
        Apply the transformation function to the random value and scale it within the given bounds.

        :param x: The initial random value (between 0 and 1).
        :param transform_func: The function to transform the value.
        :param lower_bound: The lower bound of the output range.
        :param upper_bound: The upper bound of the output range.
        :return: Transformed and scaled value.
        """
        try:
            transformed_value = max(min(transform_func(x), 1), 0)
        except Exception:
            print(f"Your chosen generator '{self._generator}' doesn't support this method.")
            return
        scaled_value = lower_bound + (upper_bound - lower_bound) * transformed_value
        return scaled_value

    def linear(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1, slope: float = 1.0,
               intercept: float = 1.0, invert: bool = False
               ) -> float:
        """
        Generate a random number based on a linear transformation and scale it within the specified bounds.

        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :param slope: Slope of the linear transformation.
        :param intercept: Intercept of the linear transformation.
        :param invert: Whether the results should be inverted to result in a falling curve instead.
        :return: Scaled random number from the linear transformation.
        """

        if invert:
            return self._transform_and_scale(self._generator.random(), lambda x: 1 - (slope * x + intercept), lower_bound, upper_bound)
        return self._transform_and_scale(self._generator.random(), lambda x: slope * x + intercept, lower_bound, upper_bound)

    def quadratic(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1, transform: float = 1.0,
                  invert: bool = False) -> float:
        """
        Generate a random number based on a quadratic distribution and scale it within the specified bounds.

        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :param transform: Lower means less high vales and more means more high values.
        :param invert: Whether the results should be inverted to result in a falling curve instead.
        :return: Scaled random number from the quadratic distribution.
        """

        if invert:
            return self._transform_and_scale(self._generator.random(), lambda x: 1 - (transform * x ** 2), lower_bound, upper_bound)
        return self._transform_and_scale(self._generator.random(), lambda x: transform * x ** 2, lower_bound, upper_bound)

    def cubic(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1, transform: float = 1.0,
              invert: bool = False) -> float:
        """
        Generate a random number based on a cubic distribution and scale it within the specified bounds.

        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :param transform: Lower means less high vales and more means more high values.
        :param invert: Whether the results should be inverted to result in a falling curve instead.
        :return: Scaled random number from the cubic distribution.
        """

        if invert:
            return self._transform_and_scale(self._generator.random(), lambda x: 1 - (transform * x ** 3), lower_bound, upper_bound)
        return self._transform_and_scale(self._generator.random(), lambda x: transform * x ** 3, lower_bound, upper_bound)

    def quartic(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1, transform: float = 1.0,
                invert: bool = False) -> float:
        """

        :param lower_bound:
        :param upper_bound:
        :param transform: Lower means less high vales and more means more high values.
        :param invert:
        """

        if invert:
            return self._transform_and_scale(self._generator.random(), lambda x: 1 - (transform * x ** 4), lower_bound, upper_bound)
        return self._transform_and_scale(self._generator.random(), lambda x: transform * x ** 4, lower_bound, upper_bound)

    def exponent(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1, exponent: float = 1.0,
                 transform: float = 1.0, invert: bool = False):
        """

        :param lower_bound:
        :param upper_bound:
        :param exponent:
        :param transform:
        :param invert:
        """

        if invert:
            return self._transform_and_scale(self._generator.random(), lambda x: 1 - (transform * x ** exponent), lower_bound, upper_bound)
        return self._transform_and_scale(self._generator.random(), lambda x: transform * x ** exponent, lower_bound, upper_bound)

    def gaussian(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1,
                 mu: Union[float, int] = 0, sigma: Union[float, int] = 1, invert: bool = False) -> float:
        """
        Generate a random number based on the normal (Gaussian) distribution and scale it within the specified bounds.

        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :param mu: Mean of the distribution.
        :param sigma: Standard deviation of the distribution.
        :param invert: Whether the results should be inverted to result in a falling curve instead.
        :return: Scaled random number from the normal distribution.
        """

        if invert:
            return self._transform_and_scale(self._generator.random(), lambda x: 1 - self._generator.gauss(mu, sigma),
                                             lower_bound, upper_bound)
        return self._transform_and_scale(self._generator.random(), lambda x: self._generator.gauss(mu, sigma),
                                         lower_bound, upper_bound)

    def exponential(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1,
                    multiplier: float = 1.0, invert: bool = False) -> float:
        """
        Generate a random number based on the exponential distribution and scale it within the specified bounds.

        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :param multiplier: Multiplier parameter x**mult e of the distribution.
        :param invert: Whether the results should be inverted to result in a falling curve instead.
        :return: Scaled random number from the exponential distribution.
        """

        if invert:
            return self._transform_and_scale(self._generator.random(), lambda x: 1 - (x ** (multiplier * math.e)),
                                             lower_bound, upper_bound)
        return self._transform_and_scale(self._generator.random(), lambda x: x ** (multiplier * math.e), lower_bound,
                                         upper_bound)

    def bias(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1, bias: float = 1.0,
                   invert: bool = False) -> float:
        """
        Generate a random number based on a biased distribution and scale it within the specified bounds.

        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :param bias: The bias of the distribution.
        :param invert: Whether the results should be inverted to result in a falling curve instead.
        :return: Scaled random number from the exponential distribution.
        """

        if invert:
            return self._transform_and_scale(self._generator.random(), lambda x: 1 - ((x * (x - bias) ** 3) / (x * (x - bias) ** 3 - x + 1)),
                                             lower_bound, upper_bound)
        return self._transform_and_scale(self._generator.random(), lambda x: (x * (x - bias) ** 3) / (x * (x - bias) ** 3 - x + 1),
                                         lower_bound, upper_bound)

    def sinusoidal(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1,
                   divisor: float = 1.0, invert: bool = False) -> float:
        """
        Generate a random number based on a sinusoidal distribution and scale it within the specified bounds.

        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :param divisor: How much the distribution should be scaled by.
        :param invert: Whether the results should be inverted to result in a falling curve instead.
        :return: Scaled random number from the sinusoidal distribution.
        """

        if invert:
            return self._transform_and_scale(self._generator.random(), lambda x: 1 - (0.5 * ((1 + math.sin(2 * math.pi * x - math.pi / 2)) / divisor)), lower_bound, upper_bound)
        return self._transform_and_scale(self._generator.random(), lambda x: 0.5 * ((1 + math.sin(2 * math.pi * x - math.pi / 2)) / divisor), lower_bound, upper_bound)

    def functional(self, math_func: Callable, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1
                   ) -> float:
        """
        Generate a random number based on a user-defined mathematical function and scale it within the specified bounds.

        :param math_func: Callable mathematical function that takes a random number between 0 and 1 and transforms it.
        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :return: Scaled transformed random number.
        """
        return self._transform_and_scale(self._generator.random(), math_func, lower_bound, upper_bound)

    def expo_var(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1, lambd: float = 1.0,
                 invert: bool = False) -> float:
        """
        Generate a random number based on the exponential distribution and scale it within the specified bounds.

        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :param lambd: Lambda parameter (1/mean) of the distribution.
        :param invert: Whether the results should be inverted to result in a falling curve instead.
        :return: Scaled random number from the exponential distribution.
        """

        if invert:
            return self._transform_and_scale(self._generator.random(),
                                             lambda x: 1 - self._generator.expovariate(lambd), lower_bound, upper_bound)
        return self._transform_and_scale(self._generator.random(),
                                         lambda x: self._generator.expovariate(lambd), lower_bound, upper_bound)

    def triangular(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1, mode: float = 0.5,
                   invert: bool = False) -> float:
        """
        Generate a random number based on a triangular distribution and scale it within the specified bounds.

        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :param mode: The value where the peak of the distribution occurs.
        :param invert: Whether the results should be inverted to result in a falling curve instead.
        :return: Scaled random number from the triangular distribution.
        """

        if invert:
            return self._transform_and_scale(self._generator.random(),
                                             lambda x: 1 - (self._generator.uniform(lower_bound, mode) if x < 0.5 else
                                                            self._generator.uniform(mode, upper_bound)), lower_bound,
                                             upper_bound)
        return self._transform_and_scale(self._generator.random(),
                                         lambda x: self._generator.uniform(lower_bound, mode) if x < 0.5 else
                                         self._generator.uniform(mode, upper_bound), lower_bound, upper_bound)

    def beta(self, alpha: float, beta: float, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1,
             invert: bool = False) -> float:
        """
        Generate a random number based on a beta distribution and scale it within the specified bounds.

        :param alpha: Alpha parameter of the beta distribution.
        :param beta: Beta parameter of the beta distribution.
        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :param invert: Whether the results should be inverted to result in a falling curve instead.
        :return: Scaled random number from the beta distribution.
        """

        if invert:
            return self._transform_and_scale(self._generator.random(),
                                             lambda x: 1 - self._generator.betavariate(alpha, beta),
                                             lower_bound, upper_bound)
        return self._transform_and_scale(self._generator.random(),
                                         lambda x: self._generator.betavariate(alpha, beta),
                                         lower_bound, upper_bound)

    def log_normal(self, mean: float, sigma: float, lower_bound: Union[float, int] = 0,
                   upper_bound: Union[float, int] = 1,
                   invert: bool = False) -> float:
        """
        Generate a random number based on a log-normal distribution and scale it within the specified bounds.

        :param mean: Mean of the underlying normal distribution.
        :param sigma: Standard deviation of the underlying normal distribution.
        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :param invert: Whether the results should be inverted to result in a falling curve instead.
        :return: Scaled random number from the log-normal distribution.
        """

        if invert:
            return self._transform_and_scale(self._generator.random(),
                                             lambda x: 1 - self._generator.lognormvariate(mean, sigma),
                                             lower_bound, upper_bound)
        return self._transform_and_scale(self._generator.random(),
                                         lambda x: self._generator.lognormvariate(mean, sigma),
                                         lower_bound, upper_bound)

    def piecewise_linear(self, breakpoints: List[float], slopes: List[float], lower_bound: Union[float, int] = 0,
                         upper_bound: Union[float, int] = 1, invert: bool = False) -> float:
        """
        Generate a random number based on a piecewise linear function and scale it within the specified bounds.

        :param breakpoints: List of breakpoints for the piecewise linear function.
        :param slopes: List of slopes for each segment of the piecewise linear function.
        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :param invert: Whether the results should be inverted to result in a falling curve instead.
        :return: Scaled random number from the piecewise linear function.
        """

        def _piecewise(x):
            for i, breakpoint in enumerate(breakpoints):
                if x < breakpoint:
                    return slopes[i] * (x - (breakpoints[i - 1] if i > 0 else 0))
            return slopes[-1] * (x - breakpoints[-1])

        if invert:
            return self._transform_and_scale(self._generator.random(), lambda x: 1 - _piecewise(x), lower_bound,
                                             upper_bound)
        return self._transform_and_scale(self._generator.random(), lambda x: _piecewise(x), lower_bound,
                                         upper_bound)

    def exponential_e(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1,
                      exponent: float = -1.0, invert: bool = False) -> float:
        """
        Generate a random number based on the e^x exponential distribution and scale it within the specified bounds.

        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :param exponent: Exponent parameter for the e^x distribution.
        :param invert: Whether the results should be inverted to result in a falling curve instead.
        :return: Scaled random number from the e^x exponential distribution.
        """

        if invert:
            return self._transform_and_scale(self._generator.random(), lambda x: 1 - (math.exp(exponent * x) - 1),
                                             lower_bound, upper_bound)
        return self._transform_and_scale(self._generator.random(), lambda x: math.exp(exponent * x) - 1,
                                         lower_bound, upper_bound)

    def weibull(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1, alpha: float = 1.0, beta: float = 1.0,
                invert: bool = False) -> float:
        """
        Generate a random number based on a Weibull distribution and scale it within the specified bounds.

        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :param alpha: Shape parameter of the Weibull distribution.
        :param beta: Scale parameter of the Weibull distribution.
        :param invert: Whether the results should be inverted to result in a falling curve instead.
        :return: Scaled random number from the Weibull distribution.
        """

        if invert:
            return self._transform_and_scale(self._generator.random(), lambda x: 1 - (self._generator.weibullvariate(alpha, beta)),
                                             lower_bound, upper_bound)
        return self._transform_and_scale(self._generator.random(), lambda x: self._generator.weibullvariate(alpha, beta),
                                         lower_bound, upper_bound)

    def gamma(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1, alpha: float = 1.0, beta: float = 1.0,
              invert: bool = False) -> float:
        """
        Generate a random number based on a Gamma distribution and scale it within the specified bounds.

        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :param alpha: Shape parameter of the Gamma distribution.
        :param beta: Scale parameter of the Gamma distribution.
        :param invert: Whether the results should be inverted to result in a falling curve instead.
        :return: Scaled random number from the Gamma distribution.
        """

        if invert:
            return self._transform_and_scale(self._generator.random(), lambda x: 1 - (self._generator.gammavariate(alpha, beta)),
                                             lower_bound, upper_bound)
        return self._transform_and_scale(self._generator.random(), lambda x: self._generator.gammavariate(alpha, beta),
                                         lower_bound, upper_bound)

    def cauchy(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1, median: float = 0.0, scale: float = 1.0,
               invert: bool = False) -> float:
        """
        Generate a random number based on a Cauchy distribution and scale it within the specified bounds.

        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :param median: Median of the distribution.
        :param scale: Scale parameter of the distribution.
        :param invert: Whether the results should be inverted to result in a falling curve instead.
        :return: Scaled random number from the Cauchy distribution.
        """

        if invert:
            return self._transform_and_scale(self._generator.random(), lambda x: 1 - (self._generator.standard_cauchy() * scale + median),
                                             lower_bound, upper_bound)
        return self._transform_and_scale(self._generator.random(), lambda x: self._generator.standard_cauchy() * scale + median,
                                         lower_bound, upper_bound)

    def pareto(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1, alpha: float = 1.0,
               invert: bool = False) -> float:
        """
        Generate a random number based on a Pareto distribution and scale it within the specified bounds.

        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :param alpha: Shape parameter of the Pareto distribution.
        :param invert: Whether the results should be inverted to result in a falling curve instead.
        :return: Scaled random number from the Pareto distribution.
        """

        if invert:
            return self._transform_and_scale(self._generator.random(), lambda x: 1 - (self._generator.paretovariate(alpha)),
                                             lower_bound, upper_bound)
        return self._transform_and_scale(self._generator.random(), lambda x: self._generator.paretovariate(alpha),
                                         lower_bound, upper_bound)

    def polynomial(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1, coefficients: List[float] = [1],
                   invert: bool = False) -> float:
        """
        Generate a random number based on a custom polynomial distribution and scale it within the specified bounds.

        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :param coefficients: Coefficients of the polynomial, ordered from the highest degree to the constant term.
        :param invert: Whether the results should be inverted to result in a falling curve instead.
        :return: Scaled random number from the polynomial distribution.
        """
        def polynomial_func(x):
            return sum(coeff * (x ** i) for i, coeff in enumerate(reversed(coefficients)))

        if invert:
            return self._transform_and_scale(self._generator.random(), lambda x: 1 - polynomial_func(x),
                                             lower_bound, upper_bound)
        return self._transform_and_scale(self._generator.random(), lambda x: polynomial_func(x), lower_bound,
                                         upper_bound)


if __name__ == "__main__":
    for generator in ("random", "os", "sys_random", "secrets"):
        # Test generator
        print(f"Testing with {generator} generator:")
        rng = WeightedRandom(generator)

        # Existing tests
        print("Gaussian:", rng.gaussian(0, 1, 0, 1))
        print("Cubic:", rng.cubic(0, 1))
        print("Exponential:", rng.exponential(0, 1, 1.0))
        print("Functional (x^2):", rng.functional(lambda x: x ** 2, 0, 1))
        print("Uniform:", rng.uniform(1, 10))
        print("RandInt:", rng.randint(1, 10))
        print("Choice:", rng.choice([1, 2, 3, 4, 5]))
        print("Linear Transform:", rng.linear(0, 1, 2, 1))
        print("Triangular:", rng.triangular(0, 1, 0.5))
        print("Beta:", rng.beta(2, 5, 0, 1))
        print("Log Normal:", rng.log_normal(0, 1, 0, 1))
        print("Sinusoidal:", rng.sinusoidal(0, 1))
        print("Piecewise Linear:", rng.piecewise_linear([0.3, 0.7], [1, -1], 0, 1))

        # New tests
        print("Expo Var:", rng.expo_var(0, 1, 1.0))
        print("Weibull:", rng.weibull(0, 1, 1.0, 1.0))
        print("Gamma:", rng.gamma(0, 1, 1.0, 1.0))
        print("Cauchy:", rng.cauchy(0, 1, 0.0, 1.0))
        print("Pareto:", rng.pareto(0, 1, 1.0))
        print("Polynomial (x^3 + 2x + 1):", rng.polynomial(0, 1, [1, 2, 0, 1]))
        print("Exponential e^x:", rng.exponential_e(0, 1, 1.0))

    print("\nCustom exponent: ", round(rng.exponential(0.1, 10, 5.0), 1))
