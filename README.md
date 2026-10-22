# books-scraper

Collects every book from [books.toscrape.com](https://books.toscrape.com/), a site built for
scraping practice, and saves title, price, rating, stock, category, and link to CSV, Excel, or
JSON. A full run takes about a minute and a half. It waits between requests, retries when the
site has a hiccup, and keeps going if one page fails.

> This is a demo/portfolio project, not client work. It only talks to books.toscrape.com,
> which exists for people to practice on.

Python 3.11+, [httpx](https://www.python-httpx.org/), Beautiful Soup, openpyxl.

## Features

- Walks all 50 categories and follows "next" links through every page
- Fixed delay between requests (1 second by default) and a clear User-Agent
- Retries with backoff (2, 4, 8 seconds) on network errors, HTTP 429, and 5xx;
  other 4xx errors fail at once instead of hammering the site
- A page that still fails is logged and skipped; Ctrl+C saves what was already collected
- Prices kept as exact decimals with the currency in its own column
- Output to CSV (UTF-8 with BOM, opens cleanly in Excel), XLSX with a bold frozen header, or JSON
- Filter by category, limit the number of pages
- Tests run offline against saved HTML pages and a mock transport, so they never hit the site

## Run it

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m books_scraper                          # all books -> output/books.csv + .xlsx
python -m books_scraper -c Poetry -c Travel -f csv,json,xlsx -o output/sample
python -m books_scraper --max-pages 3 --delay 2  # quick and gentle
```

Options:

| Option | Meaning |
| --- | --- |
| `-o`, `--output` | Output path without extension (default `output/books`) |
| `-f`, `--formats` | Any of `csv`, `json`, `xlsx`, comma separated (default `csv,xlsx`) |
| `-c`, `--category` | Only this category; repeat for more |
| `--max-pages` | Stop after this many list pages |
| `--delay` | Seconds between requests (default 1) |

## Example output

Real runs from October 22, 2026. Two categories:

```text
$ python -m books_scraper -c Poetry -c Travel -f csv,json,xlsx -o output/sample
INFO Travel, page 1: 11 books
INFO Poetry, page 1: 19 books
30 books, 3 requests, 0 retries, 2s
2 categories, 30 in stock
saved output/sample.csv
saved output/sample.json
saved output/sample.xlsx
```

The whole site (end of the log):

```text
$ python -m books_scraper
...
INFO Politics, page 1: 3 books
INFO Cultural, page 1: 1 books
INFO Erotica, page 1: 1 books
INFO Crime, page 1: 1 books
1000 books, 81 requests, 0 retries, 80s
50 categories, 1000 in stock
saved output/books.csv
saved output/books.xlsx
```

First rows of `output/books.csv`:

```text
title,price,currency,rating,in_stock,category,url
It's Only the Himalayas,45.17,GBP,2,True,Travel,https://books.toscrape.com/catalogue/its-only-the-himalayas_981/index.html
Full Moon over Noah’s Ark: An Odyssey to Mount Ararat and Beyond,49.43,GBP,4,True,Travel,https://books.toscrape.com/catalogue/full-moon-over-noahs-ark-an-odyssey-to-mount-ararat-and-beyond_811/index.html
```

One record from `output/sample.json`:

```json
{
  "title": "It's Only the Himalayas",
  "price": "45.17",
  "currency": "GBP",
  "rating": 2,
  "in_stock": true,
  "category": "Travel",
  "url": "https://books.toscrape.com/catalogue/its-only-the-himalayas_981/index.html"
}
```

## Tests and lint

```bash
pip install -r requirements-dev.txt
pytest
ruff check .
```

## Project layout

```text
books_scraper/
  fetch.py    HTTP client with delay, retries, and request stats
  parse.py    HTML -> Book records
  crawl.py    categories and pagination
  export.py   CSV, JSON, XLSX
  cli.py      command line options and summary
tests/        parser, retry, crawl, and CLI tests with saved HTML fixtures
```

## Reuse

Adapting this to another site mostly means rewriting `parse.py`. Before scraping a real site,
check its terms and robots.txt, and keep the delay polite.

## License

MIT, see [LICENSE](LICENSE).
