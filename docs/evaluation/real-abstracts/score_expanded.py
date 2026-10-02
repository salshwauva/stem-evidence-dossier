"""Score the 8 abstract store with AI query expansion. A recorded run replays from expansions.json."""

import json
from datetime import UTC, datetime
from pathlib import Path

from evidence_dossier.evaluate import SearchHit, evaluate_store, load_dataset
from evidence_dossier.extract import ClaudeCliProvider
from evidence_dossier.query import ModelQueryExpander, search_evidence
from evidence_dossier.store import Store

R = Path(__file__).parent
MODEL = "claude-sonnet-5-5"
RECORDED = R / "expansions.json"
ds = load_dataset(R / "gold", "dev")

recorded: dict[str, str] = json.loads(RECORDED.read_text()) if RECORDED.exists() else {}
live = ClaudeCliProvider(MODEL)


def model(prompt: str) -> str:
    if prompt in recorded:
        return recorded[prompt]
    reply = live.complete(prompt).text
    recorded[prompt] = reply
    RECORDED.write_text(json.dumps(recorded, indent=1))
    return reply


expander = ModelQueryExpander(model)


def search(store: Store, text: str) -> list[SearchHit]:
    results = search_evidence(store, text, limit=100, expander=expander)
    items = {i.claim.id: i for g in results.groups for i in g.items}
    return [
        SearchHit(
            claim_id=i.claim.id,
            stance=i.stance,
            comparability=i.comparability,
            reason=i.stance_reason,
        )
        for c in results.candidates
        if (i := items.get(c.claim.id))
    ]


with Store(str(R / "dossier.db")) as store:
    rep = evaluate_store(
        store,
        ds,
        model_identifier=MODEL,
        prompt_version="v1",
        schema_version="v1",
        now=datetime.now(UTC),
        search=search,
        notes=tuple(json.loads((R / "gold/notes.json").read_text())["notes"])
        + ("Search ran with AI query expansion, prompt query-expand-v1.",),
    )
(R / "report.expanded.md").write_text(rep.to_markdown())
print("ok")
