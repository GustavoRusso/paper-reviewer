# Paper source: PubMed

Search criteria and API mapping for the **PubMed** paper source (`source_id = pubmed`).

Used by the [Related-paper search](../related-paper-search.md) workflow. This document does **not** define that workflow — only how generic search criteria become PubMed queries and how PubMed hits become `PaperCandidate` records.

Product: [PubMed](https://pubmed.ncbi.nlm.nih.gov/).

## Scope

| In scope | Out of scope |
| --- | --- |
| Mapping generic `SearchCriteria` facets to PubMed/Entrez queries | Orchestrating multiple paper sources |
| ESearch + ESummary against `db=pubmed` | Creating durable `Paper` rows ([Paper archiving](../paper-archiving.md)); LLM `PaperBrief` drafting ([Paper briefs](../paper-briefs.md)) |
| Mapping DocSums to `PaperCandidate` (summary + source fetch handle) | Modeling `BibliographicReference` |
| EFetch request shape and XML → `Paper` field mapping for source-inform (owned with [Paper briefs](../paper-briefs.md)) | Rich author entities; deferred EFetch elements listed in Paper briefs |
| `source_overrides.pubmed` for fixtures | Topic analysis (`TopicAnalysisResult`); converting that result into `SearchCriteria` (owned by related-paper search / `paper_reviewer.topic_brief_generation.related_paper_search`) |

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
| **EFetch** | `efetch.fcgi` | Fuller record for **source-inform** after [Paper archiving](../paper-archiving.md); see [EFetch (source-inform)](#efetch-source-inform) and [Paper briefs](../paper-briefs.md) |

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
| `authors` | DocSum `authors[].name` → `list[str]` (ESummary JSON objects with `name`, `authtype`, `clusterid`) |
| `journal` | DocSum source / full journal name when available |
| `published_year` | Year parsed from DocSum pubdate / epubdate when available |
| `url` | `https://pubmed.ncbi.nlm.nih.gov/<pmid>/` |
| `snippet` | Only if DocSum provides a usable short text; otherwise omit |
| `facet_id` | Facet id from `SearchCriteria.topic_analysis` |

### Source fetch handle (later steps)

[Paper archiving](../paper-archiving.md) maps candidate bibliographic fields into a durable `Paper` without calling EFetch.

Archived papers are source-informed later (**Paper briefs**) using EFetch (below). Cross-source identity / Paper public id remains the DOI (required for candidates that survive related-paper search merge).

Related-paper search and Paper archiving do not call EFetch.

## EFetch (source-inform)

Used only by the [Paper briefs](../paper-briefs.md) Prefect job `inform_paper_from_source` when `Paper.source_id = pubmed` and `source_informed_at` is null.

### Request

| Parameter | Value |
| --- | --- |
| Endpoint | `efetch.fcgi` |
| `db` | `pubmed` |
| `id` | `Paper.source_uid` (PMID); batch comma-separated ids when the job batches |
| `retmode` | `xml` |
| `rettype` | omit (default full `PubmedArticle` XML) |
| `api_key` | Include when configured (same rate-limit rules as search) |

Base URL: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`

Official XML structure: [PubMed DTD (current year)](https://dtd.nlm.nih.gov/ncbi/pubmed/doc/out/250101/index.html). EFetch parameters: [E-utilities in-depth](https://ncbi.nlm.nih.gov/books/NBK25499/).

### XML → `Paper` mapping (v1)

Which logical groups land on `Paper` is owned by [paper-briefs.md](../paper-briefs.md). PubMed element sources:

| Paper briefs group | Primary PubMed XML sources |
| --- | --- |
| Abstract | `Article/Abstract` (`AbstractText` + optional `Label` / `NlmCategory`), `CopyrightInformation`; `OtherAbstract` |
| Dates | `Journal/JournalIssue/PubDate`; `Article/ArticleDate`; `DateCompleted`; `DateRevised`; `PubmedData/History/PubMedPubDate` (`PubStatus`) |
| Journal detail | `Journal/ISSN`; `JournalIssue` volume/issue; `Pagination` / `MedlinePgn`; `ISOAbbreviation`; `MedlineJournalInfo` (`MedlineTA`, `Country`, `NlmUniqueID`, `ISSNLinking`) |
| Types / language | `PublicationTypeList`; `Language`; `Article/@PubModel`; `MedlineCitation/@Status`, `@Owner` |
| Indexing | `MeshHeadingList`; `KeywordList`; `ChemicalList`; `SupplMeshList`; `CitationSubset` |
| Funding | `GrantList`; `DataBankList` |
| COI / notes | `CoiStatement`; `GeneralNote` |

Do **not** map in v1 (deferred; see Paper briefs): `ArticleIdList` / `OtherID` beyond existing DOI+PMID handle, `CommentsCorrectionsList`, cited references, rich `Author` structure (affiliations, ORCID), `VernacularTitle`, `InvestigatorList`, `GeneSymbolList`, `PersonalNameSubjectList`, `SpaceFlightMission`.

Flat `authors: list[str]` may be refreshed from `AuthorList` display names only when informing; structured author entities are out of scope here.

### Idempotency

If `Paper.source_informed_at` is set, do not call EFetch for that paper. Behavior contract: [paper-briefs.md](../paper-briefs.md).

## dlt resource

`paper_reviewer.ingest.pubmed` exposes a PubMed dlt source/resource that:

1. Accepts a facet (+ optional PubMed override).
2. Calls ESearch / ESummary as above.
3. Yields `PaperCandidate`-shaped rows for the related-paper search merge step in `paper_reviewer.topic_brief_generation.related_paper_search` (see [related-paper-search.md](../related-paper-search.md)).

## Behavior notes

| Case | Expected |
| --- | --- |
| Zero ESearch hits | No candidates for that facet from PubMed |
| Missing DOI on DocSum | Mapper may emit `doi` null; [related-paper search](../related-paper-search.md) **drops** that hit at merge so it never reaches triage or [Paper archiving](../paper-archiving.md) |
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
| PubMed XML DTD (250101) | https://dtd.nlm.nih.gov/ncbi/pubmed/doc/out/250101/index.html | EFetch `PubmedArticle` element reference |
| Paper briefs workflow | [paper-briefs.md](../paper-briefs.md) | When to call EFetch; which groups store on `Paper` |
