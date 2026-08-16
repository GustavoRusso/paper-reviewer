# Papers search

This document owns the shared **Papers search** capability: apply topic facets for a `TopicScope` to the **local ingested paper store** and return a list of `Paper`s. It is not a workflow phase step number.

Primary consumer: [Add reference](3.2-add-reference.md) (References selection step 3.2). The search document and GIN index that this query reads: [Paper indexing](2.2.4-paper-indexing.md).

v1 query **behavior is not built yet**. The engine, searchable field, and query rules below are **locked** for implementation.

For the application runtime stack (PostgreSQL full-text search, SQLAlchemy, no extra search service), see [technology-stack.md](../technology-stack.md).

## Glossary

| Term | Meaning |
| --- | --- |
| **Papers search** | Capability that selects ingested `Paper`s from the local database using `TopicFacet`s (and related criteria derived from the Topic scope). Distinct from [Search external sources](2.1-search-external-sources.md), which discovers candidates on external providers. |
| **Reference** | Topic scope ↔ Paper link owned by References selection ([3.1](3.1-show-references.md) / [3.2](3.2-add-reference.md)). Papers search may *report* whether a hit is already a Reference; it does not create References. |
| **Keyword search term** | One string from `Paper.source_record.indexing.keywords`. Paper indexing stores those strings as tokens in `keywords_tsv`. This capability turns facet **concepts** into `tsquery` values and matches them against that column. |

## Scope

### In scope (current v1)

- Accept a `TopicScope` (or its key) and load persisted `TopicFacet` rows as search input.
- Query only papers already ingested in the local database, using the PostgreSQL full-text index owned by [Paper indexing](2.2.4-paper-indexing.md).
- Match v1 queries against `Paper.keywords_tsv` only (source: `source_record.indexing.keywords`).
- Return a list of durable `Paper` hits suitable for display and for attach in Add reference.
- When a Topic scope is supplied, optionally mark each hit as already a Reference for that scope or not yet.
- Fail-soft when there are no facets, no hits, or an empty search document (rules below).

### Out of scope

- Creating, updating, or deleting **References** (owned by [Add reference](3.2-add-reference.md)).
- Building or updating `keywords_tsv` / the GIN index (owned by [Paper indexing](2.2.4-paper-indexing.md)).
- Calling external sources / dlt extract ([Search external sources](2.1-search-external-sources.md)).
- Producing `PaperCandidate` rows or running Paper archiving.
- Streamlit page ownership (UI lives on Add reference; this spec owns the search behavior contract).
- Topic-brief drafting.
- Matching MeSH headings, title, abstract, or full text in v1.
- Ranking (`ts_rank` or equivalent) in v1 (result order is unspecified).
- Using `TopicFacet.synonyms` as extra query terms in v1.

## Relation to other searches

| Capability | Corpus | Output |
| --- | --- | --- |
| [Search external sources](2.1-search-external-sources.md) | External providers (e.g. PubMed) | `PaperCandidate`s for ingest |
| **Papers search** (this document) | Local ingested `Paper`s | `Paper`s for References selection |

Do not merge these two search paths in one module contract.

## Search engine (locked)

Use **PostgreSQL full-text search** (`tsvector` / `tsquery`, GIN). Config: **`simple`** (lowercase and tokenize; do not stem). Do not add Elasticsearch, OpenSearch, Meilisearch, Typesense, ParadeDB, or `sqlalchemy-searchable`.

Column, generated expression, and GIN index: [Paper indexing](2.2.4-paper-indexing.md). This document owns how facet text becomes a query against that column.

## Query rules (v1)

| Rule | Behavior |
| --- | --- |
| Input terms | Every non-blank string in `TopicFacet.concepts` for the Topic scope (all facets). Strip surrounding whitespace. Skip blank strings. |
| One concept | `plainto_tsquery('simple', concept)`. Do **not** use `to_tsquery` or SQLAlchemy `Column.match()` (those need `tsquery` syntax and break on ordinary phrases). |
| Combine concepts | OR (`tsquery || tsquery`). A paper matches when `keywords_tsv` matches **any** concept. |
| Combine facets | Same OR pool: flatten concepts from every facet; do not AND across facets in v1. |
| Match operator | `keywords_tsv @@ <tsquery>`. |
| No usable concepts | Return an empty hit list. Do not scan all papers. |
| Empty `keywords_tsv` / no source record | That paper does not match. |
| `already_referenced` | Optional per-hit flag when a Topic scope is in scope; does not change which papers match. |

Do not write raw SQL that uses `@@` / `plainto_tsquery` in Streamlit or in Add reference. Put the operator behind a SQLAlchemy helper on `Paper` or in the Papers search domain package; callers use `select(Paper).where(...)`.

## Intended inputs and outputs (product)

| Side | Contract |
| --- | --- |
| Input | `TopicScope` (facets from the database). Optional flags for consumers that need already-referenced markers. |
| Output | List of ingested `Paper`s (order unspecified in v1); optional per-hit `already_referenced` (or equivalent) when a Topic scope is in scope. |

## Tests

Unit tests use in-memory SQLite and **must not** require a live `tsvector` / GIN. Prefer compile checks against the PostgreSQL dialect (assert `plainto_tsquery` / `@@`) and behavior tests that stub the match helper. Do not emulate PostgreSQL FTS on SQLite. General TDD rules: [tdd.md](../tdd.md).

## Related

| Concern | Spec |
| --- | --- |
| Consumer UI / attach | [3.2-add-reference.md](3.2-add-reference.md) |
| List of current References | [3.1-show-references.md](3.1-show-references.md) |
| Phase landing | [3-references-selection.md](3-references-selection.md) |
| Search document / GIN | [2.2.4-paper-indexing.md](2.2.4-paper-indexing.md) |
| `source_record.indexing.keywords` shape | [2.2.2-fulfill-papers-metadata.md](2.2.2-fulfill-papers-metadata.md) |
| Facets | [1.2-topic-analysis.md](1.2-topic-analysis.md) |
| Stack (Postgres FTS, SQLAlchemy) | [technology-stack.md](../technology-stack.md) |
