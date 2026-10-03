<!-- TODO(mvp 2.4, 3.2, 3.3): Do not publish this file before the live recording exists.
Quick start needs demo/http, demo/replies and demo/SOURCES.md, which `evidence-dossier demo --record` writes. Until then the demo command exits with "no recorded reply".
After the recording:
1. Paste a trimmed demo output into the Quick start section.
2. Add the measured demo corpus numbers to Status.
3. Revisit "No profile has run on a real paper" (Domain profiles) and "No live extraction has run yet" (Extraction providers). -->

# STEM Evidence Dossier

Checking a hypothesis against the literature means reading each paper to find what it claims and where the text says so. STEM Evidence Dossier stores those claims with a link to the exact passage each one came from. A query such as "retrieval augmentation reduces factual hallucination compared with the same model without retrieval" returns the stored claims grouped by stance (supports, contradicts, mixed, null, indirect, or insufficiently comparable), each with the reason for its stance and the character offsets of its source text.

## Quick start

Python 3.13 or later is required. The demo command builds a new store from eight real works (five arXiv abstracts and three PubMed papers), runs two queries, and prints the results. It replays recorded responses, so it needs no network and no key.

```sh
git clone https://github.com/salshwauva/stem-evidence-dossier.git && cd stem-evidence-dossier
python3.13 -m venv .venv && .venv/bin/python -m pip install -e ".[dev]"
.venv/bin/evidence-dossier --db demo.db demo
```

<!-- TODO(mvp 2.4): paste the real output here, trimmed to one query, one stance group and one claim opened to its passage. -->

The output ends with the command that opens one claim down to its exact passage. The printed command starts with `evidence-dossier`, so prefix it with `.venv/bin/` when the environment is not active. The titles, authors and licenses of the eight works are in [demo/SOURCES.md](demo/SOURCES.md). The [use cases](docs/use-cases.md) list what else the commands do.

## What it does

- Ingests works from PubMed and arXiv and splits them into sections. PMC full text is kept only under a CC BY or CC0 license, and every other work falls back to its abstract.
- Extracts claims with a model through the `claude` command line tool. Each claim points to an exact passage, names and units get a canonical form next to the original wording, and a reply that fails validation is stored with its errors.
- Searches a proposition and groups the claims by stance, with a comparability level and a written reason for each.
- Opens any claim down to its source passage and to the extraction run that produced it.
- Scores extraction, retrieval, comparability and stance against gold labels.
- Serves search, dossier snapshots, claims, works and evaluation over FastAPI.

## Status

Experimental. The core path exists: ingest, extract, normalize, query, evaluate, the API and the command line. `pytest -q` prints the current test count. The parts that remain from the plan are the conflict pairs and evidence gap dimensions of the advanced dossier, a license column on stored documents, and unit value conversion.

The PubMed and arXiv adapters have run against the live services on real works, and PMC full text under CC BY has gone through the section parser. No extraction has run on a real paper, so no precision, recall or stance result on real data exists yet. No live provider call runs in CI.

<!-- TODO(mvp 2.4, 3.3): after the live recording, add the measured numbers of the demo corpus here: works ingested, documents by source level, valid and invalid runs, claims stored. Numbers from the demo corpus only. -->

Every automated test runs on recorded fixtures with invented papers and identifiers outside the real ranges. The scores in the checked in evaluation report come from 4 invented documents and 7 gold claims, scored against predictions made from that same gold with deliberate errors. That fixture checks the report arithmetic and measures nothing about the pipeline.

## Usage

### Command line

The `evidence-dossier` command runs the whole pipeline. The option `--db` names the SQLite store, goes before the command, and defaults to `dossier.db`.

```sh
.venv/bin/evidence-dossier --db dossier.db ingest arxiv 2005.11401
.venv/bin/evidence-dossier --db dossier.db extract --model sonnet work_8fc39e0ec1b6db48_v1
.venv/bin/evidence-dossier --db dossier.db search "retrieval augmentation reduces factual hallucination compared with the same model without retrieval"
.venv/bin/evidence-dossier --db dossier.db claim work_8fc39e0ec1b6db48_v1_c1
```

`ingest` prints the document ID that `extract` takes, and `search` prints the claim IDs that `claim` takes.

