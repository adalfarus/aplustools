import time
import threading
from datetime import datetime


class Timer:
    def __init__(self):
        self._countdown_time = 0
        self._stopwatch_running = False
        self._stopwatch_start_time = None
        self._stopwatch_elapsed_time = 0
        self._stopwatch_laps = []
        self._paused = False
        self._current_timer_thread = None

    def start_countdown(self, seconds):
        self._countdown_time = seconds
        self._paused = False
        if self._current_timer_thread:
            self._current_timer_thread.join()
        self._current_timer_thread = threading.Thread(target=self._countdown)
        self._current_timer_thread.start()

    def _countdown(self):
        while self._countdown_time > 0 and not self._paused:
            print(f"Countdown Timer: {self._countdown_time} seconds remaining")
            time.sleep(1)
            self._countdown_time -= 1
        if self._countdown_time == 0:
            print("Countdown Timer: Time's up!")

    def start_stopwatch(self):
        self._stopwatch_running = True
        self._paused = False
        self._stopwatch_start_time = time.time()
        self._stopwatch_elapsed_time = 0
        self._stopwatch_laps = []
        if self._current_timer_thread:
            self._current_timer_thread.join()
        self._current_timer_thread = threading.Thread(target=self._stopwatch)
        self._current_timer_thread.start()

    def _stopwatch(self):
        while self._stopwatch_running and not self._paused:
            elapsed = time.time() - self._stopwatch_start_time + self._stopwatch_elapsed_time
            print(f"Stopwatch: {elapsed:.2f} seconds elapsed")
            time.sleep(1)

    def stop_stopwatch(self):
        if self._stopwatch_running:
            self._stopwatch_elapsed_time += time.time() - self._stopwatch_start_time
            self._stopwatch_running = False
            print(f"Stopwatch stopped at {self._stopwatch_elapsed_time:.2f} seconds")

    def lap_stopwatch(self):
        if self._stopwatch_running:
            lap_time = time.time() - self._stopwatch_start_time + self._stopwatch_elapsed_time
            self._stopwatch_laps.append(lap_time)
            print(f"Lap recorded at {lap_time:.2f} seconds")

    def pause(self):
        self._paused = True
        if self._stopwatch_running:
            self._stopwatch_elapsed_time += time.time() - self._stopwatch_start_time
        print("Timer paused")

    def resume(self):
        self._paused = False
        if self._countdown_time > 0:
            self._current_timer_thread = threading.Thread(target=self._countdown)
            self._current_timer_thread.start()
        elif self._stopwatch_running:
            self._stopwatch_start_time = time.time()
            self._current_timer_thread = threading.Thread(target=self._stopwatch)
            self._current_timer_thread.start()
        print("Timer resumed")

    def display_current_time(self):
        current_time = datetime.now().strftime("%H:%M:%S")
        print(f"Current Time: {current_time}")

    def show_laps(self):
        print("Lap times:")
        for i, lap in enumerate(self._stopwatch_laps, start=1):
            print(f"Lap {i}: {lap:.2f} seconds")


# Example usage
timer = Timer()

# Starting a countdown timer for 10 seconds
timer.start_countdown(10)

# Wait for a while to let the countdown run
time.sleep(5)

# Pause the countdown timer
timer.pause()

# Display the current system time
timer.display_current_time()

# Resume the countdown timer
timer.resume()

# Starting a stopwatch
time.sleep(3)
timer.start_stopwatch()

# Wait for a while and record a lap time
time.sleep(3)
timer.lap_stopwatch()

# Wait for a while and then stop the stopwatch
time.sleep(3)
timer.stop_stopwatch()

# Show lap times
timer.show_laps()

# Display the current system time
timer.display_current_time()
