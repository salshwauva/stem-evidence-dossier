"""The app factory and the routes from plan section 48.

Each request opens the store on its own, because a sqlite3 connection
belongs to the thread that opened it and FastAPI runs sync routes in a
thread pool.
"""

from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from pydantic import Field

from evidence_dossier.evaluate import (
    Dataset,
    EvaluationReport,
    SearchHit,
    Split,
    evaluate_store,
    load_dataset,
)
from evidence_dossier.model import (
    Domain,
    Dossier,
    EvidenceClaim,
    FrozenModel,
    QueryProposition,
    ResearchWork,
    SourceLevel,
    StanceAssessment,
    WorkLink,
)
from evidence_dossier.query import EvidenceResults, build_dossier, search_evidence
from evidence_dossier.store import Store

MAX_LIMIT = 100


class SearchRequest(FrozenModel):
    """A proposition with the optional domain, source level and context filters."""

    text: str = Field(min_length=1)
    domain: Domain | None = None
    source_level: SourceLevel | None = None
    limit: int = Field(default=20, ge=1, le=MAX_LIMIT)
    dataset: str | None = None
    system: str | None = None
    population: str | None = None


class DossierRequest(FrozenModel):
    text: str = Field(min_length=1)
    domain: Domain | None = None
    source_level: SourceLevel | None = None
    limit: int = Field(default=20, ge=1, le=MAX_LIMIT)


class DossierCreated(FrozenModel):
    dossier: Dossier
    results: EvidenceResults


class DossierDetail(FrozenModel):
    dossier: Dossier
    proposition: QueryProposition
    assessments: tuple[StanceAssessment, ...]


class WorkDetail(FrozenModel):
    work: ResearchWork
    links: tuple[WorkLink, ...]
    claim_ids: tuple[str, ...]


class ConflictsResponse(FrozenModel):
    conflicts: tuple[str, ...]
    note: str


class EvaluationResponse(EvaluationReport):
    """The report with its rendered markdown, so one response serves both readers."""

    markdown: str


def _search_hits(store: Store, query_text: str) -> list[SearchHit]:
    """Run the query package for one gold query and return its results in rank order.

    The adapter lives here because api may import query and evaluate, while
    evaluate imports neither (ADR 0008). The groups carry the stance and the
    comparability, and the candidates carry the rank order.
    """
    results = search_evidence(store, query_text, limit=MAX_LIMIT)
    items = {item.claim.id: item for group in results.groups for item in group.items}
    hits: list[SearchHit] = []
    for candidate in results.candidates:
        item = items.get(candidate.claim.id)
        if item is None:
            continue
        hits.append(
            SearchHit(
                claim_id=item.claim.id,
                stance=item.stance,
                comparability=item.comparability,
                reason=item.stance_reason,
            )
        )
    return hits


def _configuration(store: Store, dataset: Dataset) -> tuple[str, str, str]:
    """Return the model, prompt and schema version of the claims under evaluation.

    The versions come from the extraction runs of the stored claims, because
    plan section 50 asks every report to name them. A value that the runs do
    not agree on reads "mixed", and a claim set without a run reads "unknown".
    """
    models: set[str] = set()
    prompts: set[str] = set()
    schemas: set[str] = set()
    for document in dataset.documents:
        for claim in store.list_claims(research_work_id=document.research_work_id):
            if claim.extraction_run_id is None:
                continue
            run = store.get_extraction_run(claim.extraction_run_id)
            if run is None:
                continue
            models.add(run.model_identifier)
            prompts.add(run.prompt_version)
            schemas.add(run.schema_version)
    return _one(models), _one(prompts), _one(schemas)


def _one(values: set[str]) -> str:
    if not values:
        return "unknown"
    if len(values) > 1:
        return "mixed"
    return values.pop()


def _open_store(request: Request) -> Iterator[Store]:
    with Store(request.app.state.store_path) as store:
        yield store


StoreDep = Annotated[Store, Depends(_open_store)]


class _GoldNotes(FrozenModel):
    """The notes.json sidecar of a gold directory: sentences about where its inputs came from."""

    notes: tuple[str, ...]


