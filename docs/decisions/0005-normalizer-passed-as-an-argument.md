# ADR 0005: The extraction pipeline takes the normalizer as an argument

## Status
Accepted, 2026-09-12

## Context
Plan section 31 places normalization after relationship validation in the extraction pipeline, and plan section 33 keeps normalization separate from extraction. The architecture allows each planned subpackage to import model, profiles and store, and never a sibling. extract_document must still hand every valid claim to normalization before the store accepts it. The plan does not say how the two subpackages meet.

## Decision
extract defines a Normalizer protocol in `src/evidence_dossier/extract/pipeline.py`: a callable that takes an EvidenceClaim and a DomainProfile and returns an EvidenceClaim. extract_document takes a normalizer as a keyword argument and calls it on each built claim before add_claim. normalize exposes normalize_claim, a pure function with that shape. The caller, such as a command or a test, imports both subpackages and passes normalize_claim in.

Neither subpackage imports the other. normalize imports model and profiles only. extract imports model, profiles and store only.

## Consequences
Easier: the import rule holds without a third subpackage. A test can pass an identity function and check extraction on its own. The evaluation branch can pass a different normalizer to measure its effect.

Harder: every caller of extract_document names the normalizer. There is no default, because a default would need the import that the rule forbids.

## Alternatives considered
- **extract imports normalize and calls normalize_claim directly.** Rejected: it breaks the import rule in the architecture.
- **A pipeline module outside both subpackages that chains them.** Rejected: it adds a subpackage for one function, and the store call would then live outside extract.
- **normalize registers itself with extract at import time.** Rejected: the result would depend on import order, the same reason ADR 0003 rejected a registry.
