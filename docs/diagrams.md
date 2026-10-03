# Diagrams

Class diagrams of the conceptual model (plan section 59). The system diagrams, which show the data flow, are in [architecture.md](architecture.md). A diagram shows the records and services as the code defines them. It does not imply one SQL table per class; ADR 0002 gives the table layout.

Notation: a solid arrow with a label is an association, and a dashed arrow is a dependency. A hollow triangle on a dashed line is interface realization, and a hollow triangle on a solid line is inheritance. A filled diamond marks composition. A multiplicity of `0..1` marks an optional record and `*` a repeated one. A type with a question mark is optional in the code.

## Core research records

```mermaid
classDiagram
    class ResearchWork {
        +str id
        +str title
        +Domain domain
        +str? doi
        +str? abstract
        +date? publication_date
        +str? venue
        +dict external_identifiers
    }
    class Author {
        +str name
        +tuple~str~ affiliations
    }
    class WorkLink {
        +str source_work_id
        +WorkLinkRelation relation
        +str target_work_id
    }
    class SourceDocument {
        +str id
        +int version
        +SourceLevel source_level
        +str source_format
        +str raw_text
        +str content_sha256
        +datetime fetched_at
    }
    class Section {
        +str id
        +int ordinal
        +SectionType section_type
        +str? heading
        +str text
    }
    class Study {
        +str id
        +str description
    }
    class ExtractionRun {
        +str id
        +str model_identifier
        +str prompt_version
        +str schema_version
        +datetime created_at
        +str raw_response
        +ValidationStatus validation_status
        +tuple~str~ errors
    }
    class EvidenceClaim {
        +str id
        +ClaimType claim_type
        +str claim_text
    }
    class SourceLevel {
        <<enumeration>>
        FULL_TEXT
        ABSTRACT_ONLY
        METADATA_ONLY
    }
    class ValidationStatus {
        <<enumeration>>
        VALID
        PARTIAL
        INVALID
    }
    class WorkLinkRelation {
        <<enumeration>>
        PREPRINT_OF
        VERSION_OF
        DUPLICATE_OF
    }

    ResearchWork "1" *-- "*" Author : lists
    WorkLink "*" --> "1" ResearchWork : source
    WorkLink "*" --> "1" ResearchWork : target
    ResearchWork "1" --> "*" SourceDocument : has versions
    SourceDocument "1" --> "*" Section : split into
    ResearchWork "1" --> "*" Study : contains
    Study "1" --> "*" EvidenceClaim : holds
    SourceDocument "1" --> "*" ExtractionRun : read by
    ExtractionRun "0..1" --> "*" EvidenceClaim : produced
    SourceDocument ..> SourceLevel
    ExtractionRun ..> ValidationStatus
    WorkLink ..> WorkLinkRelation
```

- A research work is a container. Claims belong to studies, and studies belong to the work (plan section 9).
- A change to the text of a work is a new `SourceDocument` version, so offsets into an earlier version stay valid.
- A claim and its study belong to the same research work. The store rejects a claim that breaks this rule.
- `extraction_run_id` is optional on a claim, so a claim loaded from a gold file has no run.
- Authors are stored inside the work as JSON, in source order.

## Claim detail

