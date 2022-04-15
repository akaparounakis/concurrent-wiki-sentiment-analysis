import csv
import functools
import signal
import time
from multiprocessing import Process

from psutil import cpu_percent, virtual_memory


class _Metrics:
    __real_time: list[float] = []
    __relative_time: list[float] = []
    __cpu_util: list[float] = []
    __ram_util: list[float] = []
    __running: bool = True

    def __init__(self, name: str, run: int, interval: float):
        self.__name = name
        self.__run = run
        self.__interval: float = interval
        signal.signal(signal.SIGTERM, self.__signal_handler)
        signal.signal(signal.SIGINT, self.__signal_handler)

    def get_execution_time(self) -> float:
        return self.__relative_time[-1]

    def get_relative_time(self) -> list[float]:
        return self.__relative_time

    def get_cpu_util(self) -> list[float]:
        return self.__cpu_util

    def get_avg_cpu_util(self) -> float:
        length: int = len(self.__cpu_util)
        if length != 0:
            return sum(self.__cpu_util) / len(self.__cpu_util)

    def get_ram_util(self) -> list[float]:
        return self.__ram_util

    def get_avg_ram_util(self) -> float:
        length: int = len(self.__ram_util)
        if length != 0:
            return sum(self.__ram_util) / len(self.__ram_util)

    def __export_to_csv(self):
        with open(file='metrics_monitor_%s_%d.csv' % (self.__name, self.__run), mode='w+') as f:
            w = csv.writer(f)
            w.writerow(['time', 'cpu_util', 'ram_util', 'execution_time', 'avg_cpu_util', 'avg_ram_util'])
            w.writerow([self.__relative_time[0], self.__cpu_util[0], self.__ram_util[0],
                        self.get_execution_time(), self.get_avg_cpu_util(), self.get_avg_ram_util()])
            for t, c, r in zip(self.__relative_time[1:], self.__cpu_util[1:], self.__ram_util[1:]):
                w.writerow([t, c, r, '', '', ''])

    def __signal_handler(self, sig, frame) -> None:
        self.__stop()

    @staticmethod
    def initiate(name: str, run: int, interval: float) -> None:
        m: _Metrics = _Metrics(name, run, interval)
        m.__start()

    def __start(self) -> None:
        while self.__running:
            self.__capture_time()
            self.__capture_metrics()
            time.sleep(self.__interval)

    def __stop(self) -> None:
        self.__running = False
        self.__export_to_csv()

    def __capture_time(self) -> None:
        moment: float = time.time()
        self.__real_time.append(moment)
        self.__relative_time.append(moment - self.__real_time[0])

    def __capture_metrics(self) -> None:
        self.__cpu_util.append(cpu_percent())
        self.__ram_util.append(virtual_memory().percent)


class MetricsMonitor:

    def __init__(self, runs: int, intervals: list[float], name: str = ''):
        self.__validate_args(runs, intervals)
        self.name: str = name
        self.__runs: int = runs
        self.__intervals: list[float] = intervals

    def __call__(self, func):
        functools.wraps(func)

        def wrapper(*args, **kwargs):
            for run in range(1, self.__runs + 1):
                p: Process = Process(target=_Metrics.initiate, args=(self.name, run, self.__intervals[run - 1],))
                p.start()
                func(*args, **kwargs)
                p.terminate()
                p.join()

        return wrapper

    @staticmethod
    def __validate_args(runs: int, intervals: list[float]):
        if runs < 0:
            raise Exception('Runs cannot be less that 1 🤖 Got (runs: %d)' % runs)
        if runs != len(intervals):
            raise Exception('Intervals cannot be fewer than Runs 🤖 Got (intervals: %s)' % str(intervals))
        for interval in intervals:
            if interval < 0.5:
                raise Exception('Interval cannot be less than 0.5 🤖 Got (intervals: %s)' % str(intervals))