| Command | Purpose |
| --- | --- |
| `ingest` | Fetch works from `arxiv` or `pubmed` by identifier and store their best text |
| `extract` | Extract the claims of stored documents with the `claude` command line tool. `--model` is required, and the tool must be installed and logged in |
| `search` | Group the claims that bear on a proposition by stance. `--domain` and `--limit` narrow the search |
| `claim` | Show one claim with its context, its passage and its extraction run |
| `serve` | Serve the API on `http://127.0.0.1:8000`. `--gold` names the gold directory for `GET /evaluation` |
| `demo` | Build a new store from the recorded demo corpus. `--record --model` fetches and extracts live and records every reply. `--only SOURCE:ID` records single entries again |

### API

```sh
.venv/bin/evidence-dossier --db dossier.db serve
```

Interactive documentation is at `http://127.0.0.1:8000/docs`. The command `.venv/bin/python -m evidence_dossier.api path/to/dossier.db` starts the same app. A search request is one JSON body:

```json
{"text": "retrieval augmentation reduces factual hallucination compared with the same model without retrieval"}
```

| Route | Purpose |
| --- | --- |
| `POST /search/evidence` | Claims grouped by stance for a proposition. Optional fields: `domain`, `source_level`, `dataset`, `system`, `population`, `limit` |
| `POST /dossiers` | A search that also stores a snapshot with the counts by stance and the corpus scope |
| `GET /dossiers/{dossier_id}` | A stored snapshot with its proposition and stance assessments |
| `GET /claims/{claim_id}` | One claim |
| `GET /works/{work_id}` | A work with its links and the IDs of its claims |
| `GET /conflicts` | An empty list with a note, until the advanced dossier exists |
| `GET /evaluation` | Scores against the gold directory that `serve --gold` names. Answers 404 without one |

### Python

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

## How it works

Two paths share one SQLite file. The build path ingests a work, extracts its claims through a model, and normalizes the names and units. The ask path parses a proposition with a table of relationship verbs and comparator words, retrieves candidate claims with SQLite FTS5, checks comparability on seven dimensions, and assigns a stance with a written reason. A versioned measurement polarity table decides whether an improvement supports or contradicts a proposition, and an unknown measurement gives an indirect stance. The package uses Pydantic for the records, SQLite with FTS5 for storage and search, FastAPI for the API, and httpx for the source clients.

The [architecture](docs/architecture.md) shows both paths as diagrams and lists the module boundaries. The [diagrams](docs/diagrams.md) hold the class diagrams.

Three decisions shape the design:

- **Claim level stance.** One paper can hold a claim that supports a proposition and another that does not bear on it, so the stance belongs to the claim. Each claim links to one study and one passage.
- **Rules with reasons.** Parsing, comparability and stance are rules, and each verdict comes with a sentence that gives its reason.
- **The model sits behind an interface.** Extraction goes through an `ExtractionProvider`, so the repository holds no key, and the tests and the demo run on recorded replies.

## Domain profiles

One `EvidenceClaim` model serves every domain. Biology, chemistry, computer science, physics, and engineering have typed profiles, and the extraction prompt names the expected entities and the attribute fields of whichever one the domain picks.

The comparability engine reads a profile's own fields through a feature table. Physics maps five of its six comparability features, and engineering seven of its eight; the unmapped name on each side is the measurement, which the engine assesses on its own dimension. Biology leaves target and endpoint unmapped, chemistry leaves reaction, and computer science leaves baseline and metric. A test pins that split for every profile.

Mathematics and the other STEM fields use the generic profile. Ingestion labels a work by its arXiv primary category or, for PubMed, by a narrow MeSH heading rule; the chemistry rules are a judgment call recorded in ADR 0010, and the physics and engineering field lists in ADR 0011. No profile has run on a real paper; see Status.

## Evidence checks

An evidence span names a section and a range of Unicode character offsets. The text at those offsets must equal the stored source passage, and the store rejects a claim whose study or section belongs to another research work.

These checks establish where a passage is. They do not establish that a scientific claim is true. A stance is a rule result with a reason, not a probability.

## Query parsing

The parser turns query text into a typed proposition with a fixed table of rules and no model call. It matches one relationship verb, takes the subject from the words in front of it, and takes the measurement and the comparator from the words after it. The table holds the increase, reduce, improve, worsen, no change and outperform families, and it reads a negation in front of a verb, so "does not reduce" never parses as "reduces". The parser does not understand the sentence. A verb the table does not hold gives the relationship "unknown", and the stance classifier then answers indirect. Every rule that fires lands in `parse_notes`, which the API returns next to the proposition.