```mermaid
classDiagram
    direction LR
    class EvidenceClaim {
        +str id
        +str research_work_id
        +str study_id
        +str? extraction_run_id
        +ClaimType claim_type
        +str claim_text
        +str? normalized_claim
        +str predicate
        +str? outcome
    }
    class Term {
        +str original
        +str? canonical
    }
    class ResearchContext {
        +Domain domain
        +str? system
        +str? population
        +str? dataset
        +str? benchmark
        +str? material
        +str? environment
        +str? hardware
        +str? software
        +str? model
        +str? simulation
        +tuple~str~ theoretical_assumptions
    }
    class Method {
        +str? method_type
        +dict parameters
    }
    class Comparator {
        +str? comparator_type
        +str? configuration
    }
    class Measurement {
        +str? category
        +str? measurement_method
    }
    class Result {
        +ResultDirection direction
        +float? value
        +float? effect_size
        +str? uncertainty
        +bool? statistical_significance
        +str? p_value
        +str? confidence_interval
        +str? result_text
    }
    class EvidenceSpan {
        +str research_work_id
        +str section_id
        +int start_offset
        +int end_offset
        +str source_text
        +matches(section) bool
    }
    class Section
    class DomainAttributes {
        <<union>>
    }

    EvidenceClaim "1" *-- "1" ResearchContext
    EvidenceClaim "1" *-- "0..1" Method
    EvidenceClaim "1" *-- "0..1" Comparator
    EvidenceClaim "1" *-- "0..1" Measurement
    EvidenceClaim "1" *-- "1" Result
    EvidenceClaim "1" *-- "1" EvidenceSpan
    EvidenceClaim --> Term : subject
    Method --> Term : name
    Comparator --> Term : name
    Measurement --> Term : name
    Measurement --> "0..1" Term : unit
    Result --> "0..1" Term : unit
    ResearchContext --> "0..1" DomainAttributes
    Method --> "0..1" DomainAttributes
    Comparator --> "0..1" DomainAttributes
    EvidenceSpan ..> Section : matches
    note for DomainAttributes "One of five attribute classes, chosen by the profile tag. The table below lists them."
```

- A `Term` holds the name as the source wrote it next to the canonical form that normalization sets. Normalization keeps every original.
- `matches(section)` is true only when the span names the section and the text at its offsets equals `source_text`, with `0 <= start_offset < end_offset <= len(section.text)`.
- `DomainAttributes` is a discriminated union. The `profile` tag on each attribute class picks the class, and an unknown tag fails validation (ADR 0003). The union is closed, so a new profile adds its class to the model package.
- A claim does not flatten several values into one field. Two models with two scores are two claims (plan section 32).

| Attribute class | `profile` tag | Fields |
| --- | --- | --- |
| `BiologyAttributes` | `biology` | organism, cell_line, tissue, disease_model, intervention, dose, duration, assay |
| `ComputerScienceAttributes` | `computer_science` | task, algorithm, model, model_version, dataset, benchmark, training_data, hardware, baseline, hyperparameters, evaluation_metric, compute_budget |
| `ChemistryAttributes` | `chemistry` | compound, catalyst, solvent, temperature, pressure, concentration, reaction_time, yield, selectivity |
| `PhysicsAttributes` | `physics` | apparatus, sample, temperature, pressure, field_strength, wavelength, instrument, simulation_code, theoretical_assumptions |
| `EngineeringAttributes` | `engineering` | system, component, material, load, operating_conditions, standard, test_method, duty_cycle, tolerance |

## Query and dossier

Three diagrams follow. The first covers parsing, the second the steps from retrieval to a stance assessment, and the third the organized results and the dossier.

```mermaid
classDiagram
    direction LR
    class QueryParser {
        <<interface>>
        +parse(text, domain, dataset, system, population) QueryProposition
    }
    class DeterministicQueryParser
    class ModelQueryParser {
        -QueryModel model
        -QueryParser fallback
    }
    class QueryProposition {
        +str id
        +str text
        +Domain? domain
        +str subject
        +str relationship
        +str? measurement
        +str? comparator
        +ResultDirection? expected_direction
        +str? dataset
        +str? system
        +str? population
        +tuple~str~ parse_notes
    }

    QueryParser <|.. DeterministicQueryParser
    QueryParser <|.. ModelQueryParser
    ModelQueryParser --> QueryParser : falls back to
    QueryParser ..> QueryProposition : produces
    note for DeterministicQueryParser "Wraps parse_query. search_evidence calls parse_query directly."
    note for ModelQueryParser "No search or API route constructs it (ADR 0012)."
```

