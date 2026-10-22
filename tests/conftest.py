from pathlib import Path

import httpx
import pytest

from books_scraper.fetch import Fetcher

FIXTURES = Path(__file__).parent / "fixtures"
BASE = "https://books.toscrape.com/"
MYSTERY = BASE + "catalogue/category/books/mystery_3/"

PAGES = {
    BASE + "index.html": "index.html",
    MYSTERY + "index.html": "category_mystery_page1.html",
    MYSTERY + "page-2.html": "category_mystery_page2.html",
}


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class FakeSleep:
    """Record waits instead of sleeping, so tests run instantly."""

    def __init__(self) -> None:
        self.calls: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.calls.append(seconds)


def site_handler(request: httpx.Request) -> httpx.Response:
    name = PAGES.get(str(request.url))
    if name is None:
        return httpx.Response(404, text="not found")
    return httpx.Response(200, text=fixture(name))


@pytest.fixture
def fake_sleep() -> FakeSleep:
    return FakeSleep()


@pytest.fixture
def site_fetcher(fake_sleep: FakeSleep) -> Fetcher:
    client = httpx.Client(transport=httpx.MockTransport(site_handler))
    return Fetcher(client=client, delay=0, sleep=fake_sleep)
