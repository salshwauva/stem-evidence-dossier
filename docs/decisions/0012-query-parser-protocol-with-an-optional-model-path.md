# ADR 0012: One query parser protocol, with the rules as the default

## Status
Accepted, 2026-09-12

## Context
ADR 0006 chose a fixed set of rules over a model call and named the cost: a proposition phrased outside the verb table parses with the relationship "unknown", and the stance classifier then answers INDIRECT. Plan section 36 says to start simple and to add machinery only when a benchmark shows the simple path failing. No benchmark measured the parse, so the size of that cost was a guess.

The README claims that the project parses a research proposition. A reader deserves a number behind that claim, and a model call under the parse must not become a model call under the evidence verdicts.

## Decision
Three parts, in `src/evidence_dossier/query/`.

**The rules cover more forms.** `parser.py` holds one table of relationship verbs: increases, reduces, improves, worsens, no change, outperforms and underperforms. The parser takes the verb that starts first in the text, not the first row of the table. An auxiliary and "not" in front of a verb keep the verb label, so "does not reduce" never parses as "reduces". A negated verb states no expected direction, because "not decreased" names more than one direction. "Does not change" and "has no effect on" keep UNCHANGED, because those words name one direction and guess nothing. The comparator markers are compared with, compared to, compared against, relative to, versus, vs, vs., against, than and over. The outperform verbs name the comparator before the measurement, so they split the other way around. The measurement keeps its own phrase: it drops the article, stops at the setting that follows it, and drops a comparison word that belongs to the comparator.

The article rule differs by field, and the benchmark labels follow the same split. The subject and the measurement drop a leading article, because retrieval and the comparability engine match them against a claim subject and a measurement name, where the article carries nothing. The comparator keeps every word after the marker, article and all, because a comparator is written as one phrase: "a scrambled control" and "the uncatalysed route" read as the names of conditions. A label such as "the uncatalysed route" therefore states this convention. It does not grade a quirk of the parser as correct.

**One protocol, two implementations.** `QueryParser` is a protocol with a `parse` method. `DeterministicQueryParser` wraps the rules and stays the default. `ModelQueryParser` in `model_parser.py` takes a callable that maps a prompt to text, plus a fallback parser. The caller supplies the callable, so `query` imports no provider, holds no key and imports no sibling subpackage. The prompt wraps the query text between delimiters and names it as untrusted data. The reply must validate into `ModelParse`, which forbids an extra field and accepts only a `ResultDirection` value. A provider error, a reply that is not one JSON object, a missing field or an unknown direction falls back to the deterministic parser. Every parse records its path in `parse_notes`.

**A benchmark decides what to do next.** `tests/query_parse_benchmark.py` holds 30 hand written propositions across computer science, biology, and the physical and engineering domains, each with the subject, relationship, measurement and comparator that a correct parse yields. `.venv/bin/python -m tests.query_parse_benchmark` prints 20 resolved, 6 partial and 4 unresolved, and it names every case it does not resolve.

## Consequences
Easier: a parse still costs nothing, repeats exactly and needs no key. The benchmark turns "the rules miss some phrasings" into a list of ten named cases, so the next rule has evidence behind it. A caller who wants the model path constructs `ModelQueryParser` with its own callable and gets the rules back whenever the model fails.

Harder: the ten cases the rules do not resolve fall in three groups, and each group asks for different work. A verb outside the table ("extends", "suppresses", "is associated with") asks for more rows. A question that states no relationship ("what is the effect of X on Y") asks for a second parse shape. A sentence that does not put the subject in front of the verb (a passive question, "is there evidence that", a noun phrase, a modal such as "may") asks for structure that a verb table does not hold.

The benchmark measures the rules against its own author. Claude wrote the 30 propositions, their labels and the mix of phrasings in the same session that broadened the rules, so a phrasing that nobody thought of is missing from both. Nothing in the benchmark comes from a real query log. A second reader, or a set of queries that real users typed, would make the number worth more.

The model path carries its own risk, and this repository has not measured it. `ModelQueryParser` has never run against a real model here, so no number in the README comes from a model parse. The tests drive it with a fake callable, which proves the fallback and the validation, and proves nothing about a real reply.

## Alternatives considered
- **Make the model parser the default.** Rejected: it adds a provider dependency, a prompt version and a parse that changes between runs, and the benchmark shows the rules resolving 20 of 30 without any of that.
- **Map a negated verb to UNCHANGED.** Rejected: "does not reduce" is also true when the number rose, so UNCHANGED would be a guess that the stance rules would then treat as a fact. No expected direction gives INDIRECT, which matches the measurement polarity rule in ADR 0007.
- **Keep the model reply as free text and pick fields out of it.** Rejected: the query text is untrusted, so the reply is untrusted. Validation into a typed record is what stops an instruction inside a query from reaching a field.
- **Broaden the rules until they cover all 30.** Rejected for now: each phrasing is another row or another shape, and the benchmark says which ones are worth the rule.
