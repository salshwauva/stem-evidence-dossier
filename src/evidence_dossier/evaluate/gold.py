"""Gold labels: the annotated records that evaluation scores against (plan section 49).

The models are boundary models for JSON fixture files. A gold claim has the
shape of an EvidenceClaim without the id and the extraction run, because the
annotator does not know which extractor output it will meet.
"""

import json
from pathlib import Path
from typing import Literal

from pydantic import Field

from evidence_dossier.model import (
    ClaimType,
    ComparabilityLevel,
    Comparator,
    EvidenceSpan,
    FrozenModel,
    Measurement,
    Method,
    ResearchContext,
    Result,
    SourceLevel,
    Stance,
    Term,
)

type Split = Literal["dev", "test"]


class GoldClaim(FrozenModel):
    """One annotated claim, keyed by its research work and a gold key that is unique in the work."""

    gold_key: str
    research_work_id: str
    # Study keys are unique across the dataset, so a caller maps them to predicted study IDs.
    study_key: str
    claim_type: ClaimType
    claim_text: str
    normalized_claim: str | None = None
    subject: Term
    predicate: str
    outcome: str | None = None
    research_context: ResearchContext
    method: Method | None = None
    comparator: Comparator | None = None
    measurement: Measurement | None = None
    result: Result
    evidence_span: EvidenceSpan

    @property
    def claim_key(self) -> str:
        """The dataset-wide key of this claim. Retrieval and stance labels use it as the claim ID."""
        return f"{self.research_work_id}:{self.gold_key}"


class GoldDocument(FrozenModel):
    """The gold claims of one source document, with the source level that limits them."""

    research_work_id: str
    document_id: str
    source_level: SourceLevel
    claims: tuple[GoldClaim, ...] = ()


class GoldRetrieval(FrozenModel):
    """One benchmark query with the claim IDs that a correct retrieval returns."""

    query_id: str
    query_text: str
    relevant_claim_ids: frozenset[str] = Field(default_factory=frozenset)


class GoldStance(FrozenModel):
    """The stance and comparability label of one query and claim pair (plan sections 37 and 39)."""

    query_id: str
    claim_id: str
    stance: Stance
    comparability: ComparabilityLevel


class Dataset(FrozenModel):
    """Every gold label of one split. Prompt changes use the dev split only (plan section 49)."""

    split: Split
    documents: tuple[GoldDocument, ...] = ()
    retrievals: tuple[GoldRetrieval, ...] = ()
    stances: tuple[GoldStance, ...] = ()

    @property
    def claims(self) -> tuple[GoldClaim, ...]:
        return tuple(claim for document in self.documents for claim in document.claims)

    def restrict(self, work_ids: frozenset[str]) -> "Dataset":
        """Return the labels of these works only. Query labels keep the claims that survive."""
        documents = tuple(d for d in self.documents if d.research_work_id in work_ids)
        kept = {claim.claim_key for document in documents for claim in document.claims}
        retrievals = tuple(
            r.model_copy(update={"relevant_claim_ids": r.relevant_claim_ids & kept})
            for r in self.retrievals
        )
        stances = tuple(s for s in self.stances if s.claim_id in kept)
        return Dataset(
            split=self.split, documents=documents, retrievals=retrievals, stances=stances
        )


def load_dataset(directory: Path, split: Split) -> Dataset:
    """Read a gold directory: documents/*.json, retrievals.json and stances.json.

    Each document file holds one GoldDocument. The two list files are optional.
    Files load in name order, so the dataset is the same on every run.
    """
    documents = tuple(
        GoldDocument.model_validate_json(path.read_text())
        for path in sorted((directory / "documents").glob("*.json"))
    )
    return Dataset(
        split=split,
        documents=documents,
        retrievals=tuple(
            GoldRetrieval.model_validate(r) for r in _list(directory / "retrievals.json")
        ),
        stances=tuple(GoldStance.model_validate(s) for s in _list(directory / "stances.json")),
    )


def _list(path: Path) -> list[object]:
    if not path.exists():
        return []
    loaded: object = json.loads(path.read_text())
    if not isinstance(loaded, list):
        raise ValueError(f"{path} must hold a JSON list")
    return loaded
