from collections.abc import Mapping
from pathlib import Path

import pytest

from evidence_dossier.ingest import PacedHttpClient, RecordingHttpClient, ReplayHttpClient


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


class FixedClient:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def get(self, url: str, params: Mapping[str, str]) -> bytes:
        return self.body


def test_a_recorded_reply_replays_without_the_live_client(tmp_path: Path) -> None:
    url = "https://export.arxiv.org/api/query"
    recorder = RecordingHttpClient(FixedClient(b"<feed/>"), tmp_path)
    assert recorder.get(url, {"id_list": "9901.00001", "max_results": "1"}) == b"<feed/>"

    replay = ReplayHttpClient(tmp_path)
    assert replay.get(url, {"id_list": "9901.00001", "max_results": "1"}) == b"<feed/>"
    assert sorted(path.suffix for path in tmp_path.iterdir()) == [".json", ".xml"]


def test_two_recorders_share_one_index(tmp_path: Path) -> None:
    RecordingHttpClient(FixedClient(b"<a/>"), tmp_path).get("https://a.example/x", {"id": "1"})
    RecordingHttpClient(FixedClient(b"{}"), tmp_path).get("https://b.example/y", {"id": "2"})

    replay = ReplayHttpClient(tmp_path)
    assert replay.get("https://a.example/x", {"id": "1"}) == b"<a/>"
    assert replay.get("https://b.example/y", {"id": "2"}) == b"{}"


def test_replay_names_a_request_it_has_no_reply_for(tmp_path: Path) -> None:
    with pytest.raises(LookupError, match="no recorded reply for api/query\\?id_list=9901.00002"):
        ReplayHttpClient(tmp_path).get(
            "https://export.arxiv.org/api/query", {"id_list": "9901.00002"}
        )