def _gold_notes(gold_path: Path) -> tuple[str, ...]:
    """Return the notes that a gold directory declares about itself, or none.

    A reader meets the scores on the evaluation route, so the provenance of
    the inputs travels with them (plan section 50: no example score becomes a
    claimed achievement).
    """
    path = gold_path / "notes.json"
    if not path.is_file():
        return ()
    return _GoldNotes.model_validate_json(path.read_text(encoding="utf-8")).notes


def create_app(store_path: str | Path, *, gold_dir: str | Path | None = None) -> FastAPI:
    """Return the app. Every route opens the store at store_path for its own request.

    gold_dir holds the gold labels that GET /evaluation scores against. Without
    it that route answers 404, because there is nothing to score.
    """
    app = FastAPI(title="STEM Evidence Dossier", version="0.1.0")
    app.state.store_path = store_path
    gold_path = None if gold_dir is None else Path(gold_dir)
    app.state.gold_dir = gold_path

    @app.post("/search/evidence")
    def search(body: SearchRequest, store: StoreDep) -> EvidenceResults:
        return search_evidence(
            store,
            body.text,
            domain=body.domain,
            source_level=body.source_level,
            limit=body.limit,
            dataset=body.dataset,
            system=body.system,
            population=body.population,
        )

    @app.post("/dossiers", status_code=201)
    def create_dossier(body: DossierRequest, store: StoreDep) -> DossierCreated:
        dossier, results = build_dossier(
            store, body.text, domain=body.domain, source_level=body.source_level, limit=body.limit
        )
        return DossierCreated(dossier=dossier, results=results)

    @app.get("/dossiers/{dossier_id}")
    def get_dossier(dossier_id: str, store: StoreDep) -> DossierDetail:
        dossier = store.get_dossier(dossier_id)
        if dossier is None:
            raise HTTPException(status_code=404, detail=f"dossier {dossier_id} is not in the store")
        proposition = store.get_query_proposition(dossier.query_id)
        if proposition is None:
            raise HTTPException(
                status_code=404, detail=f"query {dossier.query_id} is not in the store"
            )
        return DossierDetail(
            dossier=dossier,
            proposition=proposition,
            assessments=tuple(store.list_stance_assessments(dossier.query_id)),
        )

    @app.get("/claims/{claim_id}")
    def get_claim(claim_id: str, store: StoreDep) -> EvidenceClaim:
        claim = store.get_claim(claim_id)
        if claim is None:
            raise HTTPException(status_code=404, detail=f"claim {claim_id} is not in the store")
        return claim

    @app.get("/works/{work_id}")
    def get_work(work_id: str, store: StoreDep) -> WorkDetail:
        work = store.get_work(work_id)
        if work is None:
            raise HTTPException(status_code=404, detail=f"work {work_id} is not in the store")
        claims = store.list_claims(research_work_id=work_id)
        return WorkDetail(
            work=work,
            links=tuple(store.get_work_links(work_id)),
            claim_ids=tuple(claim.id for claim in claims),
        )

    @app.get("/conflicts")
    def conflicts() -> ConflictsResponse:
        return ConflictsResponse(
            conflicts=(),
            note="Conflict pairs belong to the advanced dossier sequence (plan section 54).",
        )

    @app.get("/evaluation")
    def evaluation(store: StoreDep, split: Annotated[Split, Query()] = "dev") -> EvaluationResponse:
        """Score the stored claims of the gold works, plus search on the gold queries."""
        if gold_path is None:
            raise HTTPException(
                status_code=404, detail="no gold directory is configured for this app"
            )
        dataset = load_dataset(gold_path, split)
        notes = _gold_notes(gold_path)
        model_identifier, prompt_version, schema_version = _configuration(store, dataset)
        report = evaluate_store(
            store,
            dataset,
            model_identifier=model_identifier,
            prompt_version=prompt_version,
            schema_version=schema_version,
            now=datetime.now(UTC),
            search=_search_hits,
            notes=notes,
        )
        return EvaluationResponse.model_validate(
            {**report.model_dump(), "markdown": report.to_markdown()}
        )

    return app
