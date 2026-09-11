# STEM Evidence Dossier

## 1. Project Summary

### Working title

**STEM Evidence Dossier**

Alternative names:

- Research Evidence Dossier
- Evidence Atlas
- Research Evidence Engine

The architecture should not depend on the final product name.

---

# 2. Core Problem

Scientific and technical research is published as documents, but researchers usually need answers about **claims and evidence**, not documents.

A researcher investigating a question must manually determine:

- which papers actually address the question;
- what each paper claims;
- what methods were used;
- what systems, datasets, materials, populations, benchmarks, or models were studied;
- what metrics or endpoints were measured;
- which findings support the hypothesis;
- which findings contradict it;
- which results are null, mixed, or indirect;
- whether apparent replication comes from genuinely different research groups or nearly identical experimental setups;
- why apparently conflicting studies disagree;
- how diverse the evidence is;
- and which important forms of evidence have not been identified.

Traditional search systems primarily retrieve **papers**.

This system builds and queries a structured database of **provenance-linked research claims**.

---

# 3. Domain Scope

The system is designed for **STEM research**, including:

- biology;
- biotechnology;
- medicine and preclinical research;
- chemistry;
- materials science;
- physics;
- environmental science;
- earth science;
- engineering;
- computer science;
- machine learning;
- robotics;
- statistics;
- applied mathematics;
- and other technical research domains.

The system must not assume that every paper contains:

- a biological model;
- an intervention;
- a dose;
- a patient population;
- or even a physical experiment.

Those are domain-specific concepts.

Instead, the architecture uses:

> **domain-independent research claims + typed domain extensions**

---

# 4. Example STEM Queries

## Biology

> Does MAPT knockdown improve neuronal survival in FTD models?

## Chemistry

> Do nickel-based catalysts improve selectivity for electrochemical CO₂ reduction to carbon monoxide?

## Materials Science

> Does adding graphene improve the tensile strength of epoxy composites?

## Physics

> Does this class of metamaterial demonstrate negative refractive index at microwave frequencies?

## Machine Learning

> Does retrieval-augmented generation reduce factual hallucination compared with prompting the same base model without retrieval?

## Computer Systems

> Does eBPF-based packet processing provide better throughput than equivalent userspace networking approaches under high packet rates?

## Software Engineering

> Does static analysis reduce production defect rates in large software projects?

## Robotics

> Do vision-language-action models improve manipulation success on unseen objects compared with task-specific policies?

The same evidence-query interface should work across all of them.

---

# 5. Product Thesis

Transform STEM literature into an **auditable evidence database**.

The platform exposes two primary capabilities:

1. **Evidence Query**
2. **Evidence Dossier**

Both operate on the same underlying research claims.

---

# 6. Evidence Query

A researcher enters either:

- a question;
- a hypothesis;
- a statement;
- or another sufficiently specific research proposition.

Example:

> Retrieval-augmented generation reduces hallucination compared with prompting the same model without retrieval.

The system parses the statement into a structured proposition and retrieves relevant research claims.

Results are organized as:

- **Supports**
- **Contradicts**
- **Mixed / context-dependent**
- **Null / inconclusive**
- **Indirect**
- **Insufficiently comparable**

Classification occurs at the **claim level**, not the paper level.

A single paper can therefore contribute multiple claims with different relationships to the same query.

---

# 7. Example Evidence Query — Computer Science

## Query

> Retrieval-augmented generation reduces factual hallucination compared with prompting the same model without retrieval.

### Supports

**Study A**

- Method: RAG
- Baseline: same base model without retrieval
- Dataset: Dataset X
- Metric: factual error rate
- Result: lower factual-error rate with RAG
- Statistical analysis: reported
- Exact evidence passage
- Paper / DOI

### Contradicts

**Study B**

- Comparable RAG configuration
- Dataset: Dataset Y
- Metric: factuality score
- Result: no improvement
- Exact evidence passage

### Mixed / Context-Dependent

**Study C**

- improvement on factual questions;
- degradation on another task type;
- performance sensitive to retrieval quality.

### Indirect

**Study D**

- retrieval improved answer quality;
- factual hallucination itself was not directly measured.

---

# 8. Evidence Dossier

The Evidence Dossier aggregates claims around a research hypothesis.

