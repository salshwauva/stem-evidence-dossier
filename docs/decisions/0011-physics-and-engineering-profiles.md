# ADR 0011: Physics and engineering profiles

## Status
Accepted, 2026-09-12

## Context
Plan section 23 names five domain profiles: biology, chemistry, physics, computer science and engineering. Three of them existed. Ingestion already labels the other two. The arXiv archives physics, astro-ph, cond-mat and quant-ph map to PHYSICS, and eess maps to ENGINEERING (ADR 0010). Both domains fell to GenericProfile, which holds no attributes and no expected entities. The extraction prompt then told the model to leave domain_attributes null, and the comparability engine had no domain feature to read for either one.

The plan gives a field list for biology (section 24), for computer science (section 25) and for chemistry (section 27). It gives no list for physics and no list for engineering.

## Decision
PhysicsAttributes and EngineeringAttributes join the closed union in `src/evidence_dossier/model/attributes.py`, under the tags "physics" and "engineering". PhysicsProfile and EngineeringProfile sit beside the other three profiles, and `get_profile` returns them for PHYSICS and ENGINEERING. Mathematics and every other domain keep GenericProfile.

Both field lists are a judgment call. Each docstring cites the plan sections that the list reads.

Physics holds the apparatus, the sample, temperature, pressure, field strength, wavelength, the instrument, the simulation code and the theoretical assumptions. Section 14 calls a physics study a measurement on a physical system. Section 17 names system, material, environment, simulation and theoretical_assumptions. Section 20 names temperature and pressure. The physics query in section 4 asks about a refractive index at microwave frequencies.

Engineering holds the system, the component, the material, the load, the operating conditions, the standard, the test method, the duty cycle and the tolerance. Section 3 puts engineering and materials science in scope. Section 17 names system, material and environment. Section 20 names tensile strength. Section 26 names hardware, workload, concurrency and network conditions.

The comparability engine reads a claim's attributes by class. `_condition_value` named three classes, so a physics claim compared on no physics field. It now names every member of the closed union, and a new profile that stays out of that list reads as padding.

The polarity table gains cycle time as lower is better, and efficiency and yield strength as higher is better. Each of the five engineering measurement types now has a direction. Physics adds no entry. Temperature, pressure and a refractive index improve upward in one experiment and downward in the next, so the direction depends on the context and the stance classifier reports the missing polarity instead.

POLARITY_VERSION moves to polarity-v2. Every stance assessment records the table version that decided it. Two assessments that both cite polarity-v1 have to come from one table, so a new entry needs a new version.

## Consequences
Easier: a physics paper from cond-mat and an engineering paper from eess reach a typed profile. The prompt names the expected entities and the attribute fields of that profile, and the comparability engine compares two claims on the conditions that the profile names.

Harder: five profiles are five places to keep in step. One new profile still touches the attribute class, the AttributeModel alias, the registry, the isinstance list in `query/comparability.py` and the PROFILED_DOMAINS set in the tests. The feature names of a profile only report a condition when `_FEATURE_FIELDS` in `query/comparability.py` maps the name to a field, so a feature outside that table is documentation and nothing more.

Nothing here measures the two new domains on real papers. The profiles carry data that the prompt and the engine read, and the tests use invented claims.

## Alternatives considered
- **Leave both domains on GenericProfile.** Rejected: ingestion labels the papers PHYSICS and ENGINEERING already, and the generic profile drops every typed field that the plan asks a profile to carry.
- **Copy the systems extension of plan section 26 into the engineering attributes.** Rejected: section 26 describes computer systems, with concurrency and network conditions. The eess archive covers signal processing, image and video, audio and speech, and systems and control.
- **Add the new measurements to the polarity table without a version bump.** Rejected: a stored assessment cites the version, and two tables under one version make a stored reason unreadable.
- **Give physics a measurement polarity for temperature and pressure.** Rejected: a colder sample is the result in one paper and the failure in the next.
