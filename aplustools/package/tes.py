from aplustools.package.timid import TimidTimer
from datetime import timedelta
import time

# Setup your own timer class easily
mySpecialTimer = TimidTimer.setup_timer_func(time.time, to_nanosecond_multiplier=1e9)

timer = TimidTimer()

# Measure the average elapsed time over different iterations
for _ in range(1):
    timer.wait_ms(1000)
    timer.tock()
print("Average 1 second sleep extra delay: ", timer.average() - timedelta(seconds=1))

# Use multiple timers in one timer object using the index
with timer.enter(index=1):
    time.sleep(1)

# Use it for timed function execution
timer.start(index=1)  # The context manager automatically ends the timer, so we can reuse index 1 here
timer.shoot(interval=1, function=lambda: print("Shooting", timer.tock(index=1, return_datetime=True)), iterations=3)
print(timer.end())  # End the timer at index 0 that starts when the timer object gets created


def linear_time(n):
    # O(N) - Simple loop with linear complexity
    for _ in range(n):
        pass


def create_simple_input_generator():
    return ((tuple([n]), {}) for n in range(1, 100_001, 100))


# Measure the average time complexity of a function e.g. O(N)
print(timer.complexity(linear_time, create_simple_input_generator()))

# You can also show the curve
from matplotlib import pyplot

print(timer.complexity(linear_time, create_simple_input_generator(), matplotlib_pyplt=pyplot))


def complex_func(n, m, power=2):
    sum(i ** power for i in range(n)) + sum(j ** power for j in range(m))


def varying_func(n, multiplier=1):
    return sum(i * multiplier for i in range(n))


# Complex input generator with multiple arguments and keyword arguments
complex_input_generator = (
    (tuple([n, n // 2]), {'power': 2}) for n in range(1, 101)
)

# Complex input generator with varying keyword arguments
varying_input_generator = (
    (tuple([n]), {'multiplier': (n % 3 + 1)}) for n in range(1, 101)
)

print(f"Estimated Time Complexity for complex_func: {timer.complexity(complex_func, complex_input_generator)}")
print(f"Estimated Time Complexity for varying_func: {timer.complexity(varying_func, varying_input_generator)}")