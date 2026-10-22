"""HTTP fetching with a polite delay and retries."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass

import httpx

log = logging.getLogger(__name__)

RETRY_STATUS = {429, 500, 502, 503, 504}
USER_AGENT = "books-scraper/0.1 (portfolio demo; +https://github.com/pequin/books-scraper)"


class FetchError(Exception):
    """A page could not be downloaded after all retries."""


@dataclass
class Stats:
    """Counters printed at the end of a run."""

    requests: int = 0
    retries: int = 0


class Fetcher:
    """Download pages one at a time, waiting ``delay`` seconds between requests.

    Timeouts, connection errors, 429, and 5xx responses are retried up to
    ``retries`` times with exponential backoff (``backoff``, then twice that,
    and so on). Other 4xx responses fail at once, because retrying them does
    not help.
    """

    def __init__(
        self,
        client: httpx.Client | None = None,
        delay: float = 1.0,
        retries: int = 3,
        backoff: float = 2.0,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.client = client or httpx.Client(
            headers={"User-Agent": USER_AGENT}, timeout=20.0, follow_redirects=True
        )
        self.delay = delay
        self.retries = retries
        self.backoff = backoff
        self.sleep = sleep
        self.clock = clock
        self.stats = Stats()
        self._last_request: float | None = None

    def _wait_turn(self) -> None:
        if self._last_request is not None:
            remaining = self.delay - (self.clock() - self._last_request)
            if remaining > 0:
                self.sleep(remaining)
        self._last_request = self.clock()

    def get(self, url: str) -> str:
        """Return the page body as text, or raise FetchError."""
        attempt = 0
        while True:
            self._wait_turn()
            self.stats.requests += 1
            try:
                response = self.client.get(url)
            except httpx.TransportError as exc:
                problem = f"{type(exc).__name__}: {exc}"
            else:
                if response.status_code < 400:
                    return response.text
                if response.status_code not in RETRY_STATUS:
                    msg = f"{url}: HTTP {response.status_code}"
                    raise FetchError(msg)
                problem = f"HTTP {response.status_code}"
            if attempt >= self.retries:
                msg = f"{url}: {problem} (gave up after {attempt + 1} tries)"
                raise FetchError(msg)
            wait = self.backoff * 2**attempt
            log.warning("%s: %s, retrying in %.0fs", url, problem, wait)
            self.stats.retries += 1
            attempt += 1
            self.sleep(wait)

    def close(self) -> None:
        self.client.close()
