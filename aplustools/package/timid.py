from timeit import default_timer as timer
from datetime import timedelta
from typing import Optional


class TimidTimerOut:
    WEEKS = 0
    DAYS = 1
    HOURS = 2
    MINUTES = 3
    SECONDS = 4
    MILISEC = 5
    MICROSEC = 6


class TimidTimer:
    def __init__(self, output_target: Optional[TimidTimerOut] = TimidTimerOut.SECONDS,
                 start_now: Optional[bool] = True):
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
        self.start_t = timer()
        return self.start_t

    def end(self, return_end_time: Optional[bool] = False) -> timedelta | float:
        self.stop_t = timer()
        self.t_d = timedelta(seconds=self.stop_t-self.start_t)

        if not return_end_time:
            return self.t_d
        else:
            return self.stop_t
