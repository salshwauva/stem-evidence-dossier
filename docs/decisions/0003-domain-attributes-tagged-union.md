# ADR 0003: Domain attributes as a closed tagged union

## Status
Accepted, 2026-09-11

## Context
Plan section 23 gives each domain profile its own attributes, and plan section 28 keeps the generic schema authoritative. The attributes attach to ResearchContext, Method and Comparator. Extractor output for every domain must validate against one EvidenceClaim model. An unknown attribute set must fail validation, because the plan stores invalid output and never drops it without a trace.

## Decision
DomainAttributes is a Pydantic discriminated union of BiologyAttributes and ComputerScienceAttributes. A `profile` field is the tag, with the values "biology" and "computer_science". The domain_attributes field on the three records accepts one member of the union or None. A payload with an unknown tag fails with the Pydantic error type union_tag_invalid.

The union is closed. A new domain adds its attribute class to `src/evidence_dossier/model/attributes.py` and to DomainAttributes. Its profile then names that class as its attribute model, and the AttributeModel alias in `src/evidence_dossier/profiles/base.py` gains the class. BiologyProfile and ComputerScienceProfile reference BiologyAttributes and ComputerScienceAttributes this way.

The tag names a profile. It does not have to match the domain of the context, so a MULTIDISCIPLINARY context can carry biology attributes.

## Consequences
Easier: mypy narrows domain_attributes with isinstance. Stored JSON carries its own tag, so the store needs no extra column to rebuild the right class.

Harder: each new profile edits model/attributes.py and profiles/base.py. One context, method or comparator carries the attributes of one profile at most.

## Alternatives considered
- **A free-form dict for domain attributes.** Rejected: it validates nothing, so extractor mistakes pass without a trace.
- **An open base class with a registry that profiles fill at import time.** Rejected: validation would depend on import order, and custom dispatch code would replace the Pydantic discriminator.
- **One optional field per domain on each record, such as `biology` and `computer_science`.** Rejected: the generic core would then name every domain.
