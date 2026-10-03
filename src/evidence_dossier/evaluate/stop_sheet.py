"""The gold sheet of stop reason notes (docs/stop-reason-guidelines.md).

A stopped trial is a ClinicalTrials.gov record with the status TERMINATED,
WITHDRAWN or SUSPENDED. The sheet holds the Why Stopped note of a random draw
of those records, for an annotator to label. The fetch is a callable, so this
package never imports the ingest package, and tests serve invented pages.

The sheet shows the note and nothing else. A second file, the key, maps each
row back to its record, status, phases and sponsor class. The annotator does
not open the key, so a label cannot follow the pattern the dashboard compares.
"""

import csv
import random
from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

type Fetch = Callable[[str, Mapping[str, str]], bytes]

REGISTRY_STUDIES_URL = "https://clinicaltrials.gov/api/v2/studies"
STOPPED_STATUSES = ("TERMINATED", "WITHDRAWN", "SUSPENDED")
PAGE_SIZE = 1000
FIELDS = "NCTId,Condition,WhyStopped,OverallStatus,Phase,LeadSponsorClass"

# Definition 1 of the Biotech Dashboard (docs/definitions.md in that repository):
# a trial is in the oncology cohort when any condition string contains one of
# these words, compared case-insensitively. Keep the two lists the same.
COHORT_KEYWORDS = (
    "cancer",
    "carcinoma",
    "tumor",
    "neoplasm",
    "lymphoma",
    "leukemia",
    "melanoma",
    "sarcoma",
    "myeloma",
)

SHEET_COLUMNS = ("row", "note", "label", "label2", "unsure", "comment")
KEY_COLUMNS = ("row", "nct_id", "status", "phases", "sponsor_class")


@dataclass(frozen=True)
class StoppedTrial:
    """One stopped cohort trial. The note is empty when the sponsor wrote none."""

    nct_id: str
    status: str
    note: str
    phases: tuple[str, ...]
    sponsor_class: str | None


class _Lenient(BaseModel):
    """A boundary model for the registry reply, which carries far more fields than the sheet needs."""

    model_config = ConfigDict(extra="ignore")


class _Identification(_Lenient):
    nct_id: str = Field(alias="nctId")


class _Status(_Lenient):
    overall_status: str = Field(alias="overallStatus")
    why_stopped: str | None = Field(default=None, alias="whyStopped")


class _Conditions(_Lenient):
    conditions: list[str] = []


class _Design(_Lenient):
    phases: list[str] = []


class _LeadSponsor(_Lenient):
    sponsor_class: str | None = Field(default=None, alias="class")


class _Sponsors(_Lenient):
    lead_sponsor: _LeadSponsor = Field(default_factory=_LeadSponsor, alias="leadSponsor")


class _Protocol(_Lenient):
    identification: _Identification = Field(alias="identificationModule")
    status: _Status = Field(alias="statusModule")
    conditions: _Conditions = Field(default_factory=_Conditions, alias="conditionsModule")
    design: _Design = Field(default_factory=_Design, alias="designModule")
    sponsors: _Sponsors = Field(default_factory=_Sponsors, alias="sponsorCollaboratorsModule")


class _Study(_Lenient):
    protocol: _Protocol = Field(alias="protocolSection")


class _Page(_Lenient):
    studies: list[_Study] = []
    next_page_token: str | None = Field(default=None, alias="nextPageToken")


def in_cohort(conditions: Sequence[str]) -> bool:
    """Apply the oncology cohort rule to the condition strings of a trial."""
    lowered = [condition.lower() for condition in conditions]
    return any(keyword in condition for condition in lowered for keyword in COHORT_KEYWORDS)


def fetch_stopped_trials(fetch: Fetch) -> list[StoppedTrial]:
    """Return every stopped cohort trial, one record per NCT ID, in the order the registry sends them.

    The request names the status and leaves the condition open. The cohort rule
    runs here, on the condition strings, because the registry search matches
    whole words and misses a keyword inside a longer condition name.
    """
    trials: dict[str, StoppedTrial] = {}
    for status in STOPPED_STATUSES:
        token: str | None = None
        while True:
            params = {"filter.overallStatus": status, "pageSize": str(PAGE_SIZE), "fields": FIELDS}
            if token is not None:
                params["pageToken"] = token
            page = _Page.model_validate_json(fetch(REGISTRY_STUDIES_URL, params))
            for study in page.studies:
                protocol = study.protocol
                if not in_cohort(protocol.conditions.conditions):
                    continue
                nct_id = protocol.identification.nct_id
                trials[nct_id] = StoppedTrial(
                    nct_id=nct_id,
                    status=protocol.status.overall_status,
                    note=(protocol.status.why_stopped or "").strip(),
                    phases=tuple(protocol.design.phases),
                    sponsor_class=protocol.sponsors.lead_sponsor.sponsor_class,
                )
            token = page.next_page_token
            if token is None:
                break
    return list(trials.values())


def draw_batch(
    pool: Sequence[StoppedTrial], *, seed: str, size: int, exclude: Collection[str]
) -> list[StoppedTrial]:
    """Draw size trials with a note at random, in the order of the sheet.

    The candidates are sorted by NCT ID before the draw, so the same pool, seed
    and exclusions give the same batch on every run.
    """
    candidates = sorted(
        (trial for trial in pool if trial.note and trial.nct_id not in exclude),
        key=lambda trial: trial.nct_id,
    )
    if size > len(candidates):
        raise ValueError(f"asked for {size} trials and the pool has {len(candidates)} candidates")
    return random.Random(seed).sample(candidates, size)


def row_id(index: int) -> str:
    """Return the sheet row name of the trial at a zero based position."""
    return f"r{index + 1:03d}"


def write_sheet(batch: Sequence[StoppedTrial], path: Path) -> None:
    """Write the sheet the annotator fills in: the row name, the note and empty label columns."""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(SHEET_COLUMNS)
        for index, trial in enumerate(batch):
            writer.writerow([row_id(index), trial.note, "", "", "", ""])


def write_key(batch: Sequence[StoppedTrial], path: Path) -> None:
    """Write the key that joins each row name to its record. The annotator does not open it."""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(KEY_COLUMNS)
        for index, trial in enumerate(batch):
            writer.writerow(
                [
                    row_id(index),
                    trial.nct_id,
                    trial.status,
                    "|".join(trial.phases),
                    trial.sponsor_class or "",
                ]
            )