Example:

> Retrieval-augmented generation reduces hallucination.

The dossier may include:

### Evidence Summary

```text
Relevant claims                 63
Supporting                      37
Contradictory                    8
Null                             9
Mixed                            6
Indirect                         3
```

### Research Diversity

```text
Distinct datasets               14
Distinct model families          9
Distinct evaluation metrics      7
Distinct research-group clusters 18
```

### Potential Conflicts

The dossier surfaces comparable studies that report incompatible outcomes.

### Evidence Gaps

For example:

```text
Independent replication             identified
Multiple benchmark families         identified
Large-model evaluation              identified
Open-source model evaluation        limited
Long-context evaluation             limited
Real-world deployment evidence      not identified
Longitudinal evaluation             not identified
```

### Methodological Context

For each result, the researcher can inspect:

- study design;
- data;
- system/model/material;
- method;
- comparator;
- measured metric;
- outcome;
- uncertainty/statistics;
- and exact source evidence.

---

# 9. Critical Design Principle

## `EvidenceClaim` is the central domain object.

A paper is merely a **source container**.

The system reasons over specific claims extracted from individual studies.

Example:

```text
Paper
│
├── Claim A:
│   method X improves accuracy
│
├── Claim B:
│   method X increases latency
│
└── Claim C:
    method X shows no significant
    memory-use difference
```

For the question:

> Does method X improve accuracy?

Claim A may support the hypothesis.

Claims B and C are not contradictory; they concern different metrics.

This is why whole-paper stance classification is prohibited.

---

# 10. Generalized Research Model

The original biomedical schema:

```text
intervention
biological model
dose
assay
outcome
```

is too narrow.

The generalized representation becomes:

```text
ResearchWork
    ↓
Study
    ↓
EvidenceClaim
    ↓
ResearchContext
Method
Comparator
Measurement
Result
EvidenceSpan
```

Domain-specific attributes extend these objects.

---

# 11. ResearchWork

Represents a publication or technical research artifact.

Fields:

```text
id
doi
title
abstract
publication_date
venue
authors
affiliations
external_identifiers
domain
```

Possible sources include:

- journal articles;
- conference proceedings;
- preprints;
- technical reports.

The first implementation should prioritize sources that provide reliable machine-readable metadata/full text.

---

# 12. SourceDocument

Represents the actual content available to the extractor.

```text
id
research_work_id
source_level
source_format
raw_text
fetched_at
```

Example source levels:

```text
FULL_TEXT
ABSTRACT_ONLY
METADATA_ONLY
```

---

# 13. Section

```text
id
document_id
section_type
heading
text
ordinal
```

Generic section types:

```text
ABSTRACT
INTRODUCTION
BACKGROUND
METHODS
EXPERIMENT
RESULTS
EVALUATION
DISCUSSION
CONCLUSION
APPENDIX
FIGURE_CAPTION
TABLE
OTHER
```

Domain profiles may map different headings onto these categories.

For example:

```text
Experimental Setup → METHODS
Evaluation         → EVALUATION
Benchmarks         → EVALUATION
```

---

# 14. Study

A `Study` is one coherent research evaluation or analysis inside a ResearchWork.

Examples:

### Biology

A cell experiment evaluating an ASO.

### Chemistry

A catalytic reaction under specified conditions.

### Physics

A measurement conducted on a physical system.

### Computer Science

An algorithm evaluated against a baseline on a particular benchmark.

### Machine Learning

A model/configuration evaluated on one or more datasets.

A single paper may contain many studies.

---

# 15. EvidenceClaim

Core object:

```text
EvidenceClaim

id
research_work_id
study_id

subject
predicate
object / outcome

claim_type
claim_text
normalized_claim

research_context
method
comparator
measurement
result

evidence_span
```

A claim can approximately represent:

```text
subject
    +
relationship
    +
result
    +
conditions
```

---

# 16. Claim Types

Possible generalized claim types:

```text
PERFORMANCE
EFFECT
ASSOCIATION
COMPARISON
EXISTENCE
NON_EXISTENCE
MECHANISM
PROPERTY
SCALING
ROBUSTNESS
REPRODUCTION
THEORETICAL
OTHER
```

Examples:

