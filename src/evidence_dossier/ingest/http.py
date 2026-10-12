"""The one HTTP seam of the ingest package.

Adapters call HttpClient.get and nothing else, so tests inject a client that
serves recorded fixtures (plan sections 51 and 52). HttpxClient is the client
for real use. PacedHttpClient wraps a client and spaces its requests, for a
source that limits the request rate. RecordingHttpClient saves every reply of
a live client into a folder, and ReplayHttpClient serves that folder with no
network, so a recorded corpus rebuilds offline.
"""

import hashlib
import json
import time
from collections.abc import Callable, Mapping
from pathlib import Path
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


def request_key(url: str, params: Mapping[str, str]) -> str:
    """Return the stable name of a request: the URL path and the parameters that pick a record.

    A URL with no path, such as the root of the PMC cloud bucket, keys on its host.
    """
    host, _, path = url.split("://", 1)[-1].partition("/")
    path = path.strip("/") or host
    picked = {
        name: params[name]
        for name in ("db", "id", "ids", "id_list", "term", "search_query", "prefix")
        if name in params
    }
    suffix = "&".join(f"{name}={value}" for name, value in picked.items())
    return f"{path}?{suffix}" if suffix else path


INDEX_FILE = "index.json"


class RecordingHttpClient:
    """Sends each request through a live client and saves the reply body into a folder.

    The folder holds one file per reply, named by a hash of its request key,
    and index.json, which maps each request key to its file.
    """

    def __init__(self, inner: HttpClient, folder: Path) -> None:
        self._inner = inner
        self._folder = folder

    def get(self, url: str, params: Mapping[str, str]) -> bytes:
        body = self._inner.get(url, params)
        key = request_key(url, params)
        name = hashlib.sha256(key.encode()).hexdigest()[:16] + _extension(body)
        self._folder.mkdir(parents=True, exist_ok=True)
        (self._folder / name).write_bytes(body)
        index_path = self._folder / INDEX_FILE
        index = json.loads(index_path.read_text()) if index_path.is_file() else {}
        index[key] = name
        index_path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n")
        return body


class ReplayHttpClient:
    """Serves the replies that a RecordingHttpClient saved. A request with no reply raises."""

    def __init__(self, folder: Path) -> None:
        self._folder = folder
        index_path = folder / INDEX_FILE
        self._index: dict[str, str] = (
            json.loads(index_path.read_text()) if index_path.is_file() else {}
        )

    def get(self, url: str, params: Mapping[str, str]) -> bytes:
        key = request_key(url, params)
        name = self._index.get(key)
        if name is None:
            raise LookupError(f"no recorded reply for {key} in {self._folder}")
        return (self._folder / name).read_bytes()


def _extension(body: bytes) -> str:
    start = body.lstrip()[:1]
    if start == b"<":
        return ".xml"
    if start in (b"{", b"["):
        return ".json"
    return ".txt"
