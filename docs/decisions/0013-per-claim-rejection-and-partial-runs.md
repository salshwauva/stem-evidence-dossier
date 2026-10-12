# ADR 0013: A claim that fails validation is rejected alone, and the run is PARTIAL

## Status
Accepted, 2026-10-02

## Context
Plan section 31 discards a whole document when one claim fails validation. The first recordings on real papers showed the cost. One claim with an unknown field in `research_context` (`training_data`) turned a reply of four claims into an INVALID run with no claim stored. The same rule applies to an evidence span that does not match the section text.

The plan also says no data is silently discarded. A whole-document discard throws away claims that passed every check, and the reader of the store sees only that the run failed.

## Decision
The reply is checked in two passes. The studies, the top-level keys and the shape of the `claims` list validate for the whole reply, and a failure there makes the run INVALID. Each claim then validates alone: its schema, its study key, its section and its evidence span.

A claim that fails is rejected alone and leaves one error on the run, in the form `claims.<n>.<field>: <reason>`. The run is PARTIAL when at least one claim passed and at least one failed. It is INVALID when the reply fails as a whole or every claim fails. It is VALID when no claim fails.

A PARTIAL run stores the studies and the claims that passed. The run keeps its full raw reply, so a rejected claim stays recoverable from the reply and its index. A claim ID is its position in the reply, so a rejected claim leaves a gap in the numbering. The `extract` command exits with status 1 for a PARTIAL run. The `demo` command prints the status and the errors of each document and exits 0, so a replay of a recording with a PARTIAL or INVALID paper still runs to the end.

Two questions stay open until a recording shows a need:
- **A whitespace-tolerant span match.** If model copies still miss the section text, the check tries a match that treats each run of whitespace as one token boundary, but only when the exact match finds nothing. The stored span is always cut from the section text, never copied from the reply, so `EvidenceSpan.matches` holds and the offsets come from the section.
- **Prose around unfenced JSON.** The parse stays strict. A reply that is not one fenced JSON block or pure JSON becomes an INVALID run with the raw reply stored. Taking the first object in a reply may pick up an example the model quoted, and it hides drift in the prompt.

## Consequences
Easier: one bad quote or one stray field costs one claim, not a document. The run row shows what was rejected and why. No migration is needed, because `extraction_runs.errors` is a JSON list and `validation_status` is plain text.

Harder: consumers that assume dense claim numbering see gaps. A PARTIAL run is not clean, so a count of "valid runs" has to say whether it includes PARTIAL. Rejected claims have no rows of their own, so a query over them needs a new table if the need arises.

## Alternatives considered
- **Keep the whole-document discard.** Rejected: it drops claims that passed, which is the loss the plan forbids.
- **Drop unknown keys inside `research_context` and keep the claim.** Rejected: it discards data without a trace.
- **A table of rejected claims.** Deferred: the raw reply and the error prefix already recover them.
- **Extract the first JSON object from a reply with prose around it.** Rejected for now. Structured output from the CLI is the better fix if prose wrapping shows up often.
