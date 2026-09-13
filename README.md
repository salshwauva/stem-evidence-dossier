# STEM Evidence Dossier

STEM Evidence Dossier turns research papers into claims that keep a link to the exact passage they came from. A query such as "retrieval-augmented generation reduces factual hallucination compared with the same model without retrieval" returns the stored claims grouped by stance: supports, contradicts, mixed, null, indirect, or insufficiently comparable. Each result carries the reason for its stance and the section and character offsets of its source text.

One `EvidenceClaim` model serves every domain. Biology, chemistry, and computer science have typed profiles. Physics, engineering, mathematics, and other STEM fields use the generic profile. Ingestion labels a work by its arXiv primary category or, for PubMed, by a narrow MeSH heading rule; the chemistry rules are a judgment call recorded in ADR 0010.

## What the code does

- Ingests papers from PubMed and arXiv, splits them into sections, and stores each text version with a content hash. PMC full text is accepted only under a CC BY or CC0 license. Tested on invented fixtures only; see Status.
- Extracts claims from a source document through a provider interface, validates the output against the schema and the source text, and stores invalid output next to its errors instead of dropping it.
- Normalizes names and units while it keeps the original wording.
- Parses a research proposition with a table of relationship verbs and comparator words, retrieves candidate claims with SQLite FTS5, checks comparability on seven dimensions, and assigns a stance with a written reason. A versioned measurement polarity table decides whether an improvement supports or contradicts a proposition, and an unknown measurement gives an indirect stance instead of a guess.
- Scores extraction fields, study relationships, evidence spans, retrieval, comparability, and stance against gold labels, and renders one report. The API serves it at GET /evaluation when a gold directory is configured.
- Exposes the search, dossier, claim, and work routes over FastAPI.

## Evidence checks

An evidence span names a section and a range of Unicode character offsets. The text at those offsets must equal the stored source passage, and the store rejects a claim whose study or section belongs to another research work.

These checks establish where a passage is. They do not establish that a scientific claim is true. A stance is a rule result with a reason, not a probability.

## Status

The core path exists: ingest, extract, normalize, query, evaluate, and the API. `pytest -q` prints the current test count. The parts that remain from the plan are the conflict pairs and evidence gap dimensions of the advanced dossier, a license column on stored documents, and unit value conversion.

Every test runs on recorded fixtures with invented papers and identifiers outside the real ranges. The PubMed and arXiv adapters have parsed only that invented XML, not a real API response, so real JATS markup with nested sections, inline tags, tables and footnotes is untested. No extraction precision or recall on a real corpus is available yet, and no live provider call runs in CI. The scores in the checked in evaluation report come from 4 hand written documents and 7 gold claims, scored against predictions edited by hand from that same gold; that fixture checks the report arithmetic and measures nothing about the pipeline.

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

## Query parsing

The parser turns query text into a typed proposition with a fixed table of rules and no model call. It matches one relationship verb, takes the subject from the words in front of it, and takes the measurement and the comparator from the words after it. The table holds the increase, reduce, improve, worsen, no change and outperform families, and it reads a negation in front of a verb, so "does not reduce" never parses as "reduces". The parser does not understand the sentence. A verb the table does not hold gives the relationship "unknown", and the stance classifier then answers indirect instead of guessing a direction. Every rule that fires lands in `parse_notes`, which the API returns next to the proposition.

A benchmark measures how far the rules reach. It holds 30 propositions across computer science, biology, and the physical and engineering domains. Every proposition and every label is hand written. No model wrote one, and no model scored one.

```sh
.venv/bin/python -m tests.query_parse_benchmark
```

```text
query parse benchmark: 30 hand written propositions
resolved    20
partial      6
unresolved   4
```

A case is resolved when the subject, the relationship, the measurement and the comparator all match the label. It is partial when some of them match, and unresolved when none of the labeled fields match. The 10 cases the rules do not resolve fall in three groups: a verb outside the table ("extends", "suppresses", "is associated with"), a question that states no relationship ("what is the effect of X on Y"), and a sentence that does not put the subject in front of the verb, such as a passive question, a noun phrase, or a modal such as "may". The command names every case it does not resolve. ADR 0012 records the decision.

`ModelQueryParser` in `src/evidence_dossier/query/model_parser.py` is an optional second path. It takes a callable that maps a prompt to text, so the repository holds no key and `query` imports no provider. The query goes into the prompt between delimiters as untrusted data, and the reply must validate into the proposition fields. A provider error, a reply that is not one JSON object, a missing field or an unknown direction falls back to the rules, and `parse_notes` records which path answered.

That parser is off by default. Search and the API call the rules, and nothing in the package constructs the model path. It has never run against a real model in this repository, so no number above comes from a model parse. The tests drive it with a fake callable, which checks the fallback and the validation and says nothing about a real reply.

## Extraction providers

`extract_document` takes an `ExtractionProvider`. `RecordedProvider` replays stored responses and is what the tests use. `ClaudeCliProvider` runs the `claude` command line tool as a subprocess, so the repository holds no API key. The command line grants no tool, denies the file, shell, web and agent tools by name, loads no user settings and no MCP server, and runs in an empty directory. Those flags are pinned by a unit test on the argument list and have never run against the live command line tool. Each run records the model identifier, the prompt version, and the schema version.

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

Every file under `tests/fixtures/` is invented. The fixture names copy the shape of the live API paths so the recorded client can key on them, and none of them is a recording of a real response.

The [architecture](docs/architecture.md) defines module boundaries. The [implementation plan](docs/design/implementation-plan.md) is the design source. The [annotation guidelines](docs/annotation-guidelines.md) define the gold labels.
