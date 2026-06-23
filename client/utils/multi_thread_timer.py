import logging
import threading
import time


class MultiThreadTimer:
    """Periodic timer that runs callbacks without creating unbounded threads."""

    def __init__(self, interval, callback, *args, **kwargs):
        """Initialize the timer.

        Args:
            interval (float): Time interval between calls (milliseconds)
            callback (callable): Callback function
            *args: Positional arguments for the callback function
            **kwargs: Keyword arguments for the callback function
        """
        self._interval = interval / 1000 # convert milliseconds to seconds
        self.callback = callback
        self.args = args
        self.kwargs = kwargs
        self._stop_event = threading.Event()
        self._thread = None
        self._lock = threading.Lock()
        self._logger = logging.getLogger(__name__)

    def _run(self):
        # interval_s = max(0.001, self.interval / 1000.0)
        while not self._stop_event.is_set():
            # print(f"Debug: interval_s: {self._interval}")
            start_time = time.perf_counter()
            try:
                self.callback(*self.args, **self.kwargs)
            except Exception:
                self._logger.exception("MultiThreadTimer callback failed")

            elapsed = time.perf_counter() - start_time
            wait_s = max(0.0, self._interval - elapsed)
            if self._stop_event.wait(wait_s):
                break

    def start(self):
        """Start the timer if it is not already running."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def is_alive(self):
        return self._thread is not None and self._thread.is_alive()

    def join(self, timeout=None):
        """Wait for the timer thread to complete."""
        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=timeout)

    def stop(self, timeout=None):
        """Stop the timer and wait for completion."""
        self._stop_event.set()
        self.join(timeout=timeout)
    
    def set_interval(self, interval):
        """Set the timer interval."""
        self._interval = interval / 1000 # convert milliseconds to seconds


# Example function
def my_task():
    """Example task function for demonstration."""
    print(f"[{time.time()}] Task executing...")


if __name__ == "__main__":
    timer = MultiThreadTimer(1, my_task)
    timer.start()
    timer.join()
    print("Timer stopped")
