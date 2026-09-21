from collections.abc import Mapping

import pytest

from evidence_dossier.ingest import PacedHttpClient


class FakeTime:
    """A clock that moves only when the client sleeps or a test advances it."""

    def __init__(self) -> None:
        self.now = 100.0
        self.sleeps: list[float] = []

    def clock(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


class CountingClient:
    def __init__(self, fail: bool = False) -> None:
        self.calls = 0
        self.fail = fail

    def get(self, url: str, params: Mapping[str, str]) -> bytes:
        self.calls += 1
        if self.fail:
            raise ConnectionError("source unavailable")
        return b"ok"


def test_the_first_request_goes_out_without_a_wait() -> None:
    time = FakeTime()
    client = PacedHttpClient(CountingClient(), 3.0, clock=time.clock, sleep=time.sleep)
    assert client.get("https://example.invalid", {}) == b"ok"
    assert time.sleeps == []


def test_a_quick_second_request_waits_out_the_interval() -> None:
    time = FakeTime()
    client = PacedHttpClient(CountingClient(), 3.0, clock=time.clock, sleep=time.sleep)
    client.get("https://example.invalid", {})
    time.now += 1.0
    client.get("https://example.invalid", {})
    assert time.sleeps == [2.0]


def test_a_late_second_request_does_not_wait() -> None:
    time = FakeTime()
    client = PacedHttpClient(CountingClient(), 3.0, clock=time.clock, sleep=time.sleep)
    client.get("https://example.invalid", {})
    time.now += 5.0
    client.get("https://example.invalid", {})
    assert time.sleeps == []


def test_a_failed_request_still_counts_for_the_interval() -> None:
    time = FakeTime()
    inner = CountingClient(fail=True)
    client = PacedHttpClient(inner, 3.0, clock=time.clock, sleep=time.sleep)
    with pytest.raises(ConnectionError):
        client.get("https://example.invalid", {})
    inner.fail = False
    client.get("https://example.invalid", {})
    assert time.sleeps == [3.0]
    assert inner.calls == 2