```text
PERFORMANCE
Algorithm A outperforms Algorithm B.

EFFECT
Compound X increases yield.

PROPERTY
Material X exhibits superconductivity below temperature Y.

ASSOCIATION
Variable X correlates with outcome Y.

THEORETICAL
Algorithm X has O(n log n) expected complexity under assumptions A.
```

---

# 17. ResearchContext

General container describing what was studied.

```text
domain

system
population
dataset
benchmark
material
organism
cell_line
environment
hardware
software
model
simulation
theoretical_assumptions

domain_attributes
```

Not every field applies to every domain.

---

# 18. Method

Represents what researchers did.

Examples:

### Computer Science

```text
algorithm
architecture
training procedure
retrieval system
compiler optimization
networking strategy
```

### Biology

```text
knockdown
gene editing
drug treatment
assay protocol
```

### Chemistry

```text
reaction method
catalyst
synthesis procedure
```

General fields:

```text
name
normalized_name
method_type
parameters
domain_attributes
```

---

# 19. Comparator

Many research claims involve comparison.

```text
Comparator

name
type
configuration
domain_attributes
```

Examples:

```text
baseline model
control group
untreated sample
existing algorithm
standard catalyst
reference material
theoretical baseline
```

Comparator may be absent.

---

# 20. Measurement

Generalized replacement for the biomedical `Endpoint`.

```text
name
normalized_name
category
measurement_method
unit
```

Examples:

```text
accuracy
F1
latency
throughput
energy consumption
tensile strength
reaction yield
cell viability
protein abundance
temperature
pressure
```

---

# 21. Result

```text
direction
value
unit
effect_size
uncertainty
statistical_significance
p_value
confidence_interval
result_text
```

Possible generalized directions:

```text
INCREASED
DECREASED
IMPROVED
WORSENED
UNCHANGED
MIXED
OBSERVED
NOT_OBSERVED
UNKNOWN
```

---

# 22. EvidenceSpan

Every important claim must retain direct provenance.

```text
research_work_id
section_id
start_offset
end_offset
source_text
```

The system must always be able to answer:

> Why did you extract this claim?

with an exact source passage.

---

# 23. Domain Profiles

The generic model prevents the system from becoming locked to one STEM discipline.

However, completely generic extraction would sacrifice useful domain detail.

Therefore implement **Domain Profiles**.

```text
Generic STEM Core
        │
        ├── BiologyProfile
        ├── ChemistryProfile
        ├── PhysicsProfile
        ├── ComputerScienceProfile
        └── EngineeringProfile
```

A profile defines:

- expected entities;
- common methods;
- common measurement types;
- normalization rules;
- domain-specific attributes;
- evidence-gap dimensions;
- comparability features.

---

# 24. Example Biology Extension

```text
organism
cell_line
tissue
disease_model
intervention
dose
duration
assay
```

---

# 25. Example Computer Science Extension

```text
task
algorithm
model
model_version
dataset
benchmark
training_data
hardware
baseline
hyperparameters
evaluation_metric
compute_budget
```

Example:

```text
Study

task:
    factual QA

method:
    retrieval-augmented generation

model:
    Llama-family model

dataset:
    benchmark X

comparator:
    same model without retrieval

measurement:
    factual error rate

result:
    decreased by X
```

---

# 26. Example Systems Extension

```text
hardware
operating_system
workload
concurrency
dataset
network_conditions
baseline
throughput
latency
memory
CPU utilization
energy
```

This allows queries such as:

> Does eBPF improve packet-processing throughput relative to userspace networking under high load?

---

# 27. Example Chemistry Extension

```text
compound
catalyst
solvent
temperature
pressure
concentration
reaction_time
yield
selectivity
```

---

# 28. Domain Detection

Each ResearchWork receives a domain classification.

Examples:

```text
BIOLOGY
CHEMISTRY
PHYSICS
COMPUTER_SCIENCE
ENGINEERING
MATHEMATICS
MULTIDISCIPLINARY
OTHER_STEM
```

Domain detection chooses the extraction profile.

The generic schema remains authoritative.

Domain-specific extractors only enrich it.

---

# 29. Ingestion Architecture

The ingestion system must not be tied to PubMed.

Use a common adapter interface:

```text
LiteratureSourceAdapter

search()
fetch_metadata()
fetch_full_text()
```

Possible adapters:

