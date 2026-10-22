"""HTML parsing for books.toscrape.com pages."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin

from bs4 import BeautifulSoup

RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


@dataclass(frozen=True)
class Book:
    """One book as shown on a category list page."""

    title: str
    price: Decimal
    currency: str
    rating: int
    in_stock: bool
    category: str
    url: str

    def as_row(self) -> dict[str, str | int | bool]:
        row = asdict(self)
        row["price"] = str(self.price)
        return row


FIELDS = ["title", "price", "currency", "rating", "in_stock", "category", "url"]


def parse_categories(html: str, page_url: str) -> list[tuple[str, str]]:
    """Return (name, absolute URL) for every category in the sidebar."""
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select("div.side_categories ul li ul li a")
    return [(a.get_text(strip=True), urljoin(page_url, a["href"])) for a in links]


def _price(text: str) -> tuple[Decimal, str]:
    text = text.strip()
    symbol, amount = text[:1], text[1:]
    currency = {"£": "GBP", "$": "USD", "€": "EUR"}.get(symbol, "")
    if not currency:
        amount = text
    try:
        return Decimal(amount.replace(",", "")), currency
    except InvalidOperation as exc:
        msg = f"cannot read price {text!r}"
        raise ValueError(msg) from exc


def parse_list(html: str, page_url: str, category: str) -> tuple[list[Book], str | None]:
    """Parse one list page. Return its books and the URL of the next page, if any."""
    soup = BeautifulSoup(html, "html.parser")
    books = []
    for pod in soup.select("article.product_pod"):
        link = pod.select_one("h3 a")
        rating_classes = pod.select_one("p.star-rating")["class"]
        rating = next((RATINGS[c] for c in rating_classes if c in RATINGS), 0)
        price, currency = _price(pod.select_one("p.price_color").get_text())
        availability = pod.select_one("p.availability").get_text(" ", strip=True)
        books.append(
            Book(
                title=link.get("title") or link.get_text(strip=True),
                price=price,
                currency=currency,
                rating=rating,
                in_stock=availability.lower().startswith("in stock"),
                category=category,
                url=urljoin(page_url, link["href"]),
            )
        )
    next_link = soup.select_one("ul.pager li.next a")
    next_url = urljoin(page_url, next_link["href"]) if next_link else None
    return books, next_url
