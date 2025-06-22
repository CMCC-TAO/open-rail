import threading
import time

class MultiThreadTimer:
    def __init__(self, interval, callback, *args, **kwargs):
        """
        :param interval: 每次调用的时间间隔（毫秒）
        :param callback: 回调函数，将在新线程中运行
        :param args: 回调函数的位置参数
        :param kwargs: 回调函数的关键字参数
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
            # 在一个新线程中启动回调函数
            t = threading.Thread(target=self.callback, args=self.args, kwargs=self.kwargs)
            t.start()
            end_time = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
            elapsed_time = end_time - start_time
            time.sleep(max(0.0, self.interval/1000.0 - elapsed_time/1e9))

    def start(self):
        self._thread.start()
    
    def join(self, timeout=None):
        self._thread.join(timeout=timeout)

    def stop(self):
        self._stop_event.set()
        self._thread.join()

# 示例函数
def my_task():
    # print(f"[{time.strftime('%X')}] 任务执行中...")
    print(f"[{time.time()}] 任务执行中...")

if __name__ == "__main__":
    # 使用多线程定时器
    timer = MultiThreadTimer(1, my_task)
    timer.start()

    # 运行 10 秒后停止
    # time.sleep(10)
    # timer.stop()
    timer.join()
    print("定时器已停止")