```text
PubMed / PMC Adapter
Crossref Adapter
OpenAlex Adapter
arXiv Adapter
future domain sources
```

Version 1 does not need every source.

The architecture must allow them.

---

# 30. Recommended Version 1 Sources

Start with:

### PubMed / PMC

Strong biomedical coverage and structured full text where available.

### arXiv

Important for:

- computer science;
- physics;
- mathematics;
- statistics;
- engineering.

### Crossref or OpenAlex

Use for cross-domain metadata/discovery where useful.

Do not implement a large number of source integrations merely for coverage.

Two strong source adapters are preferable to six fragile ones.

---

# 31. Extraction Pipeline

```text
Literature source
        ↓
metadata
        ↓
full-text lookup
        ↓
section parser
        ↓
domain detection
        ↓
Generic STEM extractor
        ↓
domain-profile enrichment
        ↓
structured output
        ↓
Pydantic validation
        ↓
relationship validation
        ↓
normalization
        ↓
EvidenceClaims
        ↓
evidence database
```

Invalid outputs are stored.

They are never silently discarded.

---

# 32. Relationship Preservation

This remains essential across STEM.

Example computer-science paper:

```text
Model A
Dataset X
Accuracy = 87%

Model B
Dataset X
Accuracy = 92%
```

Never flatten to:

```text
models = A, B
accuracy = 87%, 92%
```

Preserve:

```text
StudyResult 1
Model A → Dataset X → Accuracy 87%

StudyResult 2
Model B → Dataset X → Accuracy 92%
```

The same requirement applies to biological doses, chemistry conditions, physics measurements, and engineering benchmarks.

---

# 33. Normalization

Normalization remains separate from extraction.

Examples:

### Computer Science

```text
ResNet-50
ResNet50
ResNet 50
        ↓
ResNet-50
```

### Biology

```text
tau
MAPT
microtubule-associated protein tau
        ↓
MAPT
```

### Units

```text
0.1 seconds
100 milliseconds
        ↓
100 ms
```

### Hardware

```text
NVIDIA A100
A100 GPU
A100
        ↓
NVIDIA A100
```

Preserve both original and canonical representations.

---

# 34. Query Proposition

User input becomes a typed `QueryProposition`.

Example:

> Retrieval-augmented generation reduces factual hallucination compared with no retrieval.

```text
domain:
    computer science

subject:
    retrieval-augmented generation

relationship:
    reduces

measurement:
    factual hallucination

comparator:
    no retrieval

expected_direction:
    decreased
```

A query does not need to populate every field.

---

# 35. Evidence Retrieval

```text
natural-language query
        ↓
QueryProposition
        ↓
normalization
        ↓
structured retrieval
        ↓
lexical / semantic candidate retrieval
        ↓
comparability analysis
        ↓
stance classification
        ↓
ranking
        ↓
organized results
```

Retrieval and stance classification must remain separate components.

---

# 36. Search Strategy

Start simple.

### Version 1

Use:

- structured database filters;
- SQLite FTS5 or equivalent full-text search;
- normalized entity matching.

Add embeddings only if benchmark results demonstrate meaningful retrieval failures.

This creates an excellent interview story:

> We measured retrieval quality before introducing a vector database.

---

# 37. Comparability Engine

Before classifying a result as support or contradiction, determine whether it actually addresses the proposition.

Generic dimensions:

```text
subject compatibility
method compatibility
context compatibility
comparator compatibility
measurement compatibility
conditions compatibility
evidence directness
```

Possible levels:

```text
EXACT
HIGH
MODERATE
LOW
INCOMPATIBLE
```

---

# 38. Domain-Specific Comparability

## Computer Science

Compare:

```text
task
dataset
model family
baseline
metric
hardware
evaluation conditions
```

## Biology

Compare:

```text
target
intervention
organism
model
endpoint
dose context
```

## Chemistry

Compare:

```text
reaction
catalyst
substrate
conditions
measurement
```

The generic engine delegates detailed comparison to the active domain profile.

---

# 39. Evidence Stance

Once comparability is established:

```text
SUPPORTS
CONTRADICTS
NULL
MIXED
INDIRECT
INSUFFICIENTLY_COMPARABLE
```

Every stance record includes:

