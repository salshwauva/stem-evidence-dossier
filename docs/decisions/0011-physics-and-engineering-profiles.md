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

A declared comparability feature reaches the engine only through `_FEATURE_FIELDS`, which maps the feature name to the claim field that reports it. The table gains nine names for the two new profiles. Physics maps system, sample, apparatus and theoretical assumptions, and keeps the conditions entry that already pointed at a temperature field. Engineering maps system, component, material, load, operating conditions and standard, and keeps the hardware entry. A feature whose name the generic ResearchContext declares, such as system and material, reads the generic field first and the attribute field second. The engineering profile names its feature "operating conditions" rather than "conditions", because "conditions" reads a temperature field that no engineering record carries.

The three older profiles keep their gaps. Biology declares target and endpoint, chemistry declares reaction, and computer science declares baseline and metric, and the table maps none of the five. An entry for any of them would change comparability, and so stance, for a domain that this decision does not touch. The gap belongs to whoever changes those domains next.

A feature named after a generic dimension needs no entry. The engine assesses subject, method, context, comparator, measurement and evidence directness on their own dimensions, so the measurement feature of physics, of engineering and of chemistry reads as unmapped and loses nothing. `test_the_feature_table_covers_the_features_each_profile_declares` pins the read and unread split for every profile that the registry returns, so the gap cannot grow in silence.

The polarity table gains cycle time as lower is better, and efficiency and yield strength as higher is better. Each of the five engineering measurement types now has a direction. Physics adds no entry. Temperature, pressure and a refractive index improve upward in one experiment and downward in the next, so the direction depends on the context and the stance classifier reports the missing polarity instead.

POLARITY_VERSION moves to polarity-v2. Every stance assessment records the table version that decided it. Two assessments that both cite polarity-v1 have to come from one table, so a new entry needs a new version.

## Consequences
Easier: a physics paper from cond-mat and an engineering paper from eess reach a typed profile. The prompt names the expected entities and the attribute fields of that profile. The engine compares two physics claims on five of the six features that the physics profile declares, and two engineering claims on seven of the eight that the engineering profile declares. The one unmapped name on each side is measurement, which the engine assesses on its own dimension.

Harder: five profiles are five places to keep in step. One new profile touches the attribute class, the AttributeModel alias, the registry, the isinstance list in `query/comparability.py`, `_FEATURE_FIELDS` in the same file, the PROFILED_DOMAINS set in the tests and the split that the guard test pins. A feature name outside `_FEATURE_FIELDS` is documentation and nothing more, and the guard test is what makes that visible.

Nothing here measures the two new domains on real papers. The profiles carry data that the prompt and the engine read, and the tests use invented claims.

## Alternatives considered
- **Leave both domains on GenericProfile.** Rejected: ingestion labels the papers PHYSICS and ENGINEERING already, and the generic profile drops every typed field that the plan asks a profile to carry.
- **Copy the systems extension of plan section 26 into the engineering attributes.** Rejected: section 26 describes computer systems, with concurrency and network conditions. The eess archive covers signal processing, image and video, audio and speech, and systems and control.
- **Add the new measurements to the polarity table without a version bump.** Rejected: a stored assessment cites the version, and two tables under one version make a stored reason unreadable.
- **Give physics a measurement polarity for temperature and pressure.** Rejected: a colder sample is the result in one paper and the failure in the next.
