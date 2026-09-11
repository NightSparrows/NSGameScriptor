
import threading
import time


class CancelledException(Exception):
    """Raised by CancellationToken.sleep()/checkPoint() once cancel() has
    been requested. Left uncaught, it unwinds cleanly out of whatever
    battle/task loop is currently blocked - every loop in the battle code
    already sleeps at least once per iteration, so replacing time.sleep()
    with CancellationToken.sleep() makes the whole call stack interruptible
    without turning any of it into real coroutines."""


class CancellationToken:
    """Cooperative cancellation flag, thread-safe: cancel() is meant to be
    called from the GUI thread while sleep()/checkPoint() are polled from
    the background automation thread."""

    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    def reset(self) -> None:
        self._event.clear()

    def isCancelled(self) -> bool:
        return self._event.is_set()

    def checkPoint(self) -> None:
        if self._event.is_set():
            raise CancelledException()

    # drop-in replacement for time.sleep(seconds): sleeps in short chunks,
    # checking the flag between each one, so a cancel() lands within
    # `interval` seconds instead of only after the full sleep completes.
    def sleep(self, seconds: float, interval: float = 0.05) -> None:
        self.checkPoint()
        remaining = seconds
        while remaining > 0:
            step = min(interval, remaining)
            time.sleep(step)
            remaining -= step
            self.checkPoint()
