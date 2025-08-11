import threading
import time

class MultiThreadTimer:
    """Multi-threaded timer that executes callbacks at specified intervals.
    
    This timer runs callbacks in separate threads to avoid blocking the main timer loop.
    """
    
    def __init__(self, interval, callback, *args, **kwargs):
        """Initialize the multi-thread timer.
        
        Args:
            interval (float): Time interval between calls (milliseconds)
            callback (callable): Callback function to run in new thread
            *args: Positional arguments for the callback function
            **kwargs: Keyword arguments for the callback function
        """
        self.interval = interval
        self.callback = callback
        self.args = args
        self.kwargs = kwargs
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run)
        self._thread.daemon = True

    def _run(self):
        while not self._stop_event.is_set():
            start_time = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
            # Start callback function in a new thread
            t = threading.Thread(target=self.callback, args=self.args, kwargs=self.kwargs)
            t.start()
            end_time = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
            elapsed_time = end_time - start_time
            time.sleep(max(0.0, self.interval/1000.0 - elapsed_time/1e9))

    def start(self):
        """Start the timer."""
        self._thread.start()
    
    def join(self, timeout=None):
        """Wait for the timer thread to complete.
        
        Args:
            timeout (float, optional): Maximum time to wait in seconds
        """
        self._thread.join(timeout=timeout)

    def stop(self):
        """Stop the timer and wait for completion."""
        self._stop_event.set()
        self._thread.join()

# Example function
def my_task():
    """Example task function for demonstration."""
    print(f"[{time.time()}] Task executing...")

if __name__ == "__main__":
    # Use multi-thread timer
    timer = MultiThreadTimer(1, my_task)
    timer.start()

    # Stop after running for 10 seconds
    # time.sleep(10)
    # timer.stop()
    timer.join()
    print("Timer stopped")