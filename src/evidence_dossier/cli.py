"""The evidence-dossier command: ingest, extract, search, claim and serve (plan section 58).

The command composes the pipeline, so it imports the other subpackages and no
subpackage imports it, the same exception that api holds. run() takes the
HTTP client and the extraction provider as arguments, so tests pass recorded
ones and no test opens a network connection.
"""

import argparse
import sqlite3
import sys
import textwrap
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import TextIO

import httpx

from evidence_dossier.extract import (
    ClaudeCliProvider,
    ExtractionProvider,
    ProviderError,
    extract_document,
)
from evidence_dossier.ingest import (
    ArxivAdapter,
    HttpClient,
    HttpxClient,
    LiteratureSourceAdapter,
    PacedHttpClient,
    PubMedAdapter,
    ingest_work,
)
from evidence_dossier.model import Domain, EvidenceClaim, Term
from evidence_dossier.normalize import normalize_claim
from evidence_dossier.query import (
    EvidenceItem,
    EvidenceResults,
    ModelQueryExpander,
    QueryExpander,
    search_evidence,
)
from evidence_dossier.store import Store

DEFAULT_DB = "dossier.db"
# Seconds between two requests. The arXiv API asks for three. NCBI allows three
# requests a second without an API key.
ARXIV_INTERVAL = 3.0
NCBI_INTERVAL = 0.34
WIDTH = 88


def main(argv: Sequence[str] | None = None) -> int:
    return run(sys.argv[1:] if argv is None else argv)


def run(
    argv: Sequence[str],
    *,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
    http: HttpClient | None = None,
    provider: ExtractionProvider | None = None,
    expander: QueryExpander | None = None,
) -> int:
    """Run one command and return its exit status.

    Without an http client, each source gets a live client paced to its rate
    limit. Without a provider, extract runs the claude command line tool.
    Search expands its query only when --expand-model names a model, and
    without an expander that flag runs the claude command line tool.
    """
    args = _parser().parse_args(argv)
    if args.command == "serve":
        return _serve(args.db, args.gold, err)
    try:
        with Store(args.db) as store:
            if args.command == "ingest":
                return _ingest(store, args.source, args.identifiers, http, out)
            if args.command == "extract":
                chosen = provider or ClaudeCliProvider(args.model)
                return _extract(store, args.document_ids, chosen, out)
            if args.command == "search":
                domain = None if args.domain is None else Domain(args.domain)
                if expander is None and args.expand_model is not None:
                    expander = _cli_expander(args.expand_model)
                results = search_evidence(
                    store, args.text, domain=domain, limit=args.limit, expander=expander
                )
                _print_results(store, results, out)
                return 0
            return _print_claim(store, args.claim_id, out, err)
    except (LookupError, ProviderError, httpx.HTTPError) as error:
        print(f"error: {error}", file=err)
        return 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="evidence-dossier",
        description="Provenance-linked evidence claims from STEM research.",
    )
    parser.add_argument("--db", default=DEFAULT_DB, help=f"SQLite store (default {DEFAULT_DB})")
    commands = parser.add_subparsers(dest="command", required=True)

    ingest = commands.add_parser("ingest", help="fetch works and store their best text")
    ingest.add_argument("source", choices=("arxiv", "pubmed"))
    ingest.add_argument("identifiers", nargs="+", help="arXiv identifiers or PMIDs")

    extract = commands.add_parser("extract", help="extract the claims of stored documents")
    extract.add_argument("document_ids", nargs="+")
    extract.add_argument("--model", required=True, help="model for the claude command line tool")

    search = commands.add_parser("search", help="find the claims that bear on a proposition")
    search.add_argument("text")
    search.add_argument("--domain", choices=[domain.value for domain in Domain])
    search.add_argument("--limit", type=int, default=20)
    search.add_argument(
        "--expand-model",
        help="model for the claude command line tool that adds related search terms",
    )

    claim = commands.add_parser("claim", help="show one claim with its context and passage")
    claim.add_argument("claim_id")

    serve = commands.add_parser("serve", help="serve the API on http://127.0.0.1:8000")
    serve.add_argument("--gold", help="gold directory for GET /evaluation")
    return parser