```text
query_id
claim_id
stance
comparability
reason
```

Do not treat model confidence as calibrated probability.

---

# 40. Potential Conflict Detection

The system searches for claims that are:

```text
sufficiently comparable
+
report meaningfully different results
```

Example CS conflict:

```text
Study A:
RAG improves factuality on benchmark X.

Study B:
RAG provides no factuality improvement
on a comparable benchmark/configuration.
```

Display:

### Shared characteristics

- model family;
- task;
- retrieval architecture;
- factuality metric.

### Differences

- benchmark;
- retrieval corpus;
- chunking;
- model size;
- evaluation protocol.

Do not assert that one of these differences caused the disagreement.

---

# 41. Cross-Study Evidence Diversity

Generic measures:

```text
distinct contexts
distinct methods
distinct measurements
distinct datasets / systems / populations
distinct research-group clusters
```

Domain profiles add useful dimensions.

### Computer Science

```text
datasets
benchmarks
model families
hardware configurations
codebases
evaluation metrics
```

### Biology

```text
organisms
cell models
animal models
assays
interventions
```

---

# 42. Replication and Independence Proxy

Bibliographic metadata provides a conservative proxy for research independence. The system compares author overlap, first and senior author overlap, and affiliation overlap. It reports distinct research-group clusters and the rules that produced them.

A cluster is not proof of independence. Different affiliations can share data, code, benchmarks, or investigators. Missing author metadata limits the result. The dossier separates the number of claims, studies, publications, and group clusters.

For computer science, shared datasets, model checkpoints, codebases, and evaluation protocols provide additional context. A repeated benchmark result does not establish independent replication by itself.

# 43. Evidence Gaps

Each domain profile defines a documented set of evidence dimensions. The system assigns coverage from qualifying claims in the searched corpus. Gap dimensions do not come from an unconstrained model response.

Generic dimensions include independent replication, diverse contexts, direct measurements, alternative methods, and external validation. Computer science profiles can add unseen datasets, different model families, hardware variation, deployment evidence, and longitudinal evaluation.

Coverage states are identified, limited, not identified, and not assessable. Each state includes its rule, qualifying claims, and corpus scope. The system states: "No qualifying evidence identified in the searched corpus." It does not infer that evidence does not exist.

# 44. Methodological Reporting

The extractor records whether methodological details appear in the analyzed text. Each flag links to an evidence span or records that no matching passage was identified.

Computer science fields include dataset version, data split, baseline configuration, hyperparameters, compute budget, hardware, random seeds, repeat runs, uncertainty estimates, and code availability.

Other profiles use relevant fields such as controls, replicates, dose, duration, randomization, blinding, instrument settings, or theoretical assumptions. A detail missing from an abstract remains unknown. A reporting flag does not establish study quality or prove that a method was absent.

# 45. Evidence Dossier Output

A dossier records its query proposition, creation time, corpus scope, source levels, and analysis versions. It contains the following sections:

- Claim counts by stance, with a list of the underlying claims.
- Diversity and research-group clusters, with uncertainty from missing metadata.
- Potential conflicts, shared conditions, and observed differences.
- Evidence gaps and methodological reporting flags.
- Source passages, publication identifiers, and links for audit.

Illustrative counts in this plan are examples. They are not measured project results. Counts must distinguish claims from studies and publications. The system does not treat a majority of supporting claims as a probability that a proposition is true.

# 46. Persistence and Extraction Audit

SQLite stores the first implementation. The core tables represent research works, source documents, sections, studies, evidence claims, evidence spans, and extraction runs. Related tables store query propositions, stance assessments, conflict pairs, dossier snapshots, and evaluation labels.

Typed records define the public contract. Domain attributes use validated extensions. A graph database is not required to preserve claim relationships.

Each extraction run records the model identifier, prompt version, schema version, source document, time, raw response, validation status, and errors. Invalid responses remain available for analysis. A claim retains the original value alongside each normalized value.

Document identity and source version must remain stable enough to reproduce evidence offsets. Changes to source text require a new version. Duplicate publications and preprint versions need explicit links so dossier counts do not silently inflate.

# 47. Service Boundaries

LiteratureSourceAdapter provides search, metadata fetch, and full-text fetch. The parser produces sections. Domain detection chooses a profile. The extractor produces structured candidate claims.

