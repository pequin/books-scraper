"""Walk categories and their pages."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Iterator

from .fetch import Fetcher, FetchError
from .parse import Book, parse_categories, parse_list

log = logging.getLogger(__name__)

START_URL = "https://books.toscrape.com/index.html"


def crawl(
    fetcher: Fetcher,
    start_url: str = START_URL,
    only: Iterable[str] = (),
    max_pages: int | None = None,
) -> Iterator[Book]:
    """Yield every book, category by category.

    ``only`` limits the run to categories with these names (case-insensitive).
    ``max_pages`` stops after that many list pages in total. A page that fails
    after all retries is logged and skipped, so one bad page does not lose the
    rest of the run.
    """
    wanted = {name.lower() for name in only}
    categories = parse_categories(fetcher.get(start_url), start_url)
    if wanted:
        categories = [(n, u) for n, u in categories if n.lower() in wanted]
        missing = wanted - {n.lower() for n, _ in categories}
        if missing:
            msg = f"unknown categories: {', '.join(sorted(missing))}"
            raise ValueError(msg)
    pages = 0
    for name, url in categories:
        next_url: str | None = url
        page_in_category = 0
        while next_url:
            if max_pages is not None and pages >= max_pages:
                return
            pages += 1
            try:
                html = fetcher.get(next_url)
            except FetchError as exc:
                log.error("skipped page: %s", exc)
                break
            page_in_category += 1
            books, next_url = parse_list(html, next_url, name)
            log.info("%s, page %d: %d books", name, page_in_category, len(books))
            yield from books
