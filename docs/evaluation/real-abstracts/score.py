import json
from datetime import UTC, datetime
from pathlib import Path

from evidence_dossier.api.app import _search_hits
from evidence_dossier.evaluate import evaluate_store, load_dataset
from evidence_dossier.store import Store

R = Path(__file__).parent
ds = load_dataset(R / "gold", "dev")


def run_versions(store: Store) -> tuple[str, str, str]:
    """Return the model, prompt and schema version that the stored runs agree on."""
    found: tuple[set[str], set[str], set[str]] = (set(), set(), set())
    for document in ds.documents:
        for claim in store.list_claims(research_work_id=document.research_work_id):
            run = (
                store.get_extraction_run(claim.extraction_run_id)
                if claim.extraction_run_id
                else None
            )
            if run is not None:
                found[0].add(run.model_identifier)
                found[1].add(run.prompt_version)
                found[2].add(run.schema_version)
    return tuple(next(iter(v)) if len(v) == 1 else "mixed" for v in found)  # type: ignore[return-value]


with Store(str(R / "dossier.db")) as store:
    model_id, prompt_id, schema_id = run_versions(store)
    rep = evaluate_store(
        store,
        ds,
        model_identifier=model_id,
        prompt_version=prompt_id,
        schema_version=schema_id,
        now=datetime.now(UTC),
        search=_search_hits,
        notes=tuple(json.loads((R / "gold/notes.json").read_text())["notes"]),
    )
(R / "report.claims-v2.md").write_text(rep.to_markdown())
(R / "report.claims-v2.json").write_text(rep.model_dump_json(indent=1))
