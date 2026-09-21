"""The one HTTP seam of the ingest package.

Adapters call HttpClient.get and nothing else, so tests inject a client that
serves recorded fixtures (plan sections 51 and 52). HttpxClient is the client
for real use. PacedHttpClient wraps a client and spaces its requests, for a
source that limits the request rate.
"""

import time
from collections.abc import Callable, Mapping
from typing import Protocol

import httpx

DEFAULT_TIMEOUT_SECONDS = 30.0


class HttpClient(Protocol):
    """A GET request with query parameters that returns the response body."""

    def get(self, url: str, params: Mapping[str, str]) -> bytes: ...


class HttpxClient:
    """The network client. A response with a 4xx or 5xx status raises httpx.HTTPStatusError."""

    def __init__(self, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS) -> None:
        self._client = httpx.Client(timeout=timeout_seconds, follow_redirects=True)

    def get(self, url: str, params: Mapping[str, str]) -> bytes:
        response = self._client.get(url, params=dict(params))
        response.raise_for_status()
        return response.content

    def close(self) -> None:
        self._client.close()


class PacedHttpClient:
    """Waits until min_interval seconds have passed since the previous request, then sends.

    The arXiv API asks for at least three seconds between requests, and NCBI
    for no more than three requests a second without an API key.
    """

    def __init__(
        self,
        inner: HttpClient,
        min_interval: float,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._inner = inner
        self._min_interval = min_interval
        self._clock = clock
        self._sleep = sleep
        self._last: float | None = None

    def get(self, url: str, params: Mapping[str, str]) -> bytes:
        if self._last is not None:
            wait = self._last + self._min_interval - self._clock()
            if wait > 0:
                self._sleep(wait)
        try:
            return self._inner.get(url, params)
        finally:
            self._last = self._clock()
