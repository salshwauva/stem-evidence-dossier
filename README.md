# STEM Evidence Dossier

STEM Evidence Dossier is a Python project for an auditable database of claims from STEM research papers. Each claim keeps a link to the exact passage it came from. A planned query layer will group the claims for a research question by stance, such as supports or contradicts.

The design lives in [docs/design/implementation-plan.md](docs/design/implementation-plan.md). The module boundaries and import rules live in [docs/architecture.md](docs/architecture.md), and the decision records live in [docs/decisions](docs/decisions).

## Status

The "schema and profiles" increment from plan section 53 is done:

- a domain-independent core model, where biology and computer science claims validate against the same `EvidenceClaim`
- biology and computer science profiles, with a generic profile for every other domain
- a SQLite store for the core records, with versioned SQL migrations

These increments are planned, and none of their code exists yet:

- corpus and source adapters
- extraction and normalization
- gold labels and evaluation
- query and stance, with the API

## Setup

The project needs Python 3.13.

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

## Tests and checks

```sh
.venv/bin/pytest -q
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy --strict src tests
.venv/bin/pip-audit
```

CI in `.github/workflows/ci.yml` runs the same checks, plus a gitleaks secret scan.
