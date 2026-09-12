"""An HttpClient that serves recorded fixtures, so no test opens a network connection."""

from collections.abc import Mapping
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "ingest"


def request_key(url: str, params: Mapping[str, str]) -> str:
    """Return the stable name of a request: the URL path and the parameters that pick a record."""
    path = url.split("://", 1)[-1].split("/", 1)[-1].strip("/")
    picked = {
        name: params[name]
        for name in ("db", "id", "ids", "id_list", "term", "search_query")
        if name in params
    }
    suffix = "&".join(f"{name}={value}" for name, value in picked.items())
    return f"{path}?{suffix}" if suffix else path


class RecordedHttpClient:
    """Maps a request key to a fixture file under tests/fixtures/ingest and records every call."""

    def __init__(self, recordings: Mapping[str, str]) -> None:
        self._recordings = dict(recordings)
        self.calls: list[str] = []

    def get(self, url: str, params: Mapping[str, str]) -> bytes:
        key = request_key(url, params)
        self.calls.append(key)
        if key not in self._recordings:
            raise KeyError(f"no recording for {key}; a live call is not allowed in tests")
        return (FIXTURES_DIR / self._recordings[key]).read_bytes()


PUBMED_RECORDINGS = {
    "entrez/eutils/esearch.fcgi?db=pubmed&term=MAPT knockdown": "pubmed_esearch.xml",
    "entrez/eutils/efetch.fcgi?db=pubmed&id=90001234": "pubmed_efetch_90001234.xml",
    "entrez/eutils/efetch.fcgi?db=pubmed&id=90001235": "pubmed_efetch_90001235.xml",
    "pmc/utils/idconv/v1.0?ids=90001234": "pmc_idconv_90001234.json",
    "entrez/eutils/efetch.fcgi?db=pubmed&id=90001236": "pubmed_efetch_90001236.xml",
    "entrez/eutils/efetch.fcgi?db=pubmed&id=90001237": "pubmed_efetch_90001237.xml",
    "pmc/utils/idconv/v1.0?ids=90001235": "pmc_idconv_90001235.json",
    "pmc/utils/idconv/v1.0?ids=90001236": "pmc_idconv_90001236.json",
    "pmc/utils/idconv/v1.0?ids=90001237": "pmc_idconv_90001237.json",
    "pmc/utils/oa/oa.fcgi?id=PMC99900001": "pmc_oa_PMC99900001.xml",
    "pmc/utils/oa/oa.fcgi?id=PMC99900002": "pmc_oa_PMC99900002.xml",
    "pmc/utils/oa/oa.fcgi?id=PMC99900003": "pmc_oa_PMC99900003.xml",
    "entrez/eutils/efetch.fcgi?db=pmc&id=PMC99900001": "pmc_efetch_PMC99900001.xml",
}

# The key of the PMC OA record of the accepted work. A license test points it at
# another fixture and keeps the rest of the recordings.
OA_KEY_PMC99900001 = "pmc/utils/oa/oa.fcgi?id=PMC99900001"

ARXIV_RECORDINGS = {
    "api/query?search_query=all:retrieval factual errors": "arxiv_search.xml",
    "api/query?id_list=9901.00001": "arxiv_entry_9901.00001.xml",
    "api/query?id_list=9999.99999": "arxiv_entry_missing.xml",
}
