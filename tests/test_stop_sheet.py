import csv
import json
from collections.abc import Mapping
from pathlib import Path

import pytest

from evidence_dossier.evaluate import (
    StoppedTrial,
    draw_batch,
    fetch_stopped_trials,
    in_cohort,
    write_key,
    write_sheet,
)
from evidence_dossier.evaluate.stop_sheet import KEY_COLUMNS, SHEET_COLUMNS


def study(
    nct_id: str,
    status: str,
    conditions: list[str],
    note: str | None,
    phases: list[str] | None = None,
    sponsor_class: str | None = "OTHER",
) -> dict[str, object]:
    status_module: dict[str, object] = {"overallStatus": status}
    if note is not None:
        status_module["whyStopped"] = note
    return {
        "protocolSection": {
            "identificationModule": {"nctId": nct_id},
            "statusModule": status_module,
            "conditionsModule": {"conditions": conditions},
            "designModule": {"phases": phases or []},
            "sponsorCollaboratorsModule": {"leadSponsor": {"class": sponsor_class}},
        }
    }


class RegistryStub:
    """Serves invented pages by status and page token, and records every request."""

    def __init__(self, pages: Mapping[tuple[str, str | None], dict[str, object]]) -> None:
        self.pages = pages
        self.requests: list[dict[str, str]] = []

    def __call__(self, url: str, params: Mapping[str, str]) -> bytes:
        self.requests.append(dict(params))
        key = (params["filter.overallStatus"], params.get("pageToken"))
        return json.dumps(self.pages.get(key, {"studies": []})).encode()


def trial(nct_id: str, note: str = "Slow recruitment at all sites") -> StoppedTrial:
    return StoppedTrial(nct_id, "TERMINATED", note, ("PHASE2",), "INDUSTRY")


def test_cohort_rule_matches_a_keyword_inside_a_condition_name() -> None:
    assert in_cohort(["Asthma", "Metastatic ADENOCARCINOMA of the colon"])
    assert in_cohort(["Uveal Melanoma"])


def test_cohort_rule_leaves_out_unrelated_conditions() -> None:
    assert not in_cohort(["Asthma", "Type 2 Diabetes"])
    assert not in_cohort([])


def test_fetch_follows_page_tokens_for_each_status_and_applies_the_cohort_rule() -> None:
    stub = RegistryStub(
        {
            ("TERMINATED", None): {
                "studies": [
                    study("NCT99000001", "TERMINATED", ["Breast Cancer"], "Slow recruitment"),
                    study("NCT99000002", "TERMINATED", ["Asthma"], "Funding ended"),
                ],
                "nextPageToken": "page-2",
            },
            ("TERMINATED", "page-2"): {
                "studies": [study("NCT99000003", "TERMINATED", ["Lymphoma"], "  Safety signal  ")]
            },
            ("WITHDRAWN", None): {
                "studies": [
                    study("NCT99000004", "WITHDRAWN", ["Leukemia"], None, ["PHASE1", "PHASE2"])
                ]
            },
        }
    )
    trials = fetch_stopped_trials(stub)
    assert [t.nct_id for t in trials] == ["NCT99000001", "NCT99000003", "NCT99000004"]
    assert trials[1].note == "Safety signal"
    assert trials[2].note == ""
    assert trials[2].phases == ("PHASE1", "PHASE2")
    assert trials[2].sponsor_class == "OTHER"
    assert [(r["filter.overallStatus"], r.get("pageToken")) for r in stub.requests] == [
        ("TERMINATED", None),
        ("TERMINATED", "page-2"),
        ("WITHDRAWN", None),
        ("SUSPENDED", None),
    ]


def test_fetch_keeps_one_record_per_nct_id() -> None:
    stub = RegistryStub(
        {
            ("TERMINATED", None): {
                "studies": [
                    study("NCT99000001", "TERMINATED", ["Cancer"], "First"),
                    study("NCT99000001", "TERMINATED", ["Cancer"], "Second"),
                ]
            }
        }
    )
    assert [t.note for t in fetch_stopped_trials(stub)] == ["Second"]


def test_draw_is_the_same_for_the_same_pool_seed_and_exclusions() -> None:
    pool = [trial(f"NCT9900{n:04d}", f"note {n}") for n in range(40)]
    first = draw_batch(pool, seed="a", size=10, exclude=set())
    assert first == draw_batch(list(reversed(pool)), seed="a", size=10, exclude=set())
    assert first != draw_batch(pool, seed="b", size=10, exclude=set())


def test_draw_skips_excluded_trials_and_empty_notes() -> None:
    pool = [trial("NCT99000001"), trial("NCT99000002"), trial("NCT99000003", note="")]
    drawn = draw_batch(pool, seed="a", size=1, exclude={"NCT99000001"})
    assert [t.nct_id for t in drawn] == ["NCT99000002"]


def test_draw_refuses_a_batch_larger_than_the_candidates() -> None:
    with pytest.raises(ValueError, match="asked for 3 trials and the pool has 2 candidates"):
        draw_batch([trial("NCT99000001"), trial("NCT99000002")], seed="a", size=3, exclude=set())


def test_sheet_shows_the_note_only_and_the_key_holds_the_rest(tmp_path: Path) -> None:
    batch = [
        trial("NCT99000001", 'Sponsor said "stop", then left, twice'),
        StoppedTrial("NCT99000002", "WITHDRAWN", "Line one\nline two", (), None),
    ]
    sheet, key = tmp_path / "sheet.csv", tmp_path / "key.csv"
    write_sheet(batch, sheet)
    write_key(batch, key)
    sheet_rows = list(csv.reader(sheet.open(newline="", encoding="utf-8")))
    key_rows = list(csv.reader(key.open(newline="", encoding="utf-8")))
    assert tuple(sheet_rows[0]) == SHEET_COLUMNS
    assert sheet_rows[1] == ["r001", 'Sponsor said "stop", then left, twice', "", "", "", ""]
    assert sheet_rows[2][:2] == ["r002", "Line one\nline two"]
    assert "NCT99000001" not in sheet.read_text(encoding="utf-8")
    assert tuple(key_rows[0]) == KEY_COLUMNS
    assert key_rows[1] == ["r001", "NCT99000001", "TERMINATED", "PHASE2", "INDUSTRY"]
    assert key_rows[2] == ["r002", "NCT99000002", "WITHDRAWN", "", ""]
