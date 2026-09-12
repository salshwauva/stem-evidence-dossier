"""The app factory and the routes from plan section 48.

Each request opens the store on its own, because a sqlite3 connection
belongs to the thread that opened it and FastAPI runs sync routes in a
thread pool.
"""

from collections.abc import Iterator
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import Field

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


def _open_store(request: Request) -> Iterator[Store]:
    with Store(request.app.state.store_path) as store:
        yield store


StoreDep = Annotated[Store, Depends(_open_store)]


def create_app(store_path: str | Path) -> FastAPI:
    """Return the app. Every route opens the store at store_path for its own request."""
    app = FastAPI(title="STEM Evidence Dossier", version="0.1.0")
    app.state.store_path = store_path

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
    def evaluation() -> JSONResponse:
        return JSONResponse(
            status_code=501,
            content={
                "detail": "The evaluate package on the evaluation branch produces the report."
                " A later commit wires this route to it."
            },
        )

    return app
