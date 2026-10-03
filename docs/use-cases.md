# Use cases

Five things a person can do with the system, the command or route for each, and where each one stops. The example propositions come from plan sections 4 and 58. Each use case takes the side of the person who holds a question and wants the evidence for it.

The table holds two facts per use case. Built means the code exists and its tests pass, and every test runs on invented fixtures. Run on real papers means the step has run against real works.

| # | Use case | Command or route | Built | Run on real papers |
| --- | --- | --- | --- | --- |
| 1 | Test a hypothesis against stored claims | `search`, `POST /search/evidence` | Yes | Not yet |
| 2 | Trace a claim to its source passage | `claim`, `GET /claims/{claim_id}` | Yes | Not yet |
| 3 | Build a corpus from PubMed and arXiv | `ingest`, `extract` | Yes | Ingest yes, extract not yet |
| 4 | Score the pipeline against gold labels | `GET /evaluation` | Yes | No real gold set exists |
| 5 | Keep a dossier snapshot | `POST /dossiers`, `GET /dossiers/{dossier_id}` | Counts only | Not yet |

<!-- TODO(mvp 2.4): update the "Run on real papers" column and the limits of use case 3 after the live recording. -->

Every command runs from the repository root with the virtual environment from the README. The global option `--db` names the SQLite store, goes before the command, and defaults to `dossier.db`.

## 1. Test a hypothesis against stored claims

A researcher has a proposition and wants to know which stored claims support it, contradict it, or bear on it only in part.

```sh
.venv/bin/evidence-dossier --db dossier.db search "retrieval augmentation reduces factual hallucination compared with the same model without retrieval"
```

The API takes the same text. `POST /search/evidence` reads a JSON body with `text` and the optional fields `domain`, `source_level`, `dataset`, `system`, `population` and `limit`.

The result holds:

- The parsed proposition (subject, relationship, measurement, comparator) and the parse rules that fired.
- The claims, grouped in the order supports, contradicts, mixed, null, indirect, insufficiently comparable.
- For each claim: the stance and the reason for it, a comparability level with one reason per dimension, and the source passage with its section and character offsets.

The demo corpus covers two propositions, one computer science and one biology: the sentence above, and "tau reduction reduces amyloid pathology compared with control mice".

Limits:

- The parser is a table of rules (ADR 0006). A verb outside the table leaves the proposition without an expected direction, and every claim that is comparable enough to classify gets the stance indirect.
- Retrieval is lexical, on SQLite FTS5. Embeddings wait for a benchmark that shows retrieval failures (plan section 36).
- A stance is a rule result with a reason. It is not a probability.
- Only works in the store can appear. A paper that was never ingested and extracted has no claims to find.

## 2. Trace a claim to its source passage

A reviewer wants to see why the store holds a claim and where in the paper it comes from. A search prints each claim ID, which has the form `<document id>_c<n>`.

```sh
.venv/bin/evidence-dossier --db dossier.db claim work_8fc39e0ec1b6db48_v1_c1
```

The output holds the work (title, venue, date, identifiers), the study, the claim text, the subject, predicate and outcome, the research context, the method, the baseline, the metric with its unit, and the result (direction, value, p value, confidence interval, uncertainty, significance). It ends with the passage, which names the section and the character offsets and quotes the text, and with the extraction run: run ID, model identifier, prompt version and schema version.

`GET /claims/{claim_id}` returns the claim as JSON. `GET /works/{work_id}` returns a work with its links to other works and the IDs of its claims.

The offsets are checked. The text at those offsets equals the stored passage, and the store rejects a claim whose study or section belongs to another research work. The check establishes where a passage is. It does not establish that the scientific claim is true.

## 3. Build a corpus from PubMed and arXiv

Someone who wants a store for a topic ingests works and then extracts their claims. `ingest` prints the document ID that `extract` takes.

