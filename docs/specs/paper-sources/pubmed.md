# Paper source: PubMed

Search criteria and API mapping for the **PubMed** paper source (`source_id = pubmed`).

Used by the [Related-paper search](../related-paper-search.md) workflow. This document does **not** define that workflow — only how generic search criteria become PubMed queries and how PubMed hits become `PaperCandidate` records.

Product: [PubMed](https://pubmed.ncbi.nlm.nih.gov/).

## Scope

| In scope | Out of scope |
| --- | --- |
| Mapping generic `SearchCriteria` strategies to PubMed/Entrez queries | Orchestrating multiple paper sources |
| ESearch + ESummary against `db=pubmed` | EFetch / full abstract payloads for **paper briefs** |
| Mapping DocSums to `PaperCandidate` (summary + source fetch handle) | Modeling `BibliographicReference` |
| `source_overrides.pubmed` for fixtures | Query analysis that generates criteria |

## Source identity

| Field | Value |
| --- | --- |
| `source_id` | `pubmed` |
| Stable record id (`source_uid`) | PubMed PMID (string or numeric string) |
| Human URL pattern | `https://pubmed.ncbi.nlm.nih.gov/<pmid>/` |

## PubMed search criteria

For each generic strategy, the PubMed adapter builds (or accepts) an Entrez **`term`** string.

### From generic strategy fields

| Generic field | PubMed / Entrez mapping |
| --- | --- |
| `concepts` | Combined with `AND`; each concept searched in `[Title/Abstract]` unless also listed as MeSH (see below) |
| `synonyms` | Grouped with the related concept using `OR` inside parentheses |
| MeSH-oriented concepts | When a concept is known/intended as MeSH, use `[Mesh]` (or `[mh]`) — Query analysis or overrides may mark this; structured default may treat `filters.mesh_terms` as MeSH if present |
| `date_from` / `date_to` | Publication date via `[pdat]` range (e.g. `2018:2024[pdat]`) |
| `filters` | Only keys documented for PubMed (e.g. `mesh_terms`, `article_types` if added later); ignore unknown keys |
| `retmax` | Passed to ESearch as `retmax` |

Boolean operators in compiled queries must be **ALL CAPS** (`AND`, `OR`, `NOT`). Terms must be URL-encoded for HTTP calls.

### Hybrid override

If `source_overrides.pubmed` supplies a `raw_term` for a strategy id, use that Entrez `term` **as-is** and skip structured compilation for that strategy.

Suggested override shape (opaque to the workflow; defined here):

```json
{
  "strategies": {
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

1. For each concept, build a clause: `"concept"[Title/Abstract]` or `"concept"[Mesh]` when MeSH is indicated.
2. Fold synonyms into the concept clause with `OR`.
3. Join concept clauses with `AND`.
4. Append date range and supported filters with `AND`.
5. Result is the ESearch `term`.

## API approach

Use **NCBI E-utilities** with `db=pubmed`.

Base URL: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`

| Utility | Endpoint | Role in this source |
| --- | --- | --- |
| **ESearch** | `esearch.fcgi` | Compiled `term` → PMIDs (`usehistory=y`, `retmax`, optional `sort`) |
| **ESummary** | `esummary.fcgi` | DocSums for candidate summary fields (by ids or History `WebEnv` + `query_key`) |
| **EFetch** | `efetch.fcgi` | **Not used here** — later paper-brief construction from retained candidates |

Recommended sequence per strategy:

1. ESearch with `usehistory=y`.
2. ESummary via History server (`WebEnv`, `query_key`) or batched `id` lists.
3. Map each DocSum to a `PaperCandidate`.

### Operational constraints

- Prefer an NCBI **API key** (higher rate limits); include `api_key` on requests when configured.
- Respect NCBI usage guidelines (rate limits without/with key).
- URL-encode `term`; avoid raw spaces (use `+` or encoding).
- Boolean operators must be uppercase.
- Prefer History for large result sets instead of huge `id` lists on every call.

## DocSum → `PaperCandidate`

| `PaperCandidate` field | PubMed source |
| --- | --- |
| `source_id` | `"pubmed"` |
| `source_uid` | PMID |
| `doi` | DOI from DocSum article ids when present; else null |
| `title` | DocSum title |
| `authors` | DocSum author list |
| `journal` | DocSum source / full journal name when available |
| `published_year` / date | DocSum pubdate / epubdate |
| `url` | `https://pubmed.ncbi.nlm.nih.gov/<pmid>/` |
| `snippet` | Only if DocSum provides a usable short text; otherwise omit |
| `strategy_id` | Strategy id from `SearchCriteria` |

### Source fetch handle (later steps)

Retained candidates are fetched later (paper briefs) using:

- **Primary:** EFetch with `db=pubmed` and `id=<PMID>` (`source_uid`)
- **Cross-source identity:** DOI when present

Related-paper search does not call EFetch.

## dlt resource (intent)

Future `paper_reviewer.ingest` exposes a PubMed dlt source/resource that:

1. Accepts a strategy (+ optional PubMed override).
2. Calls ESearch / ESummary as above.
3. Yields `PaperCandidate`-shaped rows for the workflow merge step.

## Behavior notes

| Case | Expected |
| --- | --- |
| Zero ESearch hits | No candidates for that strategy from PubMed |
| Missing DOI on DocSum | `doi` null; `source_uid` (PMID) still valid for later EFetch |
| Rate limit / HTTP error | Surface error to workflow `source_runs`; workflow fail-soft applies |

## Fixture example

Generic criteria with PubMed raw override for a deterministic Entrez query:

```json
{
  "strategies": [
    {
      "id": "fixture-pubmed",
      "label": "Fixture PubMed",
      "concepts": ["asthma", "leukotrienes"],
      "retmax": 10
    }
  ],
  "source_overrides": {
    "pubmed": {
      "strategies": {
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