```mermaid
classDiagram
    direction LR
    class Retriever {
        +retrieve(proposition, source_level, limit) list~Candidate~
    }
    class Candidate {
        +EvidenceClaim claim
        +float rank
        +tuple~str~ matched_terms
    }
    class ComparabilityEngine {
        +assess(proposition, claim, profile) ComparabilityAssessment
    }
    class ComparabilityAssessment {
        +ComparabilityLevel level
        +tuple~DimensionResult~ dimensions
        +matched(dimension) bool
        +reasons() tuple~str~
    }
    class DimensionResult {
        +str dimension
        +bool matched
        +str reason
    }
    class StanceClassifier {
        +classify(proposition, claim, assessment) StanceAssessment
    }
    class StanceAssessment {
        +str query_id
        +str claim_id
        +Stance stance
        +ComparabilityLevel comparability
        +str reason
        +datetime created_at
    }
    class QueryProposition
    class EvidenceClaim

    Retriever ..> QueryProposition : reads
    Retriever "1" --> "*" Candidate : returns
    Candidate --> EvidenceClaim
    ComparabilityEngine ..> ComparabilityAssessment : returns
    ComparabilityAssessment "1" *-- "7" DimensionResult
    StanceClassifier ..> ComparabilityAssessment : reads
    StanceClassifier ..> StanceAssessment : returns
    StanceAssessment --> QueryProposition : query_id
    StanceAssessment --> EvidenceClaim : claim_id
```

```mermaid
classDiagram
    class search {
        <<module>>
        +search_evidence(store, text, domain, source_level, limit, dataset, system, population) EvidenceResults
        +build_dossier(store, text, domain, source_level, limit) Dossier
    }
    class EvidenceResults {
        +QueryProposition proposition
        +tuple~Candidate~ candidates
        +tuple~StanceAssessment~ assessments
        +tuple~StanceGroup~ groups
    }
    class StanceGroup {
        +Stance stance
        +tuple~EvidenceItem~ items
    }
    class EvidenceItem {
        +EvidenceClaim claim
        +Stance stance
        +ComparabilityLevel comparability
        +tuple~str~ comparability_reasons
        +str stance_reason
        +Provenance provenance
    }
    class Provenance {
        +str research_work_id
        +str study_id
        +str section_id
        +int start_offset
        +int end_offset
        +str source_text
    }
    class Dossier {
        +str id
        +str query_id
        +datetime created_at
        +CorpusScope corpus_scope
        +DossierCounts counts
    }
    class CorpusScope {
        +int claim_count
        +tuple~SourceLevel~ source_levels
    }
    class DossierCounts {
        +int claims
        +int studies
        +int works
        +dict by_stance
    }

    search ..> EvidenceResults : returns
    search ..> Dossier : stores
    EvidenceResults "1" *-- "6" StanceGroup : one per stance
    StanceGroup "1" *-- "*" EvidenceItem
    EvidenceItem "1" *-- "1" Provenance
    Dossier "1" *-- "1" CorpusScope
    Dossier "1" *-- "1" DossierCounts
```

- Retrieval and stance stay separate results. `candidates` holds the retrieval order, and `assessments` and `groups` hold the stances.
- `groups` always holds the six stances in the plan order, and a stance with no claim has an empty `items`.
- The comparability engine always returns seven dimension results, one for each generic dimension. The level is EXACT when all seven match. Without a subject match it is INCOMPATIBLE, and without a measurement match it is LOW. Otherwise it is HIGH when the comparator matches and MODERATE when it does not.
- The plan names a `DossierBuilder`. The code implements it as the function `build_dossier`, so the diagram shows the module.
- `DossierCounts` keeps claims, studies and works apart. No field holds a probability.

## Domain profiles

