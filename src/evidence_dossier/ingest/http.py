"""The one HTTP seam of the ingest package.

Adapters call HttpClient.get and nothing else, so tests inject a client that
serves recorded fixtures (plan sections 51 and 52). HttpxClient is the client
for real use.
"""

from collections.abc import Mapping
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