Validation checks the schema, relationships, and evidence spans. Normalization produces canonical values. The repository stores valid claims and extraction audit records.

QueryParser produces a QueryProposition. Retriever finds candidates. ComparabilityEngine checks relevant conditions. StanceClassifier assigns a query-relative stance and explanation. DossierBuilder aggregates these records.

Evaluation uses fixed fixtures and labeled datasets. The future Experiment Design Evidence Checker consumes the same claims and comparison services after the core system is established.

# 48. API Surface

FastAPI provides a small typed interface. Route names below define the proposed STEM-wide contract. No route requires a biomedical target or disease.

```http
POST /search/evidence
POST /dossiers
GET /dossiers/{dossier_id}
GET /claims/{claim_id}
GET /works/{work_id}
GET /conflicts
GET /evaluation
```

Search accepts a proposition and optional domain, source-level, and context filters. It returns claims with stance, comparability reasons, and provenance. Dossier creation returns a dossier identifier and its results or status. Claim and work routes expose the underlying audit records.

Requests and responses use Pydantic models. Lists use bounded results and pagination. API documentation provides the initial demonstration interface. A custom frontend is outside the core MVP.

# 49. Annotation Corpus

Annotation rules precede labels. The initial corpus covers at least biology and computer science so the generic schema receives a meaningful cross-domain check. The architecture supports broader STEM coverage through later profiles and benchmarks.

An initial target is approximately 100 to 120 documents, subject to annotation effort. Development and held-out test sets remain separate. Splits keep related versions of a work together. Prompt changes use the development set.

Labels cover claims, context, methods, comparators, measurements, results, relationships, and evidence spans. Guidelines define absent values, ambiguous cases, normalization equivalence, multiple studies per paper, and source-level limits.

A query benchmark contains approximately 20 to 30 research questions with relevant claims and stance labels. The final held-out results are reported after the configuration is fixed. These corpus sizes are planning targets, not completed work.

# 50. Evaluation Layers

Extraction evaluation reports precision, recall, and F1 for each field. It includes micro and macro aggregates and results by domain and source level. Normalization rules are fixed before scoring.

Relationship evaluation checks whether values belong to the correct study and result. Correct entities with incorrect links do not receive full relationship credit. Evidence-span evaluation checks exact source text and location, with a documented overlap rule where exact boundaries differ.

Retrieval evaluation reports Recall@5, Recall@10, and Precision@10. Stance evaluation reports macro F1, per-class results, and a confusion matrix. Comparability evaluation checks labeled pairs and explains incompatible cases.

Error analysis separates extraction, normalization, retrieval, comparison, and classification failures. Model and prompt versions accompany every report. No example score in the discussion becomes a claimed achievement.

# 51. Reliability and Security

Literature text is untrusted input. Prompts delimit source content and instruct the extractor to treat it as data. The extraction step receives no authority to execute instructions found in a paper.

- Structured outputs pass schema and relationship validation before the claim store accepts them.
- Approximately 10 to 20 adversarial fixtures check planted instructions, false roles, and schema manipulation.
- Cached source fixtures keep automated tests independent of live literature APIs.
- Run limits bound document counts and API spend. Failures remain visible in the run report.
- Secrets stay outside the repository. CI runs secret and dependency scans.

The project reports adversarial regression results. It does not claim that prompt injection is impossible. Full-text availability and source restrictions remain visible; missing content does not become fabricated content.

# 52. Repository Baseline

The Python project uses Pydantic, SQLite, FastAPI, pytest, and strict type checks. The extraction provider remains behind an adapter. Model configuration records the exact model and prompt used.

GitHub Actions runs lint checks, mypy in strict mode, tests, gitleaks, and pip-audit. Boundary models cover API input, external responses, files, and LLM output. Network responses use recorded fixtures.

The repository contains a concise project description, architecture diagrams, setup instructions, and an environment example without secrets. Architectural rules describe the module boundaries. A short demo shows a query, a stance result, and its exact source passage.

Each branch addresses one feature. Changes remain small enough for a human review, with the original target of fewer than 300 changed lines per PR where practical. A human reads each generated diff before merge. Changes involving authentication, billing, or secrets receive explicit security review.

# 53. Core MVP Sequence

