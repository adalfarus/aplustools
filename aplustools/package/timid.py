from time import time, perf_counter_ns, monotonic_ns
from datetime import timedelta, datetime
from typing import Optional, Type, Union
from timeit import default_timer


class Format:
    WEEKS = 0
    DAYS = 1
    HOURS = 2
    MINUTES = 3
    SECONDS = 4
    MILISEC = 5
    MICROSEC = 6


class TimidTimer:
    """Uses the timeit.default_timer function to calculate passed time."""
    def __init__(self, start_at_seconds: int = 0,
                 start_now: bool = True):
        self.start_time = float(start_at_seconds)
        self.end_time: Optional[float] = None
        self.paused_at: Optional[float] = None
        self.paused_time: float = 0

        if start_now:
            self.start()

    def start(self) -> float:
        if self.paused_at is not None:
            self.paused_time += default_timer() - self.paused_at
            self.paused_at = None
        self.start_time = default_timer() + self.start_time - self.paused_time
        return self.start_time

    def pause(self) -> float:
        if self.paused_at is None:
            self.paused_at = default_timer()
        return self.paused_at

    def resume(self):
        if self.paused_at is not None:
            self.paused_time += default_timer() - self.paused_at
            self.paused_at = None
        return self.start_time

    def end(self, return_end_time: bool = False) -> Union[timedelta, float]:
        if self.paused_at is not None:
            self.resume()
        self.end_time = default_timer()
        td = timedelta(seconds=self.end_time - self.start_time - self.paused_time)

        if not return_end_time:
            return td
        else:
            return self.end_time

    def tick(self, return_time: bool = False) -> Union[timedelta, float]:
        """Return how much time has passed till the start."""
        if not return_time:
            return timedelta(seconds=default_timer() - self.start_time)
        else:
            return default_timer()

    def tock(self, return_time: bool = False) -> Union[timedelta, float]:
        """Returns how much time has passed till the last tock."""
        last_time = self.end_time or self.start_time
        self.end_time = default_timer()

        if not return_time:
            return timedelta(seconds=self.end_time - last_time)
        else:
            return last_time

    @staticmethod
    def test_delay(return_end_time: bool = False) -> Union[timedelta, float]:
        return TimidTimer().end(return_end_time)

    @staticmethod
    def test_tock_delay(return_end_time: bool = False) -> Union[timedelta, float]:
        timer = TimidTimer()
        timer.tock()
        return timer.end(return_end_time)

    @staticmethod
    def get_readable(td: timedelta, format_to: int = Format.SECONDS) -> str:
        total_seconds = int(td.total_seconds())
        micros = td.microseconds

        # Select the correct level of detail based on the format
        if format_to == Format.WEEKS:
            weeks = total_seconds // 604800
            days = (total_seconds % 604800) / 86400
            return f"{weeks} weeks, {days} days"

        elif format_to == Format.DAYS:
            days = total_seconds // 86400
            hours = (total_seconds % 86400) / 3600
            return f"{days} days, {hours} hours"

        elif format_to == Format.HOURS:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) / 60
            return f"{hours} hours, {minutes} minutes"

        elif format_to == Format.MINUTES:
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes} minutes, {seconds} seconds"

        elif format_to == Format.SECONDS:
            return f"{total_seconds} seconds, {micros / 1000} milliseconds"

        elif format_to == Format.MILISEC:
            millisecs = (total_seconds * 1000) + (micros // 1000)
            return f"{millisecs} milliseconds, {micros % 1000} microseconds"

        elif format_to == Format.MICROSEC:
            microsecs = (total_seconds * 1000000) + micros
            return f"{microsecs} microseconds"

        return "Invalid format specified"

    @staticmethod
    def time(func):
        def wrapper(*args, **kwargs):
            timer = TimidTimer(start_now=True)
            result = func(*args, **kwargs)
            elapsed = timer.end()
            print(f"Function {func.__name__} took {timer.get_readable(elapsed)} to complete.")
            return result
        return wrapper


class TimidTimer2:
    """Uses the time.perf_counter_ns function to calculate passed time."""
    def __init__(self, start_seconds: int = 0,
                 start_now: bool = True):
        self.starter = start_seconds
        self.ender: Optional[int] = None
        self.timedelta: Optional[timedelta] = None

        if start_now:
            self.start()

    def start(self) -> int:
        self.starter = perf_counter_ns() + int(self.starter * 1e+9)
        return self.starter

    def end(self, return_end_time: bool = False) -> Union[timedelta, int]:
        self.ender = perf_counter_ns()
        self.timedelta = timedelta(microseconds=(self.ender - self.starter) / 1000)

        if not return_end_time:
            return self.timedelta
        else:
            return self.ender

    def tick(self, return_time: bool = False) -> Union[timedelta, int]:
        """Return how much time has passed till the start."""
        if not return_time:
            return timedelta(microseconds=(perf_counter_ns() - self.starter) / 1000)
        else:
            return perf_counter_ns()

    def tock(self, return_time: bool = False) -> Union[timedelta, int]:
        """Returns how much time has passed till the last tock."""
        last_time = self.ender or self.starter
        self.ender = perf_counter_ns()

        if not return_time:
            return timedelta(microseconds=(self.ender - last_time) / 1000)
        else:
            return last_time

    @staticmethod
    def test_delay(return_end_time: bool = False) -> Union[timedelta, int]:
        return TimidTimer2().end(return_end_time)

    @staticmethod
    def test_tock_delay(return_end_time: bool = False) -> Union[timedelta, int]:
        timer = TimidTimer2()
        timer.tock()
        return timer.end(return_end_time)

    @staticmethod
    def time() -> float:
        return perf_counter_ns() / 1e+9


class NormalTimer:
    """Uses the time.time function to calculate passed time."""
    def __init__(self, start_seconds: int = 0,
                 start_now: bool = True):
        self.starter = float(start_seconds)
        self.stopper: Optional[float] = None
        self.timedelta: Optional[timedelta] = None

        if start_now:
            self.start()

    def start(self) -> float:
        self.starter = time() + self.starter
        return self.starter

    def round(self) -> timedelta:
        last_time = self.stopper or self.starter
        self.stopper = time()

        return timedelta(seconds=self.stopper - last_time)

    def stop(self) -> timedelta:
        self.stopper = time()
        return timedelta(seconds=self.stopper - self.starter)

    @staticmethod
    def time() -> datetime:
        return datetime.today()


class LazyTimer:
    """Uses the time.monotonic_ns function to calculate passed time."""
    def __init__(self, start_seconds: int = 0,
                 start_now: bool = True):
        self.starter = start_seconds
        self.stopper: Optional[int] = None
        self.timedelta: Optional[timedelta] = None

        if start_now:
            self.start()

    def start(self) -> int:
        self.starter = monotonic_ns() + int(self.starter * 1e+9)
        return self.starter

    def round(self) -> timedelta:
        last_time = self.stopper or self.starter
        self.stopper = monotonic_ns()

        return timedelta(seconds=(self.stopper - last_time) / 1e+9)

    def stop(self) -> timedelta:
        self.stopper = monotonic_ns()
        return timedelta(seconds=(self.stopper - self.starter) / 1e+9)

    @staticmethod
    def time() -> int:
        return int(monotonic_ns() / 1e+9)


# Timer
"""
class TimerOut:
    WEEKS = 0
    DAYS = 1
    HOURS = 2
    MINUTES = 3
    SECONDS = 4
    MILISEC = 5
    MICROSEC = 6


class TimeDisplay:
    def __init__(self, td: timedelta, out: TimerOut):
        raise NotImplementedError("This class isn't implemented yet, please visit back in version 1.5 or later.")
        self.microsec = td.microseconds
        self.seconds = td.seconds
        self.days = td.days

        self.repr = ""

    def __repr__(self):
        return "TimerDisplay(\
                \
                )"


class Timer:
    def __init__(self, output_target: Optional[TimerOut] = TimerOut.SECONDS,
                 start_now: Optional[bool] = True):
        raise NotImplementedError("This class isn't implemented yet, please visit back in version 1.5 or later.")
        self.output_target = output_target

        self.start_t = None
        self.stop_t = None
        self.t_d = None

        if start_now:
            self.start()

    @staticmethod
    def test_delay() -> timedelta:
        return TimidTimer().end()

    def start(self) -> float:
        return
        self.start_t = timer()
        return self.start_t

    @staticmethod
    def time() -> float:
        return
        return timer()

    def tick(self, return_time: Optional[bool] = False) -> Union[timedelta, float]:
        return
        "Return how much time has passed till the start."
        if not return_time:
            return timedelta(seconds=timer() - self.start_t)
        else:
            return timer()

    def tock(self, return_time: Optional[bool] = False) -> Union[timedelta, float]:
        return
        "Returns how much time has passed till the last tock."
        time = self.stop_t or self.start_t
        self.stop_t = time()

        if not return_time:
            return timedelta(seconds=time - self.stop_t)
        else:
            return time

    def end(self, return_end_time: Optional[bool] = False) -> Union[timedelta, float]:
        return
        self.stop_t = timer()
        self.t_d = timedelta(seconds=self.stop_t-self.start_t)

        if not return_end_time:
            return self.t_d
        else:
            return self.stop_t
"""


def local_test():
    try:
        def test_delay(cls: Type[Union[NormalTimer, LazyTimer]]) -> timedelta:
            timer = TimidTimer2()
            cls().stop()
            return timer.end() - timedelta(microseconds=1)

        print("TimidTimerDelay", TimidTimer.test_delay())
        print("TimidTimer2Delay", TimidTimer2.test_delay())
        print("All other timers are too inaccurate as to measure them with themselves, \
so we measure them with TimidTimer2 and subtract the average delay.")
        print("NormalTimerDelay", test_delay(NormalTimer))
        print("LazyTimerDelay", test_delay(LazyTimer))

        print("\nTimer Test, using 1 million passes.")
        t_timer = TimidTimer()
        t_timer2 = TimidTimer2()
        n_timer = NormalTimer()
        l_timer = LazyTimer()
        for _ in range(1000000):
            pass
        print("TimidTimer", t_timer.end())
        print("TimidTimer2", t_timer2.end())
        print("NormalTimer", n_timer.stop())
        print("LazyTimer", l_timer.stop())

        print("\nTimer Test, using 1 second sleep.")
        import time as t
        t_timer = TimidTimer()
        t_timer2 = TimidTimer2()
        n_timer = NormalTimer()
        l_timer = LazyTimer()
        t.sleep(1)
        print("TimidTimer", t_timer.end())
        print("TimidTimer2", t_timer2.end())
        print("NormalTimer", n_timer.stop())
        print("LazyTimer", l_timer.stop())

        print("\nTimidTimer delay test 2")
        timid_t = TimidTimer()
        for i in range(10):
            print(timid_t.tock())

        print("\nTimidTimer2 delay test 2")
        timid_t2 = TimidTimer2()
        for i in range(10):
            print(timid_t2.tock())

        print("\nNormalTimer delay test 2")
        normal_t = NormalTimer()
        for i in range(10):
            print(normal_t.round())

        print("\nLazyTimer delay test 2")
        lazy_t = LazyTimer()
        for i in range(10):
            print(lazy_t.round())
    except Exception as e:
        print(f"Exception occurred {e}.")
        return False
    print("Test completed successfully.")
    return True


if __name__ == "__main__":
    local_test()
