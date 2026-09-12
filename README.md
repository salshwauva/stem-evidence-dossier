# STEM Evidence Dossier

STEM Evidence Dossier turns research papers into claims that keep a link to the exact passage they came from. A query such as "retrieval-augmented generation reduces factual hallucination compared with the same model without retrieval" returns the stored claims grouped by stance: supports, contradicts, mixed, null, indirect, or insufficiently comparable. Each result carries the reason for its stance and the section and character offsets of its source text.

One `EvidenceClaim` model serves every domain. Biology, chemistry, and computer science have typed profiles. Physics, engineering, mathematics, and other STEM fields use the generic profile.

## What the code does

- Ingests papers from PubMed (with PMC full text where it exists) and arXiv, splits them into sections, and stores each text version with a content hash.
- Extracts claims from a source document through a provider interface, validates the output against the schema and the source text, and stores invalid output next to its errors instead of dropping it.
- Normalizes names and units while it keeps the original wording.
- Parses a research proposition, retrieves candidate claims with SQLite FTS5, checks comparability on seven dimensions, and assigns a stance with a written reason.
- Scores extraction fields, study relationships, evidence spans, retrieval, comparability, and stance against gold labels, and renders one report.
- Exposes the search, dossier, claim, and work routes over FastAPI.

## Evidence checks

An evidence span names a section and a range of Unicode character offsets. The text at those offsets must equal the stored source passage, and the store rejects a claim whose study or section belongs to another research work.

These checks establish where a passage is. They do not establish that a scientific claim is true. A stance is a rule result with a reason, not a probability.

## Status

The core path exists: ingest, extract, normalize, query, and evaluate, with 233 automated tests. The parts that remain from the plan are the conflict pairs and evidence gap dimensions of the advanced dossier, a live evaluation route, and unit value conversion.

Every test runs on recorded fixtures with invented papers. No extraction precision or recall on a real corpus is available yet, and no live provider call runs in CI.

## Setup

The project requires Python 3.13 or later.

```sh
git clone https://github.com/salshwauva/stem-evidence-dossier.git
cd stem-evidence-dossier
python3.13 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

## Run a query

The API serves an existing SQLite database:

```sh
.venv/bin/python -m evidence_dossier.api path/to/dossier.db
```

Interactive documentation is at `http://127.0.0.1:8000/docs`. A search request is one JSON body:

```json
{"text": "retrieval-augmented generation reduces factual hallucination compared with the same model without retrieval"}
```

The same pipeline is available from Python:

```python
from evidence_dossier.query import search_evidence
from evidence_dossier.store import Store

with Store("dossier.db") as store:
    results = search_evidence(
        store, "MAPT knockdown increases neuronal survival compared with a scrambled control"
    )
    for group in results.groups:
        for item in group.items:
            print(group.stance, item.comparability, item.provenance.source_text)
```

## Extraction providers

`extract_document` takes an `ExtractionProvider`. `RecordedProvider` replays stored responses and is what the tests use. `ClaudeCliProvider` runs the `claude` command line tool as a subprocess, so the repository holds no API key. Each run records the model identifier, the prompt version, and the schema version.

Paper text is untrusted input. The prompt wraps every section as data, and the validator rejects any response that leaves the schema. The adversarial fixtures are regression tests, not proof that injection cannot happen.

## Tests and checks

```sh
.venv/bin/pytest -q
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy --strict src tests
.venv/bin/pip-audit
```

## Source map

| Path | Purpose |
| --- | --- |
| `src/evidence_dossier/model/` | Validated records, evidence spans, query records |
| `src/evidence_dossier/profiles/` | Biology, chemistry, computer science, and generic profiles |
| `src/evidence_dossier/store/` | SQLite store, FTS5 index, and migrations |
| `src/evidence_dossier/ingest/` | PubMed and arXiv adapters, section parser |
| `src/evidence_dossier/extract/` | Prompt, providers, validation, extraction pipeline |
| `src/evidence_dossier/normalize/` | Canonical names and units |
| `src/evidence_dossier/query/` | Parser, retrieval, comparability, stance, search |
| `src/evidence_dossier/evaluate/` | Gold labels, splits, scoring, report |
| `src/evidence_dossier/api/` | FastAPI routes |
| `tests/` | Recorded fixtures and automated checks |
| `docs/` | Architecture, decisions, annotation guidelines, implementation plan |

The [architecture](docs/architecture.md) defines module boundaries. The [implementation plan](docs/design/implementation-plan.md) is the design source. The [annotation guidelines](docs/annotation-guidelines.md) define the gold labels.