The core MVP answers a research question with evaluated, provenance-linked claims. The following increments define a shippable path.

## Increment 1 Corpus and adapters

Implement the source interface, PubMed with PMC lookup, and an arXiv path. Store metadata, available content, and source level. Exit condition: recorded fixtures reproduce ingestion and abstract fallback without a live network call.

## Increment 2 Schema and profiles

Implement ResearchWork, Study, EvidenceClaim, context, method, comparator, measurement, result, and evidence spans. Add biology and computer science profiles. Exit condition: both domains validate without biomedical fields in the generic core.

## Increment 3 Extraction and normalization

Extract claims, retain invalid outputs, preserve relationships, and normalize names and units. Exit condition: a stored claim resolves to its exact source text and extraction configuration.

## Increment 4 Gold labels and evaluation

Create annotation guidelines, development and test splits, and extraction scoring. Exit condition: a reproducible report includes field, relationship, and evidence-span errors.

## Increment 5 Query and stance

Add structured retrieval, full-text search, comparability, stance, and the query benchmark. Expose the FastAPI routes. Exit condition: a query returns organized claims with reasons and provenance, plus separate retrieval and stance results.

# 54. Advanced Dossier Sequence

Advanced dossier work follows the evaluated core MVP.

- Add research-group clusters and domain-specific diversity measures.
- Add potential conflict pairs with shared conditions and observed differences.
- Add documented evidence-gap dimensions and methodological reporting flags.
- Generate reproducible dossiers with corpus scope and source-level limitations.
- Evaluate aggregation rules and demonstrate dossier drill-down to individual claims.

These increments share the existing claim database. The release remains useful before all advanced analyses exist. The expanded project does not retain the original three-week estimate.

# 55. Experiment Design Evidence Checker

The Experiment Design Evidence Checker remains a future build. It is excluded from the core MVP and advanced dossier release requirements.

A researcher enters a proposed experiment, benchmark, evaluation, or study. The checker retrieves comparable published studies and shows how the proposed conditions relate to prior evidence.

For biology, comparison can include model, intervention, dose, duration, controls, assay, and endpoints. For computer science, comparison can include task, dataset, model version, baseline, hardware, compute budget, metrics, and evaluation protocol.

The checker shows published ranges and common patterns. It identifies substantial differences from retrieved precedent. Every comparison links to evidence claims and exact source passages.

The first checker release provides evidence comparisons. It does not prescribe a design or claim that precedent proves a proposed study will succeed. Its prerequisites are reliable extraction, domain profiles, comparability, provenance, and an evaluated query system.

# 56. Other Future Work

Additional STEM profiles and source adapters expand coverage after the initial domains pass evaluation. Semantic retrieval or embeddings require evidence of meaningful failures in the baseline retrieval benchmark.

A custom interface, richer table extraction, and larger corpora can follow the backend. None is required to demonstrate the core claim-to-source path. Provider changes require a new evaluated configuration.

# 57. Acceptance Criteria

- A biology query and a computer science query both use the same core domain model.
- Each accepted claim retains its study relationships, source level, and exact evidence span.
- Query results distinguish supports, contradicts, null, mixed, indirect, and insufficiently comparable.
- A fixed held-out evaluation reports measured results and known failures without reused development labels.
- Dossiers expose their searched corpus and cautious gap language; the future checker remains outside release requirements.

# 58. Demonstration Path

The demo uses a specific computer science proposition such as whether retrieval reduces factual hallucination for the same base model. It shows structured query fields, retrieved claims, and comparability reasons.

A selected result opens the study context, baseline, metric, outcome, and exact passage. A second query demonstrates the biology profile. The evaluation report shows where the extractor or stance classifier fails.

The advanced demo adds a dossier with diversity, potential conflicts, and evidence gaps. The project description uses only measured document counts and evaluation scores after the implementation exists.

# 59. Diagram Set

The diagram appendix contains the system architecture, core research UML, claim detail UML, query and dossier UML, and domain profiles with the future checker. Each diagram uses an opaque white background, light class headers, and dark text and connectors.

UML diagrams describe the conceptual model. They do not imply that every object requires a separate SQL table. Solid associations show data relationships. A dashed arrow shows a dependency. A hollow triangle shows interface realization. Multiplicity labels indicate optional or repeated records.
