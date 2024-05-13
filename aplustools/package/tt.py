from timeit import default_timer
from datetime import timedelta
from typing import List, Optional, Union


class TimidTimer:
    """Enhanced timer with split, multiple recording and statistical capabilities."""
    def __init__(self, start_now: bool = True):
        self.start_times: List[float] = []
        self.end_times: List[float] = []
        self.splits: List[timedelta] = []
        self.is_running: bool = False
        if start_now:
            self.start()

    def start(self):
        """Start or resume the timer."""
        if not self.is_running:
            self.start_times.append(default_timer())
            self.is_running = True

    def end(self):
        """Stop the timer and record the end time."""
        if self.is_running:
            end_time = default_timer()
            self.end_times.append(end_time)
            self.is_running = False

    def split(self):
        """Record a split time."""
        if self.is_running:
            current_time = default_timer()
            if self.splits:
                last_split = self.splits[-1].total_seconds() + self.start_times[-1]
            else:
                last_split = self.start_times[-1]
            self.splits.append(timedelta(seconds=current_time - last_split))

    def tally(self) -> timedelta:
        """Return the total time recorded across all sessions."""
        total_time = sum((end - start for start, end in zip(self.start_times, self.end_times)), 0.0)
        return timedelta(seconds=total_time)

    def average(self) -> timedelta:
        """Calculate the average time across all recorded sessions."""
        total_time = self.tally().total_seconds()
        if self.end_times:
            return timedelta(seconds=total_time / len(self.end_times))
        return timedelta(seconds=0)

    def get_readable(self, td: timedelta) -> str:
        """Return a human-readable string of the given timedelta."""
        seconds = int(td.total_seconds())
        days, seconds = divmod(seconds, 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        return f"{days}d:{hours}h:{minutes}m:{seconds}s"


timer = TimidTimer(start_now=False)

timer.start()
# Simulate some work
timer.split()  # Record a split time
timer.split()  # Record another split time
timer.end()    # End the first session

timer.start()  # Start a new session
timer.end()    # End the second session

print("Total time:", timer.get_readable(timer.tally()))
print("Average time:", timer.get_readable(timer.average()))

# Print all splits
for i, split in enumerate(timer.splits, start=1):
    print(f"Split {i}: {timer.get_readable(split)}")

