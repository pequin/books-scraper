from decimal import Decimal

from books_scraper.parse import parse_categories, parse_list
from tests.conftest import BASE, MYSTERY, fixture


def test_parse_categories_reads_sidebar():
    categories = parse_categories(fixture("index.html"), BASE + "index.html")

    assert len(categories) == 50
    assert categories[0] == ("Travel", BASE + "catalogue/category/books/travel_2/index.html")
    assert ("Mystery", MYSTERY + "index.html") in categories


def test_parse_list_reads_books_and_next_page():
    books, next_url = parse_list(
        fixture("category_mystery_page1.html"), MYSTERY + "index.html", "Mystery"
    )

    assert len(books) == 20
    assert next_url == MYSTERY + "page-2.html"
    first = books[0]
    assert first.title == "Sharp Objects"
    assert first.price == Decimal("47.82")
    assert first.currency == "GBP"
    assert first.rating == 4
    assert first.in_stock is True
    assert first.category == "Mystery"
    assert first.url == BASE + "catalogue/sharp-objects_997/index.html"


def test_parse_list_uses_full_title_not_the_shortened_link_text():
    books, _ = parse_list(fixture("category_mystery_page1.html"), MYSTERY + "index.html", "M")

    assert books[1].title == "In a Dark, Dark Wood"


def test_parse_list_last_page_has_no_next():
    books, next_url = parse_list(
        fixture("category_mystery_page2.html"), MYSTERY + "page-2.html", "Mystery"
    )

    assert books
    assert next_url is None
