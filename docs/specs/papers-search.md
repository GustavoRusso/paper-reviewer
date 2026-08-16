# Papers search

This document owns the shared **Papers search** capability: apply topic facets for a `TopicScope` to the **local ingested paper store** (and later its index) and return a list of `Paper`s. It is not a workflow phase step number.

Primary consumer: [Add reference](3.2-add-reference.md) (References selection step 3.2). Indexing that feeds this search: [Paper indexing](2.2.4-paper-indexing.md).

v1 is a **shell**. Local query behavior is not built yet.

## Glossary

| Term | Meaning |
| --- | --- |
| **Papers search** | Capability that selects ingested `Paper`s from the local database/index using `TopicFacet`s (and related criteria derived from the Topic scope). Distinct from [Search external sources](2.1-search-external-sources.md), which discovers candidates on external providers. |
| **Reference** | Topic scope ↔ Paper link owned by References selection ([3.1](3.1-show-references.md) / [3.2](3.2-add-reference.md)). Papers search may *report* whether a hit is already a Reference; it does not create References. |

## Scope

### In scope (current v1)

- Reserve the capability name and contract.
- Accept a `TopicScope` (or its key) and load persisted `TopicFacet` rows as search input.
- Query only papers already ingested in the local database (and, when [Paper indexing](2.2.4-paper-indexing.md) exists, the local index).
- Return a list of durable `Paper` hits suitable for display and for attach in Add reference.
- When a Topic scope is supplied, optionally mark each hit as already a Reference for that scope or not yet.
- Fail-soft documentation for empty index / no facets / no hits (implementation detail later).

### Out of scope

- Creating, updating, or deleting **References** (owned by [Add reference](3.2-add-reference.md)).
- Building or updating the search index (owned by [Paper indexing](2.2.4-paper-indexing.md)).
- Calling external sources / dlt extract ([Search external sources](2.1-search-external-sources.md)).
- Producing `PaperCandidate` rows or running Paper archiving.
- Streamlit page ownership (UI lives on Add reference; this spec owns the search behavior contract).
- Topic-brief drafting.

## Relation to other searches

| Capability | Corpus | Output |
| --- | --- | --- |
| [Search external sources](2.1-search-external-sources.md) | External providers (e.g. PubMed) | `PaperCandidate`s for ingest |
| **Papers search** (this document) | Local ingested `Paper`s | `Paper`s for References selection |

Do not merge these two search paths in one module contract.

## Intended inputs and outputs (product)

| Side | Contract |
| --- | --- |
| Input | `TopicScope` (facets from the database). Optional flags for consumers that need already-referenced markers. |
| Output | Ordered or unordered list of ingested `Paper`s; optional per-hit `already_referenced` (or equivalent) when a Topic scope is in scope. |

Exact ranking, query language, and index technology are deferred until Paper indexing and this capability are implemented.

## Related

| Concern | Spec |
| --- | --- |
| Consumer UI / attach | [3.2-add-reference.md](3.2-add-reference.md) |
| List of current References | [3.1-show-references.md](3.1-show-references.md) |
| Phase landing | [3-references-selection.md](3-references-selection.md) |
| Local index | [2.2.4-paper-indexing.md](2.2.4-paper-indexing.md) |
| Facets | [1.2-topic-analysis.md](1.2-topic-analysis.md) |
