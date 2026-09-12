# ADR 0010: Chemistry domain detection from arXiv categories and MeSH headings

## Status
Accepted, 2026-09-12

## Context
Plan section 28 gives each research work a domain, and the domain picks the extraction profile. The chemistry profile existed, but ingestion could never produce CHEMISTRY: every PubMed work was BIOLOGY, and the arXiv table mapped archives only. arXiv has no chemistry archive. A domain label spreads: it picks the profile, and the profile shapes comparability and stance, so a wrong label costs more than a missing one.

## Decision
Two narrow rules produce CHEMISTRY from ingestion.

arXiv: the primary category physics.chem-ph maps to CHEMISTRY. Chemical physics is a physics category in the arXiv taxonomy, so this mapping is a judgment call, not a fact about arXiv. The rule reads the primary category only. A paper cross listed to chem-ph keeps the domain of its primary category.

PubMed: a work takes CHEMISTRY when at least one MeSH descriptor is in a small chemistry set (Catalysis, Chemistry and its subheadings, Chemical Synthesis, Electrochemistry, Photochemistry, Chemistry Techniques, Synthetic) and no descriptor is in a small biology set (Animals, Humans, Mice, Rats, Cell Line, Cells, Cultured, Proteins, Genes, Gene Expression, Organisms, Biological Assay). Every other PubMed work stays BIOLOGY. The comparison folds case and surrounding whitespace.

## Consequences
Easier: a chemistry paper from either source reaches the chemistry profile and its typed attributes.

Harder: MeSH describes subject matter, not method. A chemistry paper indexed with a biology heading stays BIOLOGY and loses the chemistry attributes. A biology paper indexed only with chemistry headings takes CHEMISTRY and loses its organism and assay fields. The biology veto makes the second case rarer at the cost of the first. Both sets are data in `src/evidence_dossier/ingest/domains.py`, and a change to either is a change to this rule.

## Alternatives considered
- **Detect the domain from the journal title.** Rejected: journal names are free text and many journals span domains.
- **Detect the domain with a model call.** Rejected for now: plan section 28 keeps the generic schema authoritative, and a rule that a test can pin is easier to audit than a model judgment.
- **Map every physics.chem-ph paper, primary or cross listed.** Rejected: a cross listed paper has a primary category that already names its home.
