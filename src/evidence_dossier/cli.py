"""The evidence-dossier command: ingest, extract, search, claim, serve and demo (plan section 58).

The command composes the pipeline, so it imports the other subpackages and no
subpackage imports it, the same exception that api holds. run() takes the
HTTP client and the extraction provider as arguments, so tests pass recorded
ones and no test opens a network connection. The demo command rebuilds a
store from recorded replies, so it needs no network and no key.
"""

import argparse
import sqlite3
import sys
import textwrap
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, TextIO

import httpx

from evidence_dossier.extract import (
    ClaudeCliProvider,
    ExtractionProvider,
    ProviderError,
    RecordedProvider,
    RecordingProvider,
    extract_document,
)
from evidence_dossier.ingest import (
    ArxivAdapter,
    HttpClient,
    HttpxClient,
    IngestResult,
    LiteratureSourceAdapter,
    PacedHttpClient,
    PubMedAdapter,
    RecordingHttpClient,
    ReplayHttpClient,
    ingest_work,
)
from evidence_dossier.ingest.http import INDEX_FILE
from evidence_dossier.model import Domain, EvidenceClaim, FrozenModel, Term
from evidence_dossier.normalize import normalize_claim
from evidence_dossier.query import EvidenceItem, EvidenceResults, search_evidence
from evidence_dossier.store import Store

DEFAULT_DB = "dossier.db"
# Seconds between two requests. The arXiv API asks for three. NCBI allows three
# requests a second without an API key.
ARXIV_INTERVAL = 3.0
NCBI_INTERVAL = 0.34
WIDTH = 88

type Source = Literal["arxiv", "pubmed"]


class DemoWork(FrozenModel):
    source: Source
    identifier: str


class DemoCorpus(FrozenModel):
    """The demo/corpus.json file: the works of the demo store and the queries it answers."""

    note: str
    works: tuple[DemoWork, ...]
    queries: tuple[str, ...]


def main(argv: Sequence[str] | None = None) -> int:
    return run(sys.argv[1:] if argv is None else argv)


def run(
    argv: Sequence[str],
    *,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
    http: HttpClient | None = None,
    provider: ExtractionProvider | None = None,
) -> int:
    """Run one command and return its exit status.

    Without an http client, each source gets a live client paced to its rate
    limit. Without a provider, extract runs the claude command line tool.
    """
    args = _parser().parse_args(argv)
    if args.command == "serve":
        return _serve(args.db, args.gold, err)
    try:
        if args.command == "demo":
            return _demo(
                args.db,
                Path(args.demo_dir),
                args.record,
                args.model,
                tuple(args.only),
                out,
                err,
                http,
                provider,
            )
        with Store(args.db) as store:
            if args.command == "ingest":
                return _ingest(store, args.source, args.identifiers, http, out)
            if args.command == "extract":
                chosen = provider or ClaudeCliProvider(args.model)
                summary = _extract(store, args.document_ids, chosen, out)
                return 1 if summary.invalid or summary.failed else 0
            if args.command == "search":
                domain = None if args.domain is None else Domain(args.domain)
                results = search_evidence(store, args.text, domain=domain, limit=args.limit)
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

    claim = commands.add_parser("claim", help="show one claim with its context and passage")
    claim.add_argument("claim_id")

    serve = commands.add_parser("serve", help="serve the API on http://127.0.0.1:8000")
    serve.add_argument("--gold", help="gold directory for GET /evaluation")

    demo = commands.add_parser("demo", help="build a new store from the recorded demo corpus")
    demo.add_argument("--demo-dir", default="demo", help="folder with corpus.json (default demo)")
    demo.add_argument(
        "--record", action="store_true", help="fetch and extract live, and save every reply"
    )
    demo.add_argument("--model", help="model for the claude command line tool, with --record")
    demo.add_argument(
        "--only",
        action="append",
        default=[],
        metavar="SOURCE:ID",
        help="with --record, record only this corpus entry (such as arxiv:2310.11511)"
        " and keep the other recordings; repeat to name more entries",
    )
    return parser


