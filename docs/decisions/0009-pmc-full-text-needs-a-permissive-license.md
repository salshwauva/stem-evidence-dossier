# ADR 0009: PMC full text needs a permissive license

## Status
Accepted, 2026-09-12

## Context
Plan section 30 takes full text from PMC where it is available. The adapter accepted a PMC body whenever the id converter returned a PMCID and the JATS XML held an article body. Presence in PMC is not permission. PMC holds articles under author manuscript terms, under publisher terms that permit reading alone, and under the noncommercial and no derivatives Creative Commons licenses. The ingest pipeline stores the whole body, splits it into sections, and the API serves spans out of it, so the project redistributes the text. Plan section 51 asks that source restrictions stay visible and that missing content does not become fabricated content.

## Decision
`PubMedAdapter.fetch_full_text` asks the PMC OA web service (`https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi`) for the record of the PMCID before it fetches the body. The call goes through the same HttpClient seam, and `parse_xml` reads the answer, so the entity rules of plan section 51 hold for it too.

The module constant `FULL_TEXT_LICENSES` is the allow list: "CC BY" and "CC0". The comparison folds case and hyphens, so "cc-by" and "CC-BY" match. Every other outcome means no full text: another license, an absent license attribute, an error element such as `idIsNotOpenAccess`, or no record at all. The adapter then returns None, and `ingest_work` falls back to the abstract exactly as it does for a work with no PMCID.

CC BY-NC and CC BY-ND stay out of the allow list. The evidence store is public, so it redistributes what it keeps. NC bars commercial reuse of that copy, and ND bars a modified form, which a section split and a quoted span produce.

`FetchedText` gains an optional `license` field, and the adapter fills it with the license string that the OA service reported. `SourceDocument` cannot carry the license without a migration: the `source_documents` table in `0001_core.sql` has a fixed column list, and `Store.add_source_document` inserts every model field, so a new field on the record fails against the current schema. The license therefore stays out of the store. `IngestResult` carries it instead, which needs no migration, and a caller that wants the license reads it from the result of the ingestion that fetched the text.

## Consequences
Easier: the store holds only text that its license permits it to redistribute. The license of an accepted body is visible on the ingest result. The allow list is one constant, so a later decision about a further license is one edit plus a fixture.

Harder: every full text fetch costs one more request to the OA service, one per work. A work under a license that the allow list does not hold now ingests as abstract only, so the corpus holds fewer bodies than before, and a dossier over such a work rests on the abstract. The license is not queryable in SQL, because the store does not hold it. A migration that adds a `license` column to `source_documents` is the follow up if a report needs the license of a stored document.

## Alternatives considered
- **Read the license out of the JATS `permissions` element of the body.** Rejected: the adapter must fetch and hold the body to read it, which is the copy the license decides on. The OA service answers before the fetch.
- **Accept every license that PMC reports and record it.** Rejected: the store would keep bodies that their terms do not let it redistribute, and the record alone does not undo that.
- **Add the license column to `source_documents` now.** Rejected for this change: the migration widens the change beyond the ingest package and no reader needs the column yet. The consequences above name it as the follow up.