```sh
.venv/bin/evidence-dossier --db dossier.db ingest arxiv 2005.11401
.venv/bin/evidence-dossier --db dossier.db ingest pubmed 40734174
.venv/bin/evidence-dossier --db dossier.db extract --model sonnet work_8fc39e0ec1b6db48_v1
```

Ingestion:

- arXiv gives the abstract, at source level ABSTRACT_ONLY. The adapter has no full text path.
- PubMed gives the PMC full text when the article is in PMC open access under CC BY or CC0 (ADR 0009). Every other article gives the abstract.
- A full text fetch that fails falls back to the abstract and prints the error. A stored full text is never replaced by an abstract after a failed fetch.
- The same text stores nothing a second time. Changed text becomes the next version, so offsets into the earlier version stay valid.
- Requests are paced: 3 seconds between arXiv requests and about a third of a second between NCBI requests.

Extraction:

- `extract` runs the `claude` command line tool with no tools enabled, so the tool must be installed and logged in. The repository holds no API key.
- A reply that fails as a whole, or whose every claim fails, is stored as an INVALID run with its raw text and its errors. No claim from it is stored, and the command exits with status 1.
- A claim with an unknown field, an unknown study, a missing section or a quote that does not match the section text is rejected alone. The run is PARTIAL, the other claims are stored, each rejected claim keeps an error, and the command exits with status 1.
- A second extraction of the same document reports that an earlier extraction holds its IDs and stores nothing.

Limit: no live extraction has run, so no claim in a real store has come from a real reply.

## 4. Score the pipeline against gold labels

A maintainer wants to know how far the output can be trusted before a prompt or a rule changes.

```sh
.venv/bin/evidence-dossier --db dossier.db serve --gold path/to/gold
```

`GET http://127.0.0.1:8000/evaluation?split=dev` then returns the report as JSON, with the rendered report in a `markdown` field. A gold directory holds `documents/*.json` and, optionally, `retrievals.json`, `stances.json` and `notes.json`. Without `--gold` the route answers 404.

The report scores:

- Extraction fields, with micro and macro aggregates, and results by domain and by source level.
- Study relationships and evidence spans.
- Retrieval: Recall@5, Recall@10 and Precision@10.
- Stance: macro F1, per class results and a confusion matrix.
- Comparability.

It names the model, prompt version and schema version of the claims it scored, and it repeats the notes of the gold directory.

Limits:

- No real gold set exists. The gold directory in `tests/fixtures/evaluate` holds invented documents, and its predictions come from the same gold with deliberate errors. It checks the report arithmetic and measures nothing about the pipeline.
- A real gold set needs a human annotator who follows the [annotation guidelines](annotation-guidelines.md).
- The dev split serves prompt changes. The test split is for final numbers after the configuration is fixed (plan section 49).

## 5. Keep a dossier snapshot

A researcher wants a stored record of what a search returned, against which corpus, and when. With `serve` running:

```sh
curl -s -X POST http://127.0.0.1:8000/dossiers -H "content-type: application/json" -d '{"text": "retrieval augmentation reduces factual hallucination compared with the same model without retrieval"}'
```

The response has status 201 and holds the dossier and the search results. A dossier holds its ID, the query ID, the creation time, the corpus scope (the claim count of the store and the source levels in it) and the counts: claims, studies and works among the returned claims, and claims per stance. `GET /dossiers/{dossier_id}` returns a stored dossier with its proposition and stance assessments.

The counts keep claims, studies and works apart, so one paper with three claims counts as three claims and one work. No count is a probability that the proposition holds.

Not built (plan section 54): conflict pairs (`GET /conflicts` answers with an empty list and a note), research group clusters and diversity measures, evidence gap dimensions, and methodological reporting flags.

## Outside the MVP

- The experiment design evidence checker (plan section 55). It needs an evaluated query system first.
- A web interface. The API documentation page at `/docs` is the interface (plan section 48).
- Embedding based retrieval, until a benchmark shows retrieval failures.
- Sources beyond PubMed with PMC and arXiv.