def _live_client(source: str) -> HttpClient:
    interval = ARXIV_INTERVAL if source == "arxiv" else NCBI_INTERVAL
    return PacedHttpClient(HttpxClient(), interval)


def _adapter(source: str, http: HttpClient | None) -> LiteratureSourceAdapter:
    client = http or _live_client(source)
    return ArxivAdapter(client) if source == "arxiv" else PubMedAdapter(client)


def _ingest(
    store: Store,
    source: str,
    identifiers: Sequence[str],
    http: HttpClient | None,
    out: TextIO,
) -> int:
    adapter = _adapter(source, http)
    for identifier in identifiers:
        _ingest_one(store, adapter, source, identifier, out)
    return 0


def _ingest_one(
    store: Store, adapter: LiteratureSourceAdapter, source: str, identifier: str, out: TextIO
) -> IngestResult:
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
    return result


class ExtractSummary(FrozenModel):
    """How the documents of one extract call ended."""

    invalid: int = 0
    # Documents with no reply or no stored run: a provider error, a missing
    # document, or IDs that an earlier extraction holds.
    failed: int = 0


def _extract(
    store: Store, document_ids: Sequence[str], provider: ExtractionProvider, out: TextIO
) -> ExtractSummary:
    """Extract each document in turn. A document that fails prints its reason and the loop goes on."""
    invalid = failed = 0
    for document_id in document_ids:
        try:
            run = extract_document(
                store, document_id, provider, normalizer=normalize_claim, now=datetime.now(UTC)
            )
        except sqlite3.IntegrityError as error:
            print(f"{document_id}: nothing stored, an earlier extraction holds its IDs", file=out)
            print(f"  {error}", file=out)
            failed += 1
            continue
        except (ProviderError, LookupError) as error:
            print(f"{document_id}: nothing stored, no reply: {error}", file=out)
            failed += 1
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
            invalid += 1
    return ExtractSummary(invalid=invalid, failed=failed)


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


