"""Candidate retrieval: structured filters plus FTS5 over the proposition terms (plan sections 35 and 36).

Retrieval finds candidates. It assigns no stance, and the stance classifier
never changes the candidate list.
"""

from evidence_dossier.model import Domain, EvidenceClaim, FrozenModel, QueryProposition, SourceLevel
from evidence_dossier.query.text import tokens
from evidence_dossier.store import Store


class Candidate(FrozenModel):
    """One retrieved claim with its bm25 rank and the query terms its text holds."""

    claim: EvidenceClaim
    # bm25 score from FTS5. A lower value is a better match.
    rank: float
    matched_terms: tuple[str, ...] = ()


def query_terms(proposition: QueryProposition) -> tuple[str, ...]:
    """Return the search terms of a proposition: subject, measurement and comparator tokens."""
    return tokens(
        " ".join(
            filter(None, (proposition.subject, proposition.measurement, proposition.comparator))
        )
    )


def fts_match(terms: tuple[str, ...]) -> str:
    """Return an FTS5 expression that matches any of the terms. Each token is a quoted string."""
    return " OR ".join(f'"{term}"' for term in terms)


class Retriever:
    """Finds candidate claims for a proposition in a store."""

    def __init__(self, store: Store) -> None:
        self._store = store

    def retrieve(
        self,
        proposition: QueryProposition,
        *,
        source_level: SourceLevel | None = None,
        limit: int = 20,
    ) -> list[Candidate]:
        """Return up to limit candidates, best rank first.

        The domain and the source level filter on real claim columns. The
        context filters (dataset, system, population) compare against the
        research context after the search, case insensitive.
        """
        terms = query_terms(proposition)
        if not terms:
            return []
        domain: Domain | None = proposition.domain
        hits = self._store.search_claims(
            fts_match(terms), domain=domain, source_level=source_level, limit=limit
        )
        candidates: list[Candidate] = []
        for claim, rank in hits:
            if not _context_matches(proposition, claim):
                continue
            held = set(tokens(_indexed_text(claim)))
            candidates.append(
                Candidate(
                    claim=claim,
                    rank=rank,
                    matched_terms=tuple(term for term in terms if term in held),
                )
            )
        return candidates


def _indexed_text(claim: EvidenceClaim) -> str:
    """Return the same text that the claims_fts index holds for a claim."""
    parts = (
        claim.claim_text,
        claim.normalized_claim,
        claim.subject.original,
        claim.subject.canonical,
        claim.outcome,
        claim.predicate,
        claim.evidence_span.source_text,
    )
    return " ".join(part for part in parts if part)


def _context_matches(proposition: QueryProposition, claim: EvidenceClaim) -> bool:
    context = claim.research_context
    pairs = (
        (proposition.dataset, context.dataset),
        (proposition.system, context.system),
        (proposition.population, context.population),
    )
    return all(
        wanted is None or (actual is not None and wanted.lower() == actual.lower())
        for wanted, actual in pairs
    )
