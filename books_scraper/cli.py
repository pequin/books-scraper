"""Command line entry point: ``python -m books_scraper``."""

from __future__ import annotations

import argparse
import logging
import sys
import time
from collections import Counter
from pathlib import Path

from .crawl import START_URL, crawl
from .export import FORMATS, save
from .fetch import Fetcher, FetchError


def _formats(value: str) -> list[str]:
    items = [v.strip().lower() for v in value.split(",") if v.strip()]
    bad = [v for v in items if v not in FORMATS]
    if bad:
        msg = f"unknown format(s): {', '.join(bad)}; choose from {', '.join(FORMATS)}"
        raise argparse.ArgumentTypeError(msg)
    return items


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="books_scraper",
        description="Collect every book from books.toscrape.com, a practice site for scraping.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output/books"),
        help="output path without extension (default: output/books)",
    )
    parser.add_argument(
        "-f",
        "--formats",
        type=_formats,
        default=["csv", "xlsx"],
        help="comma separated: csv, json, xlsx (default: csv,xlsx)",
    )
    parser.add_argument(
        "-c", "--category", action="append", default=[], help="only this category; repeat for more"
    )
    parser.add_argument("--max-pages", type=int, help="stop after this many list pages")
    parser.add_argument(
        "--delay", type=float, default=1.0, help="seconds between requests (default: 1)"
    )
    parser.add_argument("--start-url", default=START_URL, help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None, fetcher: Fetcher | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    fetcher = fetcher or Fetcher(delay=args.delay)
    started = time.monotonic()
    books = []
    code = 0
    try:
        for book in crawl(fetcher, args.start_url, args.category, args.max_pages):
            books.append(book)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except FetchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        code = 1
    except KeyboardInterrupt:
        print("interrupted, saving what was collected", file=sys.stderr)
        code = 130
    finally:
        fetcher.close()

    elapsed = time.monotonic() - started
    stats = fetcher.stats
    print(f"{len(books)} books, {stats.requests} requests, {stats.retries} retries, {elapsed:.0f}s")
    if books:
        categories = Counter(b.category for b in books)
        print(f"{len(categories)} categories, {sum(b.in_stock for b in books)} in stock")
        for path in save(books, args.output, args.formats):
            print(f"saved {path}")
    return code
