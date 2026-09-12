# STEM Evidence Dossier

STEM Evidence Dossier stores research claims with the exact source passages that support them. It provides a shared evidence model for biology and computer science, with a generic profile for other domains.

The project is the foundation for a literature extractor. The current version contains the data model, domain profiles, and SQLite store. Automated extraction is planned.

## What the code does

- Represents research works, source documents, studies, and evidence claims as validated Pydantic models.
- Records each claim's context, method, comparator, measurement, and reported result.
- Links a claim to a section and an exact text span, with character offsets.
- Checks source text and record relationships before the store accepts a claim.
- Applies versioned SQLite migrations and stores the core records.

Biology-specific fields live in a biology profile. Computer science fields live in a separate profile. Both use the same `EvidenceClaim` model.

## Evidence checks

An evidence span identifies a source section and a range of Unicode character offsets. The text at those offsets must equal the stored source passage.

The store rejects a claim if its study or source section belongs to another research work. These checks establish the passage's location. They do not establish that a scientific claim is true.

## Status

The core model, profiles, and store are implemented. The current version has no paper import command or extraction service.

The remaining plan covers corpus adapters, extraction and normalization, labeled evaluation, and a query API. Those parts do not exist in this version.

## Setup

The project requires Python 3.13 or later.

```sh
git clone https://github.com/salshwauva/stem-evidence-dossier.git
cd stem-evidence-dossier
python3.13 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

The package exposes Python models and a store. For example, an empty local database uses:

```python
from evidence_dossier.store import Store

with Store("evidence.sqlite3") as store:
    work = store.get_work("example-work")
    assert work is None
```

The store applies migrations when it opens. The [test factories](tests/factories.py) contain complete example records.

## Tests and checks

```sh
.venv/bin/pytest -q
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy --strict src tests
.venv/bin/pip-audit
```

The tests cover model validation, domain profiles, evidence spans, migrations, and store relationships. CI also checks for secrets.

## Source map

| Path | Purpose |
| --- | --- |
| `src/evidence_dossier/model/` | Validated records and evidence spans |
| `src/evidence_dossier/profiles/` | Biology, computer science, and generic profiles |
| `src/evidence_dossier/store/` | SQLite store and migrations |
| `tests/` | Example records and automated checks |
| `docs/` | Architecture, decisions, and implementation plan |

The [architecture](docs/architecture.md) defines module boundaries. The [implementation plan](docs/design/implementation-plan.md) describes the intended extractor and query system.
