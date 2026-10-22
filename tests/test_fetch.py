import httpx
import pytest

from books_scraper.fetch import Fetcher, FetchError


def make_fetcher(responses, fake_sleep, **kwargs):
    calls = iter(responses)

    def handler(request):
        item = next(calls)
        if isinstance(item, Exception):
            raise item
        return item

    client = httpx.Client(transport=httpx.MockTransport(handler))
    return Fetcher(client=client, sleep=fake_sleep, delay=0, **kwargs)


def test_retries_server_errors_with_backoff(fake_sleep):
    fetcher = make_fetcher(
        [httpx.Response(503), httpx.ReadTimeout("slow"), httpx.Response(200, text="ok")],
        fake_sleep,
    )

    assert fetcher.get("https://example.test/") == "ok"
    assert fake_sleep.calls == [2.0, 4.0]
    assert fetcher.stats.requests == 3
    assert fetcher.stats.retries == 2


def test_gives_up_after_the_retry_limit(fake_sleep):
    fetcher = make_fetcher([httpx.Response(500)] * 3, fake_sleep, retries=2)

    with pytest.raises(FetchError, match="gave up after 3 tries"):
        fetcher.get("https://example.test/")


def test_does_not_retry_404(fake_sleep):
    fetcher = make_fetcher([httpx.Response(404)], fake_sleep)

    with pytest.raises(FetchError, match="HTTP 404"):
        fetcher.get("https://example.test/")
    assert fake_sleep.calls == []


def test_waits_between_requests(fake_sleep):
    now = [100.0]
    client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200)))
    fetcher = Fetcher(client=client, delay=1.5, sleep=fake_sleep, clock=lambda: now[0])

    fetcher.get("https://example.test/a")
    now[0] += 0.5
    fetcher.get("https://example.test/b")

    assert fake_sleep.calls == [1.0]
