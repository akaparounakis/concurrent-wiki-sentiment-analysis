from ConcurrentWikiSentimentAnalysis import MultiProcessWikiSentimentAnalysis, MultithreadWikiSentimentAnalysis


def main(mode: str) -> None:
    with open('wikipedia_urls.txt', 'r') as f:
        urls: list[str] = [line.strip() for line in f.readlines()]

        if mode == 'mt':
            mtcwsa: MultithreadWikiSentimentAnalysis = MultithreadWikiSentimentAnalysis(urls, 2)
            mtcwsa.start()
            mtcwsa.export_to_csv()

        if mode == 'mp':
            mpcwsa: MultiProcessWikiSentimentAnalysis = MultiProcessWikiSentimentAnalysis(urls, 2)
            mpcwsa.start()
            mpcwsa.export_to_csv()


# Choose 'mt' for a Multithread Approach | Choose 'mp' for a Multiprocess Approach
if __name__ == '__main__':
    main(mode='mt')
