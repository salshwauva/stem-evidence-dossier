# ADR 0004: Dev and test splits by a stable hash of the work group

## Status
Accepted, 2026-09-12

## Context
Plan section 49 keeps the development and held-out test sets separate and keeps related versions of a work together. Plan section 57 reports held-out results without reused development labels. Annotation adds works over time, so a split method that moves an existing work from test to dev when a new work arrives would leak test labels into prompt work. The plan names no split method.

## Decision
DatasetSplitter assigns each work by a SHA-256 hash of a salt and a group ID. The group is the connected component of the work under the WorkLink records that the caller passes, and its ID is the smallest work ID in the component. A work goes to dev when the hash, read as a fraction in [0, 1), is below the dev ratio, and to test otherwise. The default ratio is 0.7 and the default salt is "dossier-split-1".

The assignment of a work depends on its group only. A new work never moves an existing work. A new link can move a group when it joins two groups, and the smaller root wins. The salt is part of the split identity, so a report that names the salt names the split.

The Dataset model carries the split as a Literal, and a loader reads one directory per split or restricts one directory by the assignment. Gold labels live as JSON files under version control, not in the SQLite store, because the labels change through review and a diff must show each change.

## Consequences
Easier: the split is the same on every machine with no stored assignment table. A work keeps its side across releases, which a test pins for two known IDs.

Harder: the realized ratio drifts from the target on a small corpus, and it moves as works arrive. A change of salt or ratio is a new split, and old reports do not compare with new ones.

## Alternatives considered
- **A seeded random shuffle over the work list.** Rejected: the assignment of every work changes when one work joins or leaves the list.
- **A stored assignment table in the SQLite store.** Rejected: the split would live outside version control next to the labels it splits, and a second machine would need the same database.
- **Hash of the work ID with no grouping.** Rejected: a preprint and its journal article could land on different sides, which plan section 49 forbids.
