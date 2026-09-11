# ADR 0001: Biomedical fields move from the generic core to BiologyAttributes

## Status
Accepted, 2026-09-11

## Context
Plan section 17 lists organism and cell_line on ResearchContext. Plan section 53 sets the exit condition for the schema increment: "both domains validate without biomedical fields in the generic core". A computer science claim has no organism, dose or assay. These fields do not belong on records that every domain shares.

## Decision
ResearchContext keeps only domain neutral fields: system, population, dataset, benchmark, material, environment, hardware, software, model, simulation and theoretical_assumptions. Eight biology fields move to BiologyAttributes: organism, cell_line, tissue, disease_model, intervention, dose, duration and assay. BiologyProfile holds BiologyAttributes as its attribute model.

BiologyAttributes and ComputerScienceAttributes live in `src/evidence_dossier/model/attributes.py`. The domain_attributes field on ResearchContext, Method and Comparator needs both classes when Python builds those models. If the classes lived in profiles, model would import profiles while profiles imports model. With the classes in model, model stays a leaf and the imports stay acyclic.

A test reads model_fields on every class under evidence_dossier.model. It takes the attribute classes from the members of the domain_attributes union, so it needs no hand-written exclusion list. No other class may declare one of the eight fields.

## Consequences
Easier: every domain validates against the same generic records. The biology fields sit in one class, and a test pins them there.

Harder: a biology claim keeps its organism one level down, in research_context.domain_attributes. A reader who follows section 17 does not find organism on ResearchContext. The biology field names still appear under the model package, in attributes.py, because the union needs the class there.

## Alternatives considered
- **Keep organism and cell_line on ResearchContext, as section 17 lists them.** Rejected: the schema then fails the section 53 exit condition.
- **Put the attribute classes in profiles and import them into model.** Rejected: model and profiles would import each other.
- **A fourth subpackage for the attribute classes.** Rejected: model would still import another subpackage, and the biology fields would sit outside both model and profiles.
- **An open base class in model, with a registry that profiles fill at import time.** Rejected: validation would depend on import order. ADR 0003 covers the union itself.
