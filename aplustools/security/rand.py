from typing import Callable, Type, Protocol, Union, Any, List, Literal
import secrets
import random
import math
import os


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
    def generate_random_string(cls, length: int, char_set: str = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ") -> str:
        return ''.join(cls.choice(char_set) for _ in range(length))


def os_random() -> float:
    return int.from_bytes(os.urandom(7), "big") / (1 << 56)


def secrets_random() -> float:
    return secrets.randbits(56) / (1 << 56)


OSRandomGenerator = CustomRandomGenerator.setup_random_func(os_random)
SecretsRandomGenerator = CustomRandomGenerator.setup_random_func(secrets_random)


class WeightedRandom:
    def __init__(self, generator: Literal["random", "os", "sys_random", "secrets"] = "sys_random"):
        self._generator = {"random": random, "os": OSRandomGenerator, "sys_random": secrets.SystemRandom(),
                           "secrets": SecretsRandomGenerator}[generator]

    def random(self) -> float:
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
        return self._generator.choices(seq, k)

    def shuffle(self, seq):
        """
        Randomly change the order of elements in a sequence.

        :param seq: Sequence to change.
        :return: Randomly selected element from the sequence.
        """
        return self._generator.shuffle(seq)

    def sample(self, s: Union[str, list], k: int):
        return self._generator.sample(s, k)

    @staticmethod
    def _transform_and_scale(x: float, transform_func: Callable[[float], float], lower_bound: Union[float, int],
                             upper_bound: Union[float, int]) -> float:
        """
        Apply the transformation function to the random value and scale it within the given bounds.

        :param x: The initial random value (between 0 and 1).
        :param transform_func: The function to transform the value.
        :param lower_bound: The lower bound of the output range.
        :param upper_bound: The upper bound of the output range.
        :return: Transformed and scaled value.
        """
        transformed_value = transform_func(x)
        scaled_value = lower_bound + (upper_bound - lower_bound) * transformed_value
        return scaled_value

    def gaussian(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1,
                 mu: Union[float, int] = 0, sigma: Union[float, int] = 1) -> float:
        """
        Generate a random number based on the normal (Gaussian) distribution and scale it within the specified bounds.

        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :param mu: Mean of the distribution.
        :param sigma: Standard deviation of the distribution.
        :return: Scaled random number from the normal distribution.
        """
        return self._transform_and_scale(self._generator.random(), lambda x: self._generator.gauss(mu, sigma),
                                         lower_bound, upper_bound)

    def quadratic(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1) -> float:
        """
        Generate a random number based on a quadratic distribution and scale it within the specified bounds.

        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :return: Scaled random number from the quadratic distribution.
        """
        return self._transform_and_scale(self._generator.random(), lambda x: x ** 2, lower_bound, upper_bound)

    def cubic(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1) -> float:
        """
        Generate a random number based on a cubic distribution and scale it within the specified bounds.

        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :return: Scaled random number from the cubic distribution.
        """
        return self._transform_and_scale(self._generator.random(), lambda x: x ** 3, lower_bound, upper_bound)

    def exponential(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1, lambd: float = 1.0
                    ) -> float:
        """
        Generate a random number based on the exponential distribution and scale it within the specified bounds.

        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :param lambd: Lambda parameter (1/mean) of the distribution.
        :return: Scaled random number from the exponential distribution.
        """
        return self._transform_and_scale(self._generator.random(), lambda x: self._generator.expovariate(lambd),
                                         lower_bound, upper_bound)

    def falling(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1) -> float:
        """
        Generate a random number based on a falling distribution and scale it within the specified bounds.
        """
        return self._transform_and_scale(self._generator.random(), lambda x: 1 - x, lower_bound, upper_bound)

    def sloping(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1) -> float:
        """
        Generate a random number based on a sloping distribution and scale it within the specified bounds.
        """
        return self._transform_and_scale(self._generator.random(), lambda x: x ** 2, lower_bound, upper_bound)

    def exponential_falling(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1,
                            lambd: float = 1.0) -> float:
        """
        Generate a random number based on a falling exponential distribution and scale it within the specified bounds.
        """
        return self._transform_and_scale(self._generator.random(), lambda x: 1 - self._generator.expovariate(lambd), lower_bound, upper_bound)

    def quadratic_falling(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1) -> float:
        """
        Generate a random number based on a quadratic distribution and scale it within the specified bounds.

        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :return: Scaled random number from the quadratic distribution.
        """
        return self._transform_and_scale(self._generator.random(), lambda x: 1 - x ** 2, lower_bound, upper_bound)

    def cubic_falling(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1) -> float:
        """
        Generate a random number based on a falling cubic distribution and scale it within the specified bounds.
        """
        return self._transform_and_scale(self._generator.random(), lambda x: 1 - x ** 3, lower_bound, upper_bound)

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

    def linear_transform(self, slope: float, intercept: float, lower_bound: Union[float, int] = 0,
                         upper_bound: Union[float, int] = 1) -> float:
        """
        Generate a random number based on a linear transformation and scale it within the specified bounds.

        :param slope: Slope of the linear transformation.
        :param intercept: Intercept of the linear transformation.
        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :return: Scaled random number from the linear transformation.
        """
        return self._transform_and_scale(self._generator.random(), lambda x: slope * x + intercept, lower_bound, upper_bound)

    def triangular(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1, mode: float = 0.5
                   ) -> float:
        """
        Generate a random number based on a triangular distribution and scale it within the specified bounds.

        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :param mode: The value where the peak of the distribution occurs.
        :return: Scaled random number from the triangular distribution.
        """
        return self._transform_and_scale(self._generator.random(), lambda x: self._generator.uniform(lower_bound, mode) if x < 0.5 else self._generator.uniform(mode, upper_bound), lower_bound, upper_bound)

    def beta(self, alpha: float, beta: float, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1
             ) -> float:
        """
        Generate a random number based on a beta distribution and scale it within the specified bounds.

        :param alpha: Alpha parameter of the beta distribution.
        :param beta: Beta parameter of the beta distribution.
        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :return: Scaled random number from the beta distribution.
        """
        return self._transform_and_scale(self._generator.random(), lambda x: self._generator.betavariate(alpha, beta), lower_bound, upper_bound)

    def log_normal(self, mean: float, sigma: float, lower_bound: Union[float, int] = 0,
                   upper_bound: Union[float, int] = 1) -> float:
        """
        Generate a random number based on a log-normal distribution and scale it within the specified bounds.

        :param mean: Mean of the underlying normal distribution.
        :param sigma: Standard deviation of the underlying normal distribution.
        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :return: Scaled random number from the log-normal distribution.
        """
        return self._transform_and_scale(self._generator.random(), lambda x: self._generator.lognormvariate(mean, sigma), lower_bound, upper_bound)

    def sinusoidal(self, lower_bound: Union[float, int] = 0, upper_bound: Union[float, int] = 1) -> float:
        """
        Generate a random number based on a sinusoidal distribution and scale it within the specified bounds.

        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :return: Scaled random number from the sinusoidal distribution.
        """
        return self._transform_and_scale(self._generator.random(), lambda x: 0.5 * (1 + math.sin(2 * math.pi * x - math.pi / 2)), lower_bound, upper_bound)

    def piecewise_linear(self, breakpoints: List[float], slopes: List[float], lower_bound: Union[float, int] = 0,
                         upper_bound: Union[float, int] = 1) -> float:
        """
        Generate a random number based on a piecewise linear function and scale it within the specified bounds.

        :param breakpoints: List of breakpoints for the piecewise linear function.
        :param slopes: List of slopes for each segment of the piecewise linear function.
        :param lower_bound: Lower bound of the scaled range.
        :param upper_bound: Upper bound of the scaled range.
        :return: Scaled random number from the piecewise linear function.
        """
        def piecewise(x):
            for i, breakpoint in enumerate(breakpoints):
                if x < breakpoint:
                    return slopes[i] * (x - (breakpoints[i-1] if i > 0 else 0))
            return slopes[-1] * (x - breakpoints[-1])

        return self._transform_and_scale(self._generator.random(), piecewise, lower_bound, upper_bound)


if __name__ == "__main__":
    for generator in ("random", "os", "sys_random", "secrets"):
        # Test generator
        print(f"Testing with {generator} generator:")
        rng = WeightedRandom(generator)
        print("Gaussian:", rng.gaussian(0, 1, 0, 1))
        print("Cubic:", rng.cubic(0, 1))
        print("Exponential:", rng.exponential(0, 1, 1.0))
        print("Falling:", rng.falling(0, 1))
        print("Sloping:", rng.sloping(0, 1))
        print("Exponential Falling:", rng.exponential_falling(0, 1, 1.0))
        print("Cubic Falling:", rng.cubic_falling(0, 1))
        print("Functional (x^2):", rng.functional(lambda x: x ** 2, 0, 1))
        print("Uniform:", rng.uniform(1, 10))
        print("RandInt:", rng.randint(1, 10))
        print("Choice:", rng.choice([1, 2, 3, 4, 5]))
        print("Linear Transform:", rng.linear_transform(2, 1, 0, 1))
        print("Triangular:", rng.triangular(0, 1, 0.5))
        print("Beta:", rng.beta(2, 5, 0, 1))
        print("Log Normal:", rng.log_normal(0, 1, 0, 1))
        print("Sinusoidal:", rng.sinusoidal(0, 1))
        print("Piecewise Linear:", rng.piecewise_linear([0.3, 0.7], [1, -1], 0, 1))

    print("\nCustom exponent: ", round(rng.exponential(0.1, 10, 5.0), 1))
