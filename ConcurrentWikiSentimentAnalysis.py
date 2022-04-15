import csv
from abc import ABC, abstractmethod
from multiprocessing import Process, RawArray
from threading import Thread
from typing import Union

from bs4 import BeautifulSoup
from psutil import cpu_count
from requests import Response, get

from MetricsMonitor import MetricsMonitor


class ConcurrentWikiSentimentAnalysis(ABC):
    __MIN_LOAD_PER_WORKER: int = 4
    __POSITIVE_WORDS: set[str] = {}
    __NEGATIVE_WORDS: set[str] = {}

    def __init__(self, urls: list[str], workers: int = cpu_count()):
        self.__POSITIVE_WORDS = set(self.__load_file_to_list('positive_words.txt'))
        self.__NEGATIVE_WORDS = set(self.__load_file_to_list('negative_words.txt'))
        self.__urls: list[str] = urls
        self.__load: int = len(self.__urls)
        self.__workers_count: int = workers
        self.__load_per_worker: int = int(self.__load / self.__workers_count)
        self.__load_per_worker_remainder: int = self.__load % self.__workers_count
        self.__sentiments: RawArray = RawArray('i', self.__load)

    @MetricsMonitor(name='concurrent-sentiment-analysis', runs=5, intervals=[1.0, 1.0, 1.0, 1.0, 1.0])
    def start(self) -> None:

        if self.__load_per_worker < self.__MIN_LOAD_PER_WORKER:
            self.worker_func(0, self.__load - 1)
            return

        start: int = 0
        worker_i: int = 0
        workers: list[Union[Thread, Process]] = []

        while worker_i < self.__load_per_worker_remainder:
            end = start + self.__load_per_worker
            workers.append(self.spawn_worker(start, end))
            start = end + 1
            worker_i = worker_i + 1

        while worker_i < self.__workers_count:
            end = start + self.__load_per_worker - 1
            workers.append(self.spawn_worker(start, end))
            start = end + 1
            worker_i = worker_i + 1

        for worker in workers:
            worker.join()

    def export_to_csv(self):
        with open('sentiment_analysis.csv', 'w+') as f:
            w = csv.writer(f)
            w.writerow(['url', 'sentiment'])
            w.writerows(self.__construct_sentiments())

    def __construct_sentiments(self) -> (str, str):
        r: list[(str, str)] = []
        for u, s in zip(self.__urls, self.__sentiments):
            if s > 0:
                r.append((u, 'Positive'))
            elif s < 0:
                r.append((u, 'Negative'))
            else:
                r.append((u, 'Neutral'))
        return r

    @abstractmethod
    def spawn_worker(self, start: int, end: int) -> Union[Thread, Process]:
        pass

    def worker_func(self, start: int, end: int) -> None:
        while start <= end:
            content: str = self.__scrape(start)
            self.__sentiments[start] = self.__analyze(content)
            start = start + 1

    def __scrape(self, url_i: int) -> str:
        r: Response = get(self.__urls[url_i])
        if r.status_code != 200:
            raise Exception('Cannot make request 👀 (got url: %s)' % self.__urls[url_i])
        html: BeautifulSoup = BeautifulSoup(r.text, 'html.parser')
        content: str = " ".join([paragraph.text for paragraph in html.select('p')])
        return content

    def __analyze(self, text: str) -> int:
        tokenized_text: set[str] = set(text.split())
        positive_words_count: int = len(tokenized_text.intersection(self.__POSITIVE_WORDS))
        negative_words_count: int = len(tokenized_text.intersection(self.__NEGATIVE_WORDS))
        return positive_words_count - negative_words_count

    @staticmethod
    def __load_file_to_list(file: str) -> list[str]:
        with open(file, 'r') as f:
            return [line.strip() for line in f.readlines()]


class MultithreadWikiSentimentAnalysis(ConcurrentWikiSentimentAnalysis):

    def __init__(self, urls: list[str], workers: int = cpu_count()):
        super().__init__(urls, workers)

    def spawn_worker(self, start: int, end: int) -> Thread:
        t: Thread = Thread(target=self.worker_func, args=(start, end,))
        t.start()
        return t


class MultiProcessWikiSentimentAnalysis(ConcurrentWikiSentimentAnalysis):

    def __init__(self, urls: list[str], workers: int = cpu_count()):
        super().__init__(urls, workers)

    def spawn_worker(self, start: int, end: int) -> Process:
        p: Process = Process(target=self.worker_func, args=(start, end,))
        p.start()
        return p