def _cli_expander(model: str) -> QueryExpander:
    """Return an expander that asks the claude command line tool for related search terms."""
    provider = ClaudeCliProvider(model)
    return ModelQueryExpander(lambda prompt: provider.complete(prompt).text)


def _adapter(source: str, http: HttpClient | None) -> LiteratureSourceAdapter:
    if source == "arxiv":
        return ArxivAdapter(http or PacedHttpClient(HttpxClient(), ARXIV_INTERVAL))
    return PubMedAdapter(http or PacedHttpClient(HttpxClient(), NCBI_INTERVAL))


def _ingest(
    store: Store,
    source: str,
    identifiers: Sequence[str],
    http: HttpClient | None,
    out: TextIO,
) -> int:
    adapter = _adapter(source, http)
    for identifier in identifiers:
        result = ingest_work(store, adapter, identifier, fetched_at=datetime.now(UTC))
        work = store.get_work(result.work_id)
        title = "" if work is None else work.title
        sections = "section" if result.section_count == 1 else "sections"
        facts = [
            result.document_id,
            result.source_level.value,
            f"{result.section_count} {sections}",
            "stored" if result.stored else "unchanged",
        ]
        if result.license is not None:
            facts.append(f"license {result.license}")
        print(f"{source} {identifier}: {title}", file=out)
        print(f"  {', '.join(facts)}", file=out)
        if result.fetch_error is not None:
            print(f"  full text failed, kept the fallback: {result.fetch_error}", file=out)
    return 0


def _extract(
    store: Store, document_ids: Sequence[str], provider: ExtractionProvider, out: TextIO
) -> int:
    status = 0
    for document_id in document_ids:
        try:
            run = extract_document(
                store, document_id, provider, normalizer=normalize_claim, now=datetime.now(UTC)
            )
        except sqlite3.IntegrityError as error:
            print(f"{document_id}: nothing stored, an earlier extraction holds its IDs", file=out)
            print(f"  {error}", file=out)
            status = 1
            continue
        document = store.get_source_document(document_id)
        work_id = "" if document is None else document.research_work_id
        count = sum(
            1
            for claim in store.list_claims(research_work_id=work_id)
            if claim.extraction_run_id == run.id
        )
        print(f"{document_id}: {run.validation_status.value}, {count} claims", file=out)
        for message in run.errors:
            print(f"  {message}", file=out)
        if run.errors:
            status = 1
    return status


def _print_results(store: Store, results: EvidenceResults, out: TextIO) -> None:
    proposition = results.proposition
    print(f"Query: {proposition.text}", file=out)
    fields = [
        f'subject "{proposition.subject}"',
        f"relationship {proposition.relationship}",
    ]
    if proposition.measurement is not None:
        fields.append(f'measurement "{proposition.measurement}"')
    if proposition.comparator is not None:
        fields.append(f'comparator "{proposition.comparator}"')
    print(f"Parsed: {' | '.join(fields)}", file=out)
    for note in proposition.parse_notes:
        print(f"  - {note}", file=out)
    count = len(results.candidates)
    print(f"Retrieved {count} {'claim' if count == 1 else 'claims'}.", file=out)
    for group in results.groups:
        if group.items:
            print(f"\n{group.stance.value} ({len(group.items)})", file=out)
        for item in group.items:
            _print_item(store, item, out)
    empty = [group.stance.value for group in results.groups if not group.items]
    if empty:
        print(f"\nNo claims: {', '.join(empty)}", file=out)


def _print_item(store: Store, item: EvidenceItem, out: TextIO) -> None:
    claim = item.claim
    work = store.get_work(claim.research_work_id)
    title = claim.research_work_id if work is None else work.title
    year = (
        "" if work is None or work.publication_date is None else f" ({work.publication_date.year})"
    )
    print(f"  {claim.id}  {title}{year}", file=out)
    _wrapped(out, "Claim: ", claim.claim_text, indent=4)
    _wrapped(out, "Why: ", item.stance_reason, indent=4)
    print(f"    Comparability: {item.comparability.value}", file=out)
    for reason in item.comparability_reasons:
        _wrapped(out, "- ", reason, indent=6)
    _print_passage(store, claim, out)


