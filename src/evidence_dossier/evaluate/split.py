"""Dev and test splits that keep related works together (plan section 49)."""

import hashlib
from collections.abc import Iterable

from evidence_dossier.evaluate.gold import Split
from evidence_dossier.model import WorkLink


class DatasetSplitter:
    """Assign works to dev or test by a stable hash, so a split does not move between runs.

    Works joined by a WorkLink form one group, and the group takes the side of
    its smallest work ID. A preprint and its journal article therefore never
    sit on different sides.
    """

    def __init__(self, dev_ratio: float = 0.7, salt: str = "dossier-split-1") -> None:
        if not 0.0 <= dev_ratio <= 1.0:
            raise ValueError("dev_ratio must lie in [0, 1]")
        self.dev_ratio = dev_ratio
        self.salt = salt

    def assign(self, work_ids: Iterable[str], links: Iterable[WorkLink] = ()) -> dict[str, Split]:
        """Return the side of every work ID. Links to works outside work_ids still join groups."""
        parent: dict[str, str] = {}

        def root(work_id: str) -> str:
            parent.setdefault(work_id, work_id)
            while parent[work_id] != work_id:
                parent[work_id] = parent[parent[work_id]]
                work_id = parent[work_id]
            return work_id

        for link in links:
            a, b = root(link.source_work_id), root(link.target_work_id)
            if a != b:
                parent[max(a, b)] = min(a, b)
        return {work_id: self._side(root(work_id)) for work_id in work_ids}

    def _side(self, group_id: str) -> Split:
        digest = hashlib.sha256(f"{self.salt}:{group_id}".encode()).digest()
        fraction = int.from_bytes(digest[:8], "big") / 2**64
        return "dev" if fraction < self.dev_ratio else "test"