A benchmark measures how far the rules reach. It holds 30 propositions across computer science, biology, and the physical and engineering domains, each with the subject, relationship, measurement and comparator that a correct parse yields. Every label was written before the parser ran on the text.

```sh
.venv/bin/python -m tests.query_parse_benchmark
```

```text
query parse benchmark: 30 labeled propositions
resolved    20
partial      6
unresolved   4
```

Read those counts with the provenance in mind. The author of the rules also wrote the propositions, the labels and the mix of phrasings, in the same pass that broadened the rules, so the benchmark carries the bias of the author of the code. Nothing in it comes from a real query log, and no second reader has checked the labels.

A case is resolved when the subject, the relationship, the measurement and the comparator all match the label. It is partial when some of them match, and unresolved when none of the labeled fields match. The 10 cases the rules do not resolve fall in three groups: a verb outside the table ("extends", "suppresses", "is associated with"), a question that states no relationship ("what is the effect of X on Y"), and a sentence that does not put the subject in front of the verb, such as a passive question, a noun phrase, or a modal such as "may". The command names every case it does not resolve. ADR 0012 records the decision.

`ModelQueryParser` in `src/evidence_dossier/query/model_parser.py` is an optional second path. It takes a callable that maps a prompt to text, so the repository holds no key and `query` imports no provider. The query goes into the prompt between delimiters as untrusted data, and the reply must validate into the proposition fields. A provider error, a reply that is not one JSON object, a missing field or an unknown direction falls back to the rules, and `parse_notes` records which path answered.

That parser is off by default. Search and the API call the rules, and nothing in the package constructs the model path. It has never run against a real model in this repository, so no number above comes from a model parse. The tests drive it with a fake callable, which checks the fallback and the validation and says nothing about a real reply.

## Extraction providers

`extract_document` takes an `ExtractionProvider`. `RecordedProvider` replays stored responses and is what the tests and the demo use. `RecordingProvider` wraps another provider and saves each reply in the folder that `RecordedProvider` reads. `ClaudeCliProvider` runs the `claude` command line tool as a subprocess, so the repository holds no API key. The flags ask the command line tool for no tools, deny the file, shell, web and agent tools by name, and turn off the user, project and local settings, the MCP servers and the session history. The command runs in an empty directory. A unit test pins those flags on the argument list. An opt in test sends one short prompt through the installed command line tool when `CLAUDE_CLI_LIVE=1` is set. No live extraction has run yet. Each run records the model identifier, the prompt version, and the schema version.

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
| `src/evidence_dossier/profiles/` | Biology, chemistry, computer science, physics, engineering, and generic profiles |
| `src/evidence_dossier/store/` | SQLite store, FTS5 index, and migrations |
| `src/evidence_dossier/ingest/` | PubMed and arXiv adapters, section parser, HTTP client with record and replay |
| `src/evidence_dossier/extract/` | Prompt, providers, validation, extraction pipeline |
| `src/evidence_dossier/normalize/` | Canonical names and units |
| `src/evidence_dossier/query/` | Parser, retrieval, comparability, stance, search |
| `src/evidence_dossier/evaluate/` | Gold labels, splits, scoring, report |
| `src/evidence_dossier/api/` | FastAPI routes |
| `src/evidence_dossier/cli.py` | The `evidence-dossier` command |
| `demo/` | The demo corpus, its recorded replies, and the sources table |
| `tests/` | Recorded fixtures and automated checks |
| `docs/` | Architecture, diagrams, use cases, decisions, annotation guidelines, implementation plan |

Every file under `tests/fixtures/` is invented. The fixture names copy the shape of the live API paths so the recorded client can key on them, and none of them is a recording of a real response. The files under `demo/http` and `demo/replies` are recordings of real responses and real model replies.

The [architecture](docs/architecture.md) defines the data flow and the module boundaries. The [diagrams](docs/diagrams.md) hold the class diagrams. The [use cases](docs/use-cases.md) list what each command does and what is not built. The [implementation plan](docs/design/implementation-plan.md) is the design source. The [annotation guidelines](docs/annotation-guidelines.md) define the gold labels. The decisions are in [docs/decisions](docs/decisions/).
