
# Concurrent Wiki Sentiment Analysis

Dead simple sentiment analysis on WIkipedia articles, done concurrently (and in parallel) using Python.


## Run Locally

Clone the project

```bash
  git clone https://github.com/kaparounakis/concurrent-wiki-sentiment-analysis
```

Go to the project directory

```bash
  cd concurrent-wiki-sentiment-analysis
```

Install dependencies

```bash
  pip install -r requirements.txt
```

Run main.py

```bash
  python3.10 main.py
```

and check for the produced .csv files
## Choose between Multithread and Multiprocess

Change main.py accordingly

```python
# Choose 'mt' for a Multithread Approach | Choose 'mp' for a Multiprocess Approach
if __name__ == '__main__':
    main(mode='mt')
```
