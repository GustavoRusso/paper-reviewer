# Paper source: PubMed

Search criteria and API mapping for the **PubMed** paper source (`source_id = pubmed`).

Used by the [Related-paper search](../related-paper-search.md) workflow. This document does **not** define that workflow — only how generic search criteria become PubMed queries and how PubMed hits become `PaperCandidate` records.

Product: [PubMed](https://pubmed.ncbi.nlm.nih.gov/).

## Scope

| In scope | Out of scope |
| --- | --- |
| Mapping generic `SearchCriteria` facets to PubMed/Entrez queries | Orchestrating multiple paper sources |
| ESearch + ESummary against `db=pubmed` | EFetch / full abstract payloads for **paper briefs** |
| Mapping DocSums to `PaperCandidate` (summary + source fetch handle) | Modeling `BibliographicReference` |
| `source_overrides.pubmed` for fixtures | Topic analysis that generates criteria |

## Source identity

| Field | Value |
| --- | --- |
| `source_id` | `pubmed` |
| Stable record id (`source_uid`) | PubMed PMID (string or numeric string) |
| Human URL pattern | `https://pubmed.ncbi.nlm.nih.gov/<pmid>/` |

## PubMed search criteria

For each generic `TopicFacet`, the PubMed adapter builds (or accepts) an Entrez **`term`** string.

### From generic facet fields

| Generic field | PubMed / Entrez mapping |
| --- | --- |
| `concepts` | Combined with `AND`; each concept searched in `[Title/Abstract]` by default |
| `synonyms` | Grouped with the related concept using `OR` inside parentheses |
| MeSH (v1) | Topic analysis does **not** emit MeSH markup. Use `[Mesh]` (or `[mh]`) only for terms in `filters.mesh_terms`, or supply a full Entrez `term` via `source_overrides.pubmed` `raw_term` |
| `date_from` / `date_to` | Publication date via `[pdat]` range (e.g. `2018:2024[pdat]`) |
| `filters` | Only keys documented for PubMed (e.g. `mesh_terms`, `article_types` if added later); ignore unknown keys |
| `retmax` | Passed to ESearch as `retmax` |

Boolean operators in compiled queries must be **ALL CAPS** (`AND`, `OR`, `NOT`). Terms must be URL-encoded for HTTP calls.

### Hybrid override

If `source_overrides.pubmed` supplies a `raw_term` for a facet id, use that Entrez `term` **as-is** and skip structured compilation for that facet.

Suggested override shape (opaque to the workflow; defined here):

```json
{
  "facets": {
    "core-concepts": {
      "raw_term": "glioblastoma[mesh] AND immunotherapy[Title/Abstract] AND 2018:3000[pdat]",
      "retmax": 50,
      "sort": "relevance"
    }
  }
}
```

### Compilation sketch (structured path)

Illustrative only — exact quoting/escaping is an implementation concern:

1. For each concept, build a clause: `"concept"[Title/Abstract]`.
2. Fold synonyms into the concept clause with `OR`.
3. Join concept clauses with `AND`.
4. Append `filters.mesh_terms` (if any) as `[Mesh]` clauses, then date range and other supported filters, with `AND`.
5. Result is the ESearch `term`.

## API approach

Use **NCBI E-utilities** with `db=pubmed`.

Base URL: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`

| Utility | Endpoint | Role in this source |
| --- | --- | --- |
| **ESearch** | `esearch.fcgi` | Compiled `term` → PMIDs (`usehistory=y`, `retmax`, optional `sort`) |
| **ESummary** | `esummary.fcgi` | DocSums for candidate summary fields (by ids or History `WebEnv` + `query_key`) |
| **EFetch** | `efetch.fcgi` | **Not used here** — later paper-brief construction from retained candidates |

Recommended sequence per facet:

1. ESearch with `usehistory=y`.
2. ESummary via History server (`WebEnv`, `query_key`) or batched `id` lists.
3. Map each DocSum to a `PaperCandidate`.

### Operational constraints (NCBI API key and rate limits)

This document owns PubMed/NCBI operational detail (README links here).

- Prefer an NCBI **API key** (higher rate limits); include `api_key` on requests when configured.
- Without a key, E-utilities allow about 3 requests/sec; with a key, about 10/sec. Respect NCBI usage guidelines.
- URL-encode `term`; avoid raw spaces (use `+` or encoding).
- Boolean operators must be uppercase.
- Prefer History for large result sets instead of huge `id` lists on every call.
- ESearch `retmax` only truncates the `idlist` in the ESearch response; with `usehistory=y` the History set still holds **all** matching UIDs. ESummary via History **must** pass `retmax` (capped at **500** for JSON). Omitting it makes NCBI try to return the full History set and fail with a JSON `error` for large queries.

## DocSum → `PaperCandidate`

Maps DocSum fields onto the shared `PaperCandidate` contract owned by [related-paper-search.md](../related-paper-search.md). Do not invent extra candidate fields here.

| `PaperCandidate` field | PubMed source |
| --- | --- |
| `source_id` | `"pubmed"` |
| `source_uid` | PMID |
| `doi` | DOI from DocSum article ids when present; else null |
| `title` | DocSum title |
| `authors` | DocSum author list |
| `journal` | DocSum source / full journal name when available |
| `published_year` | Year parsed from DocSum pubdate / epubdate when available |
| `url` | `https://pubmed.ncbi.nlm.nih.gov/<pmid>/` |
| `snippet` | Only if DocSum provides a usable short text; otherwise omit |
| `facet_id` | Facet id from `SearchCriteria.topic_analysis` |

### Source fetch handle (later steps)

Retained candidates are fetched later (paper briefs) using:

- **Primary:** EFetch with `db=pubmed` and `id=<PMID>` (`source_uid`)
- **Cross-source identity:** DOI when present

Related-paper search does not call EFetch.

## dlt resource

`paper_reviewer.ingest.pubmed` exposes a PubMed dlt source/resource that:

1. Accepts a facet (+ optional PubMed override).
2. Calls ESearch / ESummary as above.
3. Yields `PaperCandidate`-shaped rows for the related-paper search merge step in `paper_reviewer.search`.

This step extracts candidates in memory for the workflow; it does not load them into Postgres.

## Behavior notes

| Case | Expected |
| --- | --- |
| Zero ESearch hits | No candidates for that facet from PubMed |
| Missing DOI on DocSum | `doi` null; `source_uid` (PMID) still valid for later EFetch |
| Rate limit / HTTP error | Surface error to workflow `source_runs`; workflow fail-soft applies |

## Fixture example

Generic criteria with PubMed raw override for a deterministic Entrez query:

```json
{
  "topic_analysis": {
    "facets": [
      {
        "id": "fixture-pubmed",
        "label": "Fixture PubMed",
        "concepts": ["asthma", "leukotrienes"],
        "retmax": 10
      }
    ]
  },
  "source_overrides": {
    "pubmed": {
      "facets": {
        "fixture-pubmed": {
          "raw_term": "asthma[mesh] AND leukotrienes[mesh] AND 2009[pdat]"
        }
      }
    }
  }
}
```

## API sources

Official docs for implementers and reviewers (prefer these over secondary blogs):

| Source | URL | Use for |
| --- | --- | --- |
| E-utilities hub | https://www.ncbi.nlm.nih.gov/books/NBK25501/ | Suite overview |
| General introduction | https://www.ncbi.nlm.nih.gov/books/NBK25497/ | Query syntax, History server, API keys / rate limits |
| Quick start | https://www.ncbi.nlm.nih.gov/books/NBK25500/ | Minimal ESearch / ESummary URL patterns |
| Parameters in depth | https://www.ncbi.nlm.nih.gov/books/NBK25499/ | `term`, `retmax`, `usehistory`, field tags |
| Sample applications | https://www.ncbi.nlm.nih.gov/books/NBK25498/ | ESearch → History → ESummary |
| Utility reference (NLM) | https://www.nlm.nih.gov/dataguide/eutilities/utilities.html | Per-utility parameters (PubMed-focused) |
| How E-utilities work (NLM) | https://dataguide.nlm.nih.gov/eutilities/how_eutilities_works.html | URL construction walkthrough |
| NCBI APIs index | https://www.ncbi.nlm.nih.gov/home/develop/api/ | Context vs other NCBI APIs |
| PubMed | https://pubmed.ncbi.nlm.nih.gov/ | Product UI |