```mermaid
classDiagram
    class DomainProfile {
        <<dataclass>>
        +Domain domain
        +AttributeModel? attribute_model
        +tuple~str~ expected_entities
        +tuple~str~ common_methods
        +tuple~str~ common_measurement_types
        +tuple~str~ evidence_gap_dimensions
        +tuple~str~ comparability_features
    }
    class BiologyProfile
    class ChemistryProfile
    class ComputerScienceProfile
    class PhysicsProfile
    class EngineeringProfile
    class GenericProfile
    class profiles {
        <<module>>
        +get_profile(domain) DomainProfile
    }
    class ComparabilityEngine
    class ExperimentDesignChecker {
        <<not built>>
    }

    DomainProfile <|-- BiologyProfile
    DomainProfile <|-- ChemistryProfile
    DomainProfile <|-- ComputerScienceProfile
    DomainProfile <|-- PhysicsProfile
    DomainProfile <|-- EngineeringProfile
    DomainProfile <|-- GenericProfile
    profiles ..> DomainProfile : returns
    ComparabilityEngine ..> DomainProfile : reads comparability_features
    ExperimentDesignChecker ..> ComparabilityEngine : uses
    ExperimentDesignChecker ..> profiles : uses
```

| Profile | Attribute class | Comparability features | Extra evidence gap dimensions |
| --- | --- | --- | --- |
| `BiologyProfile` | `BiologyAttributes` | target, intervention, organism, model, endpoint, dose context | None |
| `ChemistryProfile` | `ChemistryAttributes` | reaction, catalyst, substrate, conditions, measurement | None |
| `ComputerScienceProfile` | `ComputerScienceAttributes` | task, dataset, model family, baseline, metric, hardware, evaluation conditions | unseen datasets, different model families, hardware variation, deployment evidence, longitudinal evaluation |
| `PhysicsProfile` | `PhysicsAttributes` | system, sample, apparatus, conditions, measurement, theoretical assumptions | None |
| `EngineeringProfile` | `EngineeringAttributes` | system, component, material, load, operating conditions, standard, hardware, measurement | None |
| `GenericProfile` | None | The seven generic dimensions | None |

- `get_profile(domain)` returns the profile of the domain, and a `GenericProfile` for MATHEMATICS, MULTIDISCIPLINARY and OTHER_STEM. `GenericProfile` has no attribute class.
- `attribute_model` names one attribute class per profile, as the table lists.
- A profile is plain data. The extraction prompt reads `expected_entities` and `attribute_model`. The comparability engine reads `comparability_features` through the table `_FEATURE_FIELDS` (ADR 0011). `normalize_claim` reads `domain`.
- No code reads `common_methods`, `common_measurement_types` or `evidence_gap_dimensions` yet. The gap dimensions belong to the advanced dossier (plan section 54).
- The Experiment Design Evidence Checker (plan section 55) would consume the same claims and comparison services after the core system is evaluated. Nothing in the repository implements it, and it is not part of the MVP.

## Enumerations

| Enumeration | Values |
| --- | --- |
| `Domain` | BIOLOGY, CHEMISTRY, PHYSICS, COMPUTER_SCIENCE, ENGINEERING, MATHEMATICS, MULTIDISCIPLINARY, OTHER_STEM |
| `SectionType` | ABSTRACT, INTRODUCTION, BACKGROUND, METHODS, EXPERIMENT, RESULTS, EVALUATION, DISCUSSION, CONCLUSION, APPENDIX, FIGURE_CAPTION, TABLE, OTHER |
| `ClaimType` | PERFORMANCE, EFFECT, ASSOCIATION, COMPARISON, EXISTENCE, NON_EXISTENCE, MECHANISM, PROPERTY, SCALING, ROBUSTNESS, REPRODUCTION, THEORETICAL, OTHER |
| `ResultDirection` | INCREASED, DECREASED, IMPROVED, WORSENED, UNCHANGED, MIXED, OBSERVED, NOT_OBSERVED, UNKNOWN |
| `Stance` | SUPPORTS, CONTRADICTS, NULL, MIXED, INDIRECT, INSUFFICIENTLY_COMPARABLE |
| `ComparabilityLevel` | EXACT, HIGH, MODERATE, LOW, INCOMPATIBLE |
