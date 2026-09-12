"""The evidence store: add and get methods for every core record, on SQLite (ADR 0002)."""

import json
import sqlite3
from pathlib import Path
from types import TracebackType
from typing import Any, Self

from pydantic import BaseModel

from evidence_dossier.model import (
    ClaimType,
    Comparator,
    Domain,
    Dossier,
    EvidenceClaim,
    EvidenceSpan,
    ExtractionRun,
    Measurement,
    Method,
    QueryProposition,
    ResearchContext,
    ResearchWork,
    Result,
    Section,
    SourceDocument,
    SourceLevel,
    StanceAssessment,
    Study,
    Term,
    WorkLink,
)
from evidence_dossier.store.migrate import apply_migrations

# Record fields that the tables hold as JSON text.
_WORK_JSON = ("authors", "external_identifiers")
_RUN_JSON = ("errors",)
_QUERY_JSON = ("parse_notes",)
_DOSSIER_JSON = ("corpus_scope", "counts")


class ClaimRejectedError(ValueError):
    """add_claim refused a claim because a relationship or its evidence span does not hold."""


class Store:
    """SQLite storage for the core records, opened on a file path or ":memory:".

    Opening a store applies any pending migration. An add method raises
    sqlite3.IntegrityError when the ID already exists or a referenced record
    is missing. A get method returns None for an unknown ID.
    """

    def __init__(self, path: str | Path) -> None:
        self._conn = sqlite3.connect(path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        apply_migrations(self._conn)

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def add_work(self, work: ResearchWork) -> None:
        self._insert("works", _dump(work, _WORK_JSON))

    def get_work(self, work_id: str) -> ResearchWork | None:
        return _load(ResearchWork, self._fetch("works", work_id), _WORK_JSON)

    def add_work_link(self, link: WorkLink) -> None:
        self._insert("work_links", _dump(link))

    def get_work_links(self, work_id: str) -> list[WorkLink]:
        """Return the links where the work is the source or the target."""
        rows = self._conn.execute(
            "SELECT * FROM work_links WHERE source_work_id = ? OR target_work_id = ?"
            " ORDER BY source_work_id, relation, target_work_id",
            (work_id, work_id),
        ).fetchall()
        return [WorkLink.model_validate(dict(row)) for row in rows]

    def add_source_document(self, document: SourceDocument) -> None:
        self._insert("source_documents", _dump(document))

    def get_source_document(self, document_id: str) -> SourceDocument | None:
        return _load(SourceDocument, self._fetch("source_documents", document_id))

    def add_section(self, section: Section) -> None:
        self._insert("sections", _dump(section))

    def get_section(self, section_id: str) -> Section | None:
        return _load(Section, self._fetch("sections", section_id))

    def list_sections(self, document_id: str) -> list[Section]:
        """Return the sections of a document in ordinal order."""
        rows = self._conn.execute(
            "SELECT * FROM sections WHERE document_id = ? ORDER BY ordinal", (document_id,)
        ).fetchall()
        return [Section.model_validate(dict(row)) for row in rows]

    def add_study(self, study: Study) -> None:
        self._insert("studies", _dump(study))

    def get_study(self, study_id: str) -> Study | None:
        return _load(Study, self._fetch("studies", study_id))

    def add_extraction_run(self, run: ExtractionRun) -> None:
        """Store an extraction run. An INVALID run keeps its raw response and its errors."""
        self._insert("extraction_runs", _dump(run, _RUN_JSON))

    def get_extraction_run(self, run_id: str) -> ExtractionRun | None:
        return _load(ExtractionRun, self._fetch("extraction_runs", run_id), _RUN_JSON)

    def add_claim(self, claim: EvidenceClaim) -> None:
        """Store a claim after the checks on its study and its evidence span pass.

        Raises ClaimRejectedError when the study or the span section is not in
        the store, when either one belongs to another research work, when the
        span names another research work, or when the span text does not match
        the section text.
        """
        prefix = f"claim {claim.id}:"
        study = self.get_study(claim.study_id)
        if study is None:
            raise ClaimRejectedError(f"{prefix} study {claim.study_id} is not in the store")
        if study.research_work_id != claim.research_work_id:
            raise ClaimRejectedError(
                f"{prefix} study {study.id} belongs to research work {study.research_work_id},"
                f" but the claim belongs to {claim.research_work_id}"
            )
        span = claim.evidence_span
        if span.research_work_id != claim.research_work_id:
            raise ClaimRejectedError(
                f"{prefix} the evidence span names research work {span.research_work_id},"
                f" but the claim belongs to {claim.research_work_id}"
            )
        row = self._conn.execute(
            "SELECT sections.*, source_documents.research_work_id AS owner_work_id,"
            " source_documents.source_level AS source_level"
            " FROM sections JOIN source_documents ON source_documents.id = sections.document_id"
            " WHERE sections.id = ?",
            (span.section_id,),
        ).fetchone()
        if row is None:
            raise ClaimRejectedError(f"{prefix} section {span.section_id} is not in the store")
        if row["owner_work_id"] != claim.research_work_id:
            raise ClaimRejectedError(
                f"{prefix} section {span.section_id} belongs to research work"
                f" {row['owner_work_id']}, but the claim belongs to {claim.research_work_id}"
            )
        section = Section.model_validate({field: row[field] for field in Section.model_fields})
        if not span.matches(section):
            raise ClaimRejectedError(
                f"{prefix} the evidence span text does not match the section text"
                f" at offsets {span.start_offset} to {span.end_offset}"
            )
        self._insert("claims", _claim_row(claim, row["source_level"]))

    def get_claim(self, claim_id: str) -> EvidenceClaim | None:
        row = self._fetch("claims", claim_id)
        return None if row is None else _claim_from_row(row)

    def list_claims(
        self,
        *,
        domain: Domain | None = None,
        claim_type: ClaimType | None = None,
        research_work_id: str | None = None,
        study_id: str | None = None,
    ) -> list[EvidenceClaim]:
        """Return the claims that match every given filter, ordered by claim ID."""
        filters = {
            "domain": None if domain is None else domain.value,
            "claim_type": None if claim_type is None else claim_type.value,
            "research_work_id": research_work_id,
            "study_id": study_id,
        }
        params = {column: value for column, value in filters.items() if value is not None}
        sql = "SELECT * FROM claims"
        if params:
            sql += " WHERE " + " AND ".join(f"{column} = :{column}" for column in params)
        rows = self._conn.execute(sql + " ORDER BY id", params).fetchall()
        return [_claim_from_row(row) for row in rows]

    def search_claims(
        self,
        match: str,
        *,
        domain: Domain | None = None,
        source_level: SourceLevel | None = None,
        limit: int | None = 20,
    ) -> list[tuple[EvidenceClaim, float]]:
        """Return the claims whose text matches an FTS5 query, best bm25 rank first.

        The caller builds the match expression with quoted tokens (plan section 36).
        The rank is the bm25 score, where a lower value is a better match. A
        limit of None returns every match.
        """
        params: dict[str, Any] = {"match": match}
        sql = (
            "SELECT claims.*, bm25(claims_fts) AS rank FROM claims_fts"
            " JOIN claims ON claims.rowid = claims_fts.rowid WHERE claims_fts MATCH :match"
        )
        if domain is not None:
            sql += " AND claims.domain = :domain"
            params["domain"] = domain.value
        if source_level is not None:
            sql += " AND claims.source_level = :source_level"
            params["source_level"] = source_level.value
        sql += " ORDER BY rank, claims.id"
        if limit is not None:
            sql += " LIMIT :limit"
            params["limit"] = limit
        rows = self._conn.execute(sql, params).fetchall()
        return [(_claim_from_row(row), row["rank"]) for row in rows]

    def count_claims_by_source_level(self) -> dict[SourceLevel, int]:
        """Return how many stored claims come from each source level (plan section 45)."""
        rows = self._conn.execute(
            "SELECT source_level, COUNT(*) AS n FROM claims GROUP BY source_level"
        ).fetchall()
        return {SourceLevel(row["source_level"]): row["n"] for row in rows}

    def add_query_proposition(self, proposition: QueryProposition) -> None:
        self._insert("query_propositions", _dump(proposition, _QUERY_JSON))

    def get_query_proposition(self, query_id: str) -> QueryProposition | None:
        return _load(QueryProposition, self._fetch("query_propositions", query_id), _QUERY_JSON)

    def add_stance_assessment(self, assessment: StanceAssessment) -> None:
        self._insert("stance_assessments", _dump(assessment))

    def list_stance_assessments(self, query_id: str) -> list[StanceAssessment]:
        """Return the stance assessments for a proposition, ordered by claim ID."""
        rows = self._conn.execute(
            "SELECT * FROM stance_assessments WHERE query_id = ? ORDER BY claim_id", (query_id,)
        ).fetchall()
        return [StanceAssessment.model_validate(dict(row)) for row in rows]

    def add_dossier(self, dossier: Dossier) -> None:
        self._insert("dossiers", _dump(dossier, _DOSSIER_JSON))

    def get_dossier(self, dossier_id: str) -> Dossier | None:
        return _load(Dossier, self._fetch("dossiers", dossier_id), _DOSSIER_JSON)

    # Table and column names in the SQL below come from this module and from
    # the model fields, never from caller input.

    def _insert(self, table: str, values: dict[str, Any]) -> None:
        columns = ", ".join(values)
        placeholders = ", ".join(f":{column}" for column in values)
        with self._conn:
            self._conn.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", values)

    def _fetch(self, table: str, record_id: str) -> sqlite3.Row | None:
        row: sqlite3.Row | None = self._conn.execute(
            f"SELECT * FROM {table} WHERE id = ?", (record_id,)
        ).fetchone()
        return row


def _dump(record: BaseModel, json_fields: tuple[str, ...] = ()) -> dict[str, Any]:
    values = record.model_dump(mode="json")
    for field in json_fields:
        values[field] = json.dumps(values[field])
    return values


def _load[T: BaseModel](
    model: type[T], row: sqlite3.Row | None, json_fields: tuple[str, ...] = ()
) -> T | None:
    if row is None:
        return None
    values = dict(row)
    for field in json_fields:
        values[field] = json.loads(values[field])
    return model.model_validate(values)


def _part_json(part: BaseModel | None) -> str | None:
    return None if part is None else part.model_dump_json()


def _part[T: BaseModel](model: type[T], text: str | None) -> T | None:
    return None if text is None else model.model_validate_json(text)


def _claim_row(claim: EvidenceClaim, source_level: str) -> dict[str, Any]:
    span = claim.evidence_span
    return {
        "id": claim.id,
        "research_work_id": claim.research_work_id,
        "study_id": claim.study_id,
        "extraction_run_id": claim.extraction_run_id,
        "claim_type": claim.claim_type.value,
        "claim_text": claim.claim_text,
        "normalized_claim": claim.normalized_claim,
        "subject_original": claim.subject.original,
        "subject_canonical": claim.subject.canonical,
        "predicate": claim.predicate,
        "outcome": claim.outcome,
        "research_context": claim.research_context.model_dump_json(),
        "method": _part_json(claim.method),
        "comparator": _part_json(claim.comparator),
        "measurement": _part_json(claim.measurement),
        "result": claim.result.model_dump_json(),
        "section_id": span.section_id,
        "start_offset": span.start_offset,
        "end_offset": span.end_offset,
        "source_text": span.source_text,
        "domain": claim.research_context.domain.value,
        "method_canonical": None if claim.method is None else claim.method.name.canonical,
        "comparator_canonical": (
            None if claim.comparator is None else claim.comparator.name.canonical
        ),
        "measurement_canonical": (
            None if claim.measurement is None else claim.measurement.name.canonical
        ),
        "result_direction": claim.result.direction.value,
        "source_level": source_level,
    }


def _claim_from_row(row: sqlite3.Row) -> EvidenceClaim:
    return EvidenceClaim(
        id=row["id"],
        research_work_id=row["research_work_id"],
        study_id=row["study_id"],
        extraction_run_id=row["extraction_run_id"],
        claim_type=ClaimType(row["claim_type"]),
        claim_text=row["claim_text"],
        normalized_claim=row["normalized_claim"],
        subject=Term(original=row["subject_original"], canonical=row["subject_canonical"]),
        predicate=row["predicate"],
        outcome=row["outcome"],
        research_context=ResearchContext.model_validate_json(row["research_context"]),
        method=_part(Method, row["method"]),
        comparator=_part(Comparator, row["comparator"]),
        measurement=_part(Measurement, row["measurement"]),
        result=Result.model_validate_json(row["result"]),
        # add_claim only stores a span whose research work is the research work of the claim.
        evidence_span=EvidenceSpan(
            research_work_id=row["research_work_id"],
            section_id=row["section_id"],
            start_offset=row["start_offset"],
            end_offset=row["end_offset"],
            source_text=row["source_text"],
        ),
    )
