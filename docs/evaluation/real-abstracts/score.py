from datetime import UTC, datetime
from pathlib import Path
import json
from evidence_dossier.api.app import _search_hits
from evidence_dossier.evaluate import evaluate_store, load_dataset
from evidence_dossier.store import Store
R = Path(__file__).parent
ds = load_dataset(R / "gold", "dev")
with Store(str(R / "dossier.db")) as store:
    rep = evaluate_store(store, ds, model_identifier="claude-sonnet-5-5", prompt_version="v1", schema_version="v1",
                         now=datetime.now(UTC), search=_search_hits,
                         notes=tuple(json.loads((R / "gold/notes.json").read_text())["notes"]))
(R / "report.md").write_text(rep.to_markdown())
(R / "report.json").write_text(rep.model_dump_json(indent=1))
