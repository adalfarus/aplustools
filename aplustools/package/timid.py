import sys
from typing import Callable, Union, List, Tuple, Optional, Type
from datetime import timedelta, datetime
from timeit import default_timer
import threading
import time


class TimeFormat:
    WEEKS = 0
    DAYS = 1
    HOURS = 2
    MINUTES = 3
    SECONDS = 4
    MILISEC = 5
    MICROSEC = 6


class TimidTimer:
    """If a time value is not specified as something specific, it's in seconds."""
    def __init__(self, start_at: Union[float, int] = 0, start_now: bool = True):
        self._fires: List[Tuple[Optional[threading.Thread], Optional[threading.Event]]] = []
        self._times: List[Optional[Tuple[Union[float, int]], Optional[Union[float, int]], Optional[Union[float, int]], Union[float, int]]] = []
        self._tick_tocks: List[List[Tuple[Union[float, int], Union[float, int]]]] = []
        self._exit_index = 0

        if start_now:
            self.warmup()
            self.start(start_at=start_at)

    @staticmethod
    def _time() -> Union[float, int]:
        return default_timer() * 1e9

    def start(self, index: int = None, start_at: Union[float, int] = 0):
        start_time = self._time()
        if index and index < len(self._times):
            self.resume(index)
            return
        if index is None:
            index = len(self._times)
        # Ensure the _times list has enough elements
        while len(self._times) < index:
            self._times.append((None, None, None, 0))
        # Ensure the _tick_tocks list has enough elements
        while len(self._tick_tocks) < index:
            self._tick_tocks.append([])
        # Insert or replace the elements at the specified index
        if index < len(self._times) and self._times[index] == (None, None, None, 0):
            self._times[index] = (start_time + (start_at * 1e9), None, None, 0)
            self._tick_tocks[index] = []
        else:
            self._times.insert(index, (start_time + (start_at * 1e9), None, None, 0))
            self._tick_tocks.insert(index, [])

    def pause(self, index: Optional[int] = None, for_seconds: Optional[int] = None):
        pause_time = self._time()
        index = index or 0  # If it's 0 it just sets it to 0 so it's okay.
        start, end, paused_at, paused_time = self._times[index]
        if for_seconds:
            self._times[index] = (start, end, None, paused_time + (for_seconds * 1e9))
        else:
            self._times[index] = (start, end, pause_time, paused_time)

    def resume(self, index: Optional[int] = None):
        resumed_time = self._time()
        index = index or 0  # If it's 0 it just sets it to 0 so it's okay.
        start, end, paused_at, paused_time = self._times[index]
        if paused_at is not None:
            self._times[index] = (start, end, None, paused_time + (resumed_time - paused_at))

    def stop(self, index: Optional[int] = None):
        end_time = self._time()
        index = index or 0  # If it's 0 it just sets it to 0 so it's okay.
        if index >= len(self._times):
            raise IndexError(f"Index {index} doesn't exist in {self._times}.")
        start, end, paused_at, paused_time = self._times[index]
        if paused_time is not None:
            self.resume()
        _, __, ___, paused_time = self._times[index]
        self._times[index] = (start, end_time, None, paused_time)

    def end(self, index: Optional[int] = None, return_datetime: bool = True) -> Optional[timedelta]:
        end_time = self._time()
        index = index or 0  # If it's 0 it just sets it to 0 so it's okay.
        if index >= len(self._times):
            raise IndexError(f"Index {index} doesn't exist in {self._times}.")
        start, _, paused_at, __ = self._times[index]
        if paused_at is not None:
            self.resume(index)
        _, __, ___, paused_time = self._times[index]
        del self._times[index]
        del self._tick_tocks[index]
        if return_datetime:
            elapsed_time = end_time - start - paused_time
            return timedelta(microseconds=elapsed_time / 1000)

    def tick(self, index: Optional[int] = None, return_datetime: bool = True) -> Optional[timedelta]:
        """Return how much time has passed till the start."""
        tick_time = self._time()
        index = index or 0  # If it's 0 it just sets it to 0 so it's okay.
        if index >= len(self._times):
            raise IndexError(f"Index {index} doesn't exist in {self._times}.")
        start, _, __, ___ = self._times[index]
        self._tick_tocks[index].append((start, tick_time))
        if return_datetime:
            return timedelta(microseconds=(tick_time - start) / 1000)

    def tock(self, index: Optional[int] = None, return_datetime: bool = True) -> Optional[timedelta]:
        """Returns how much time has passed till the last tock."""
        tock_time = self._time()
        index = index or 0  # If it's 0 it just sets it to 0 so it's okay.
        if index >= len(self._times):
            raise IndexError(f"Index {index} doesn't exist in {self._times}.")
        start, end, paused_at, paused_time = self._times[index]

        last_time = end or start
        end = tock_time
        self._times[index] = (start, end, paused_at, paused_time)
        self._tick_tocks[index].append((last_time, end))
        if return_datetime:
            return timedelta(microseconds=(end - last_time) / 1000)

    def tally(self, index: Optional[int] = None) -> timedelta:
        """Return the total time recorded across all ticks and tocks."""
        index = index or 0  # If it's 0 it just sets it to 0 so it's okay.
        start, end, _, __ = self._times[index]
        tick_tocks = self._tick_tocks[index].copy()
        if end is not None and len(tick_tocks) > 0:
            tick_tocks.append((tick_tocks[-1][1], end))
        elif end is not None:
            tick_tocks.append((start, end))
        total_time = sum((end - start for start, end in tick_tocks))
        return timedelta(microseconds=total_time / 1000)

    def average(self, index: Optional[int] = None) -> timedelta:
        """Calculate the average time across all recorded ticks and tocks."""
        index = index or 0  # If it's 0 it just sets it to 0 so it's okay.
        _, end, __, ___ = self._times[index]
        tick_tocks = self._tick_tocks[index].copy()
        return self.tally() / max(1, len(tick_tocks) + (1 if end is not None and end != ([(0, 0)] + tick_tocks)[-1][1] else 0))

    def warmup(self, rounds: int = 3):
        for _ in range(rounds):
            self.start()
            self.end()

    @classmethod
    def setup_timer_func(cls, func: Callable, to_nanosecond_multiplier: Union[float, int]) -> Type["TimidTimer"]:
        NewClass = type('TimidTimerModified', (cls,), {
            '_time': lambda self=None: func() * to_nanosecond_multiplier
        })
        return NewClass

    @classmethod
    def _trigger(cls, interval: Union[float, int], function, args: tuple, kwargs: dict, iterations: int,
                 stop_event: threading.Event = threading.Event()):
        cls.wait(interval)
        while not stop_event.is_set():
            if iterations == 0:
                break
            try:
                function(*args, **kwargs)
            except Exception as e:
                print(f"Error in _trigger thread: {e}")
            cls.wait(interval)
            iterations -= 1

    @classmethod
    def _trigger_ms(cls, interval_ms: Union[float, int], function, args: tuple, kwargs: dict, iterations: int,
                    stop_event: threading.Event = threading.Event()):
        cls.wait_ms(interval_ms)
        while not stop_event.is_set():
            if iterations == 0:
                break
            try:
                function(*args, **kwargs)
            except Exception as e:
                print(f"Error in _trigger thread: {e}")
            cls.wait_ms(interval_ms)
            iterations -= 1

    @classmethod
    def single_shot(cls, wait_time: Union[float, int], function: Callable, args: tuple = (),
                    kwargs: Optional[dict] = None):
        if kwargs is None:
            kwargs = {}
        threading.Thread(target=cls._trigger, args=(wait_time, function, args, kwargs, 1)).start()

    @classmethod
    def single_shot_ms(cls, wait_time_ms: Union[float, int], function: Callable, args: tuple = (),
                       kwargs: Optional[dict] = None):
        if kwargs is None:
            kwargs = {}
        threading.Thread(target=cls._trigger_ms, args=(wait_time_ms, function, args, kwargs, 1)).start()

    @classmethod
    def shoot(cls, interval: Union[float, int], function: Callable, args: tuple = (), kwargs: Optional[dict] = None,
              iterations: int = 1):
        if kwargs is None:
            kwargs = {}
        threading.Thread(target=cls._trigger, args=(interval, function, args, kwargs, iterations)).start()

    @classmethod
    def shoot_ms(cls, interval_ms: Union[float, int], function: Callable, args: tuple = (),
                 kwargs: Optional[dict] = None, iterations: int = 1):
        if kwargs is None:
            kwargs = {}
        threading.Thread(target=cls._trigger_ms, args=(interval_ms, function, args, kwargs, iterations)).start()

    def fire(self, interval: Union[float, int], function: Callable, args: tuple = (), kwargs: Optional[dict] = None,
             index: int = None):
        if kwargs is None:
            kwargs = {}
        if index is None:
            index = len(self._fires)
        while len(self._fires) < index:
            self._fires.append((None, None))

        event = threading.Event()
        thread = threading.Thread(target=self._trigger, args=(interval, function, args, kwargs, -1, event))

        if index < len(self._fires) and self._fires[index] == (None, None):
            self._fires[index] = (thread, event)
        else:
            self._fires.insert(index, (thread, event))
        thread.start()

    def fire_ms(self, interval_ms: Union[float, int], function: Callable, args: tuple = (),
                kwargs: Optional[dict] = None, index: int = None):
        if kwargs is None:
            kwargs = {}
        if index is None:
            index = len(self._fires)
        while len(self._fires) < index:
            self._fires.append((None, None))

        event = threading.Event()
        thread = threading.Thread(target=self._trigger_ms, args=(interval_ms, function, args, kwargs, -1, event))

        if index < len(self._fires) and self._fires[index] == (None, None):
            self._fires[index] = (thread, event)
        else:
            self._fires.insert(index, (thread, event))
        thread.start()

    def stop_fire(self, index: Optional[int] = None, amount: Optional[int] = None):
        if amount is None:
            amount = 1
        for _ in range(amount):
            thread, event = self._fires.pop(index or 0)
            event.set()
            thread.join()

    def warmup_fire(self, rounds: int = 300):
        for _ in range(rounds):
            self.wait_ms(1)

    @classmethod
    def test_delay(cls, amount: Union[float, int] = 0) -> timedelta:
        """Tests a ... second delay.
        Keep in mind that any amount that isn't 0 is subject to around a 2 ns extra delay."""
        timer = cls()
        if amount:
            cls.wait(amount)
        return timer.end()

    @classmethod
    def test_delay_ms(cls, amount_ms: Union[float, int] = 0) -> timedelta:
        """Tests a ... second delay.
        Keep in mind that any amount that isn't 0 is subject to around a 2 ns extra delay."""
        timer = cls()
        if amount_ms:
            cls.wait_ms(amount_ms)
        return timer.end()

    @classmethod
    def wait(cls, seconds: int = 0):
        time.sleep(seconds)

    @classmethod
    def wait_ms(cls, milliseconds: int = 0):
        wanted_time = cls._time() + (milliseconds * 1e+6)
        while cls._time() < wanted_time:
            if wanted_time - cls._time() > 1_000_000:  # 3_000_000
                time.sleep(0.001)
            else:
                continue

    @staticmethod
    def get_readable(td: timedelta, format_to: int = TimeFormat.SECONDS) -> str:
        total_seconds = int(td.total_seconds())
        micros = td.microseconds

        # Select the correct level of detail based on the format
        if format_to == TimeFormat.WEEKS:
            weeks = total_seconds // 604800
            days = (total_seconds % 604800) / 86400
            return f"{weeks} weeks, {days} days"

        elif format_to == TimeFormat.DAYS:
            days = total_seconds // 86400
            hours = (total_seconds % 86400) / 3600
            return f"{days} days, {hours} hours"

        elif format_to == TimeFormat.HOURS:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) / 60
            return f"{hours} hours, {minutes} minutes"

        elif format_to == TimeFormat.MINUTES:
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes} minutes, {seconds} seconds"

        elif format_to == TimeFormat.SECONDS:
            return f"{total_seconds} seconds, {micros / 1000} milliseconds"

        elif format_to == TimeFormat.MILISEC:
            millisecs = (total_seconds * 1000) + (micros // 1000)
            return f"{millisecs} milliseconds, {micros % 1000} microseconds"

        elif format_to == TimeFormat.MICROSEC:
            microsecs = (total_seconds * 1000000) + micros
            return f"{microsecs} microseconds"

        return "Invalid format specified"

    @classmethod
    def time(cls, func):
        def wrapper(*args, **kwargs):
            timer = cls()
            result = func(*args, **kwargs)
            elapsed = timer.end()
            print(f"Function {func.__name__} took {timer.get_readable(elapsed)} to complete.")
            return result
        return wrapper

    def enter(self, index: Optional[int] = None):
        self.start(index)
        self._exit_index = index
        return self

    def __enter__(self):
        if self._exit_index > len(self._times):
            self.start(self._exit_index)

    def __exit__(self, exc_type, exc_val, exc_tb):
        td = self.end(self._exit_index)
        print(f"Codeblock {self._exit_index} took {td} to execute.")


Timer = TimidTimer.setup_timer_func(time.time, 1e9)
TimerNS = TimidTimer.setup_timer_func(time.time_ns, 1)
PerfTimer = TimidTimer.setup_timer_func(time.perf_counter, 1e9)
PerfTimerNS = TimidTimer.setup_timer_func(time.perf_counter_ns, 1)
CPUTimer = TimidTimer.setup_timer_func(time.process_time, 1e9)
CPUTimerNS = TimidTimer.setup_timer_func(time.process_time_ns, 1)
MonotonicTimer = TimidTimer.setup_timer_func(time.monotonic, 1e9)
MonotonicTimerNS = TimidTimer.setup_timer_func(time.monotonic_ns, 1)
ThreadTimer = TimidTimer.setup_timer_func(time.thread_time, 1e9)
ThreadTimerNS = TimidTimer.setup_timer_func(time.thread_time_ns, 1)


class DateTimeTimer(TimidTimer):
    """This is obviously a joke and should not be taken seriously as it isn't performant."""
    def _time(self) -> float:
        return datetime.now().timestamp() * 1e9


def local_test():
    try:
        def test_timer(timer_class, description):
            timer = timer_class()
            timer.start()
            for _ in range(1000000):
                pass  # A simple loop to simulate computation
            elapsed = timer.end()
            print(f"{description} elapsed time: {timer.get_readable(elapsed)}")

        def sleep_and_measure(timer_class, description, sleep_time_ms=1000):
            """Measures how long the system sleeps using the given timer."""
            timer = timer_class()
            timer.start()
            TimidTimer.wait_ms(sleep_time_ms)  # Sleep for a specified time
            elapsed = timer.end()
            print(f"{description}, expected sleep: {sleep_time_ms / 1000}s, measured time: {timer.get_readable(elapsed)}")

        timer1 = TimidTimer()
        timer1.shoot(1, lambda: print(timer1.tock(return_datetime=True)), iterations=3)

        timer = TimidTimer()
        for _ in range(10):
            timer.wait_ms(1000)
            timer.tock()
        print("Average 1 second sleep extra delay: ", timer.average() - timedelta(seconds=1))
        print("TTD", TimidTimer.test_delay_ms(1000) - timedelta(seconds=1))

        with TimidTimer().enter(index=1):
            timer.wait_ms(1)

        print("Starting timer tests...")
        test_timer(TimidTimer, "Timid Timer")
        test_timer(Timer, "Normal Timer")
        test_timer(PerfTimer, "Performance Timer")
        test_timer(PerfTimerNS, "Performance Timer Nanosecond")
        test_timer(CPUTimer, "CPU Timer")
        test_timer(CPUTimerNS, "CPU Timer Nanosecond")
        test_timer(MonotonicTimer, "Monotonic Timer")
        test_timer(MonotonicTimerNS, "Monotonic Timer Nanosecond")

        print("\nTesting sleep accuracy...")
        sleep_and_measure(TimidTimer, "Timid Timer")
        sleep_and_measure(Timer, "Normal Timer")
        sleep_and_measure(PerfTimer, "Performance Timer")
        sleep_and_measure(PerfTimerNS, "Performance Timer Nanosecond")
        sleep_and_measure(CPUTimer, "CPU Timer")
        sleep_and_measure(CPUTimerNS, "CPU Timer Nanosecond")
        sleep_and_measure(MonotonicTimer, "Monotonic Timer")
        sleep_and_measure(MonotonicTimerNS, "Monotonic Timer Nanosecond")
    except Exception as e:
        print(f"Exception occurred {e}.")
        return False
    print("Test completed successfully.")
    return True


if __name__ == "__main__":
    local_test()