def _demo(
    db: str,
    folder: Path,
    record: bool,
    model: str | None,
    only: tuple[str, ...],
    out: TextIO,
    err: TextIO,
    http: HttpClient | None,
    provider: ExtractionProvider | None,
) -> int:
    """Build a new store from demo/corpus.json, extract every document, and run the queries.

    Replay reads demo/http and demo/replies and opens no network connection.
    Record fetches and extracts live, saves every reply there, and writes
    demo/SOURCES.md with the title, authors and license of each work. Record
    with --only runs live for the named entries and replays the rest, so one
    failed paper does not cost a full recording.
    """
    corpus_path = folder / "corpus.json"
    if not corpus_path.is_file():
        print(f"error: {corpus_path} is missing; run from the repository root", file=err)
        return 1
    if only and not record:
        print("error: --only needs --record", file=err)
        return 1
    if Path(db).exists():
        print(f"error: {db} exists; the demo builds a new store, so pass another --db", file=err)
        return 1
    corpus = DemoCorpus.model_validate_json(corpus_path.read_text(encoding="utf-8"))
    http_dir, replies_dir = folder / "http", folder / "replies"
    entries = [_entry(work) for work in corpus.works]
    live = set(only) if only else set(entries)
    if record:
        if model is None:
            print("error: --record needs --model", file=err)
            return 1
        unknown = sorted(live - set(entries))
        if unknown:
            print(
                f"error: --only: no corpus entry {', '.join(unknown)}; entries: {', '.join(entries)}",
                file=err,
            )
            return 1
        recordings = any(path.exists() and any(path.iterdir()) for path in (http_dir, replies_dir))
        if only and not ((http_dir / INDEX_FILE).is_file() and replies_dir.is_dir()):
            print(f"error: --only needs earlier recordings in {folder}", file=err)
            return 1
        if recordings and not only:
            print(
                f"error: {folder} holds recordings; delete http and replies to record again,"
                " or pass --only to record single entries",
                file=err,
            )
            return 1
    replay = ReplayHttpClient(http_dir)
    recorded = RecordedProvider(fixture_dir=replies_dir)
    recording_provider = (
        RecordingProvider(provider or ClaudeCliProvider(model), replies_dir)
        if record and model is not None
        else None
    )

    def client_for(work: DemoWork) -> HttpClient:
        if record and _entry(work) in live:
            return RecordingHttpClient(http or _live_client(work.source), http_dir)
        return replay

    def provider_for(work: DemoWork) -> ExtractionProvider:
        return recording_provider if recording_provider and _entry(work) in live else recorded

    with Store(db) as store:
        results = [
            _ingest_one(
                store, _adapter(work.source, client_for(work)), work.source, work.identifier, out
            )
            for work in corpus.works
        ]
        if record:
            _write_sources(store, corpus, results, folder / "SOURCES.md")
        print(file=out)
        summary = ExtractSummary()
        for work, result in zip(corpus.works, results, strict=True):
            part = _extract(store, [result.document_id], provider_for(work), out)
            summary = ExtractSummary(
                invalid=summary.invalid + part.invalid, failed=summary.failed + part.failed
            )
        first_claim: str | None = None
        for text in corpus.queries:
            print(file=out)
            found = search_evidence(store, text)
            _print_results(store, found, out)
            if first_claim is None:
                first_claim = next(
                    (group.items[0].claim.id for group in found.groups if group.items), None
                )
    if first_claim is not None:
        print(f"\nOpen one claim: evidence-dossier --db {db} claim {first_claim}", file=out)
    if summary.failed:
        documents = "document" if summary.failed == 1 else "documents"
        if record:
            print(
                f"error: {summary.failed} {documents} got no reply. A failed recording keeps its"
                " earlier reply. If the prompt, the schema or the section parser changed since"
                " the last full recording, delete demo/http and demo/replies, then run"
                " demo --record without --only.",
                file=err,
            )
            return 1
        print(
            f"error: {summary.failed} {documents} had no recorded reply. The prompt, the schema"
            " or the section parser changed since the recording, so the recorded replies no"
            " longer match. Delete demo/http and demo/replies, then run demo --record.",
            file=err,
        )
        return 1
    return 0


def _entry(work: DemoWork) -> str:
    """Return the name of a corpus entry as --only takes it, such as arxiv:2310.11511."""
    return f"{work.source}:{work.identifier}"


def _write_sources(
    store: Store, corpus: DemoCorpus, results: Sequence[IngestResult], path: Path
) -> None:
    lines = [
        "# Sources",
        "",
        "The demo store holds these works. `evidence-dossier demo --record` writes this file.",
        "arXiv metadata, the abstracts included, is CC0. PMC full text is stored only under",
        "CC BY or CC0, and the store splits it into sections.",
        "",
        "| Work | Authors | Identifier | Text | License |",
        "| --- | --- | --- | --- | --- |",
    ]
    for demo_work, result in zip(corpus.works, results, strict=True):
        work = store.get_work(result.work_id)
        if work is None:
            continue
        names = [author.name for author in work.authors]
        authors = ", ".join(names[:3]) + (" et al." if len(names) > 3 else "")
        identifier = f"{demo_work.source} {demo_work.identifier}"
        if work.doi:
            identifier += f", doi {work.doi}"
        license_name = result.license or ("CC0" if demo_work.source == "arxiv" else "not reported")
        lines.append(
            f"| {work.title} | {authors} | {identifier} | {result.source_level.value} | {license_name} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _serve(db: str, gold: str | None, err: TextIO) -> int:
    try:
        import uvicorn
    except ImportError:
        print("uvicorn is not installed; install the dev extras to run the API", file=err)
        return 1
    from evidence_dossier.api import create_app

    uvicorn.run(create_app(db, gold_dir=gold), host="127.0.0.1", port=8000)
    return 0