def _print_claim(store: Store, claim_id: str, out: TextIO, err: TextIO) -> int:
    claim = store.get_claim(claim_id)
    if claim is None:
        print(f"error: claim {claim_id} is not in the store", file=err)
        return 1
    work = store.get_work(claim.research_work_id)
    study = store.get_study(claim.study_id)
    print(f"Claim {claim.id} ({claim.claim_type.value})", file=out)
    if work is not None:
        print(f"Work: {work.title}", file=out)
        where = [work.venue, str(work.publication_date or "")]
        where += [f"{scheme} {value}" for scheme, value in work.external_identifiers.items()]
        print(f"  {', '.join(part for part in where if part)}", file=out)
    if study is not None:
        _wrapped(out, "Study: ", study.description)
    _wrapped(out, "Claim: ", claim.claim_text)
    print(f"Subject: {_term(claim.subject)}", file=out)
    outcome = "" if claim.outcome is None else f" | Outcome: {claim.outcome}"
    print(f"Predicate: {claim.predicate}{outcome}", file=out)
    context = claim.research_context.model_dump(
        exclude={"domain", "domain_attributes"}, exclude_none=True, exclude_defaults=True
    )
    parts = [f"domain {claim.research_context.domain.value}"]
    for key, value in context.items():
        shown = "; ".join(value) if isinstance(value, list | tuple) else value
        parts.append(f"{key.replace('_', ' ')} {shown}")
    _wrapped(out, "Context: ", ", ".join(parts))
    if claim.method is not None:
        print(f"Method: {_term(claim.method.name)}", file=out)
    if claim.comparator is not None:
        print(f"Baseline: {_term(claim.comparator.name)}", file=out)
    if claim.measurement is not None:
        unit = "" if claim.measurement.unit is None else f" ({claim.measurement.unit.original})"
        print(f"Metric: {_term(claim.measurement.name)}{unit}", file=out)
    result = claim.result
    parts = [result.direction.value]
    if result.value is not None:
        unit = "" if result.unit is None else f" {result.unit.original}"
        parts.append(f"value {result.value:g}{unit}")
    for label, value in (
        ("p", result.p_value),
        ("CI", result.confidence_interval),
        ("uncertainty", result.uncertainty),
    ):
        if value is not None:
            parts.append(f"{label} {value}")
    if result.statistical_significance is not None:
        parts.append("significant" if result.statistical_significance else "not significant")
    print(f"Result: {', '.join(parts)}", file=out)
    _print_passage(store, claim, out, indent=0)
    if claim.extraction_run_id is not None:
        run = store.get_extraction_run(claim.extraction_run_id)
        if run is not None:
            print(
                f"Extraction: run {run.id}, model {run.model_identifier},"
                f" prompt {run.prompt_version}, schema {run.schema_version}",
                file=out,
            )
    return 0


def _print_passage(store: Store, claim: EvidenceClaim, out: TextIO, indent: int = 4) -> None:
    span = claim.evidence_span
    section = store.get_section(span.section_id)
    where = span.section_id
    if section is not None:
        where = section.section_type.value
        if section.heading:
            where += f' "{section.heading}"'
    pad = " " * indent
    print(
        f"{pad}Passage: {where}, characters {span.start_offset} to {span.end_offset}",
        file=out,
    )
    _wrapped(out, "", f'"{span.source_text}"', indent=indent + 2)


def _term(term: Term) -> str:
    if term.canonical is None or term.canonical == term.original:
        return term.original
    return f"{term.original} (canonical: {term.canonical})"


def _wrapped(out: TextIO, label: str, text: str, indent: int = 0) -> None:
    pad = " " * indent
    print(
        textwrap.fill(
            text, WIDTH, initial_indent=pad + label, subsequent_indent=pad + " " * len(label)
        ),
        file=out,
    )


def _serve(db: str, gold: str | None, err: TextIO) -> int:
    try:
        import uvicorn
    except ImportError:
        print("uvicorn is not installed; install the dev extras to run the API", file=err)
        return 1
    from evidence_dossier.api import create_app

    uvicorn.run(create_app(db, gold_dir=gold), host="127.0.0.1", port=8000)
    return 0
