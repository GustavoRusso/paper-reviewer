# External source: PubMed

Search criteria and API mapping for the **PubMed** external source (`source_id = pubmed`).

Used by the [Search external sources](../2.1-search-external-sources.md) workflow. This document does **not** define that workflow — only how generic search criteria become PubMed queries and how PubMed hits become `PaperCandidate` records.

Product: [PubMed](https://pubmed.ncbi.nlm.nih.gov/).

## Scope

| In scope | Out of scope |
| --- | --- |
| Mapping generic `SearchCriteria` facets to PubMed/Entrez queries | Orchestrating multiple external sources |
| ESearch + ESummary against `db=pubmed` | Creating durable `Paper` rows ([Paper archiving](../2.2.1-paper-archiving.md)) |
| Mapping DocSums to `PaperCandidate` (summary + source fetch handle) | Modeling `BibliographicReference` |
| EFetch request shape and XML → `Paper` field mapping for the source-record flow (owned with [Fulfill papers metadata](../2.2.2-fulfill-papers-metadata.md)) | Rich author entities; deferred EFetch elements listed in Fulfill papers metadata (except PMCID for Cloud enrichment) |
| PMC Cloud enrichment for the full-text flow (highest version `.txt`, HTTPS PDF URL, OA flag) | Storing PDF/XML bytes; Unpaywall; legacy PMC FTP / OA Web Service; LLM `PaperBrief` drafting ([Generate paper brief](../2.2.3-generate-paper-brief.md)) |
| `source_overrides.pubmed` for fixtures | Topic analysis (`TopicAnalysisResult`); converting that result into `SearchCriteria` (owned by search external sources / `paper_reviewer.topic_brief_generation.search_external_sources`) |

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
| **EFetch** | `efetch.fcgi` | Fuller record for the **source-record** flow after [Paper archiving](../2.2.1-paper-archiving.md); see [EFetch (source record)](#efetch-source-record) and [Fulfill papers metadata](../2.2.2-fulfill-papers-metadata.md) |
| **PMC Cloud** | AWS Open Data bucket `pmc-oa-opendata` (HTTPS) | Full-text flow after a succeeded source record; see [PMC Cloud enrichment](#pmc-cloud-enrichment) |

Recommended sequence per facet:

1. ESearch with `usehistory=y`.
2. ESummary via History server (`WebEnv`, `query_key`) or batched `id` lists.
3. Map each DocSum to a `PaperCandidate`.

### Operational constraints (NCBI API key and rate limits)

This document owns PubMed/NCBI operational detail (README links here).

- Prefer an NCBI **API key** (higher rate limits); include `api_key` on requests when configured.
- Without a key, E-utilities allow about 3 requests/sec; with a key, about 10/sec. Respect NCBI usage guidelines.
- When EFetch returns HTTP 429 / `API rate limit exceeded`, `inform_source_record` soft-retries with a random wait in `(0.5s, 2s)` and does not count that attempt toward the hard-failure budget — see [Fulfill papers metadata](../2.2.2-fulfill-papers-metadata.md) (in-run extract retries).
- URL-encode `term`; avoid raw spaces (use `+` or encoding).
- Boolean operators must be uppercase.
- Prefer History for large result sets instead of huge `id` lists on every call.
- ESearch `retmax` only truncates the `idlist` in the ESearch response; with `usehistory=y` the History set still holds **all** matching UIDs. ESummary via History **must** pass `retmax` (capped at **500** for JSON). Omitting it makes NCBI try to return the full History set and fail with a JSON `error` for large queries.

## DocSum → `PaperCandidate`

Maps DocSum fields onto the shared `PaperCandidate` contract owned by [search external sources](../2.1-search-external-sources.md). Do not invent extra candidate fields here.

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

[Paper archiving](../2.2.1-paper-archiving.md) maps candidate bibliographic fields into a durable `Paper` without calling EFetch.

Archived papers receive a source record and then full text later (**Fulfill papers metadata**) using EFetch (`inform_source_record`) and PMC Cloud (`inform_full_text`). Cross-source identity / Paper public id remains the DOI (required for candidates that survive search external sources merge).

Search external sources and Paper archiving do not call EFetch.

## EFetch (source record)

Used only by the [Fulfill papers metadata](../2.2.2-fulfill-papers-metadata.md) Prefect job `inform_source_record` when `Paper.source_id = pubmed` and `source_record_status` is `not_started` (or when `regenerate_paper` forces a re-fetch).

Implementation: a **dlt resource** in `paper_reviewer.ingest.pubmed` performs EFetch (one PMID per call in v1), parses XML, and yields a mapped row for the source-record job to write onto `Paper`. This is separate from the ESearch/ESummary search resource. Do not call PMC Cloud from this resource.

### Request

| Parameter | Value |
| --- | --- |
| Endpoint | `efetch.fcgi` |
| `db` | `pubmed` |
| `id` | `Paper.source_uid` (PMID); **v1: one PMID per EFetch call** (no comma-separated batch lists) |
| `retmode` | `xml` |
| `rettype` | omit (default full `PubmedArticle` XML) |
| `api_key` | Include when configured (same rate-limit rules as search) |

Base URL: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`

Official XML structure: [PubMed DTD (current year)](https://dtd.nlm.nih.gov/ncbi/pubmed/doc/out/250101/index.html). EFetch parameters: [E-utilities in-depth](https://ncbi.nlm.nih.gov/books/NBK25499/).

### XML → `Paper` mapping (v1)

Which logical groups land on `Paper` (as `source_record` JSONB plus typed promotes such as `pub_date` and `abstract_text`) is owned by [Fulfill papers metadata](../2.2.2-fulfill-papers-metadata.md). PubMed element sources:

| Logical group | Primary PubMed XML sources |
| --- | --- |
| Abstract | `Article/Abstract` (`AbstractText` + optional `Label` / `NlmCategory`), `CopyrightInformation`; `OtherAbstract` |
| Dates | `Journal/JournalIssue/PubDate`; `Article/ArticleDate`; `DateCompleted`; `DateRevised`; `PubmedData/History/PubMedPubDate` (`PubStatus`) |
| Journal detail | `Journal/ISSN`; `JournalIssue` volume/issue; `Pagination` / `MedlinePgn`; `ISOAbbreviation`; `MedlineJournalInfo` (`MedlineTA`, `Country`, `NlmUniqueID`, `ISSNLinking`) |
| Types / language | `PublicationTypeList`; `Language`; `Article/@PubModel`; `MedlineCitation/@Status`, `@Owner` |
| Indexing | `MeshHeadingList`; `KeywordList`; `ChemicalList`; `SupplMeshList`; `CitationSubset` |
| Funding | `GrantList`; `DataBankList` |
| COI / notes | `CoiStatement`; `GeneralNote` |
| PMCID (typed promote) | `PubmedData/ArticleIdList` / article ids with `IdType` / idtype `pmc` → typed `Paper.pmcid` (e.g. `PMC5334499`) for Cloud enrichment |

Do **not** map in v1 (deferred; see Fulfill papers metadata): other `ArticleIdList` / `OtherID` values beyond DOI+PMID handle and PMCID, `CommentsCorrectionsList`, cited references, rich `Author` structure (affiliations, ORCID), `VernacularTitle`, `InvestigatorList`, `GeneSymbolList`, `PersonalNameSubjectList`, `SpaceFlightMission`.

Flat `authors: list[str]` is **always refreshed** from `AuthorList` display names when those names are present on the EFetch record (first successful source-record write on the default path). Also promote `pub_date` / `abstract_text`, set `pmcid` when present, and write the full mapped object to `Paper.source_record` per [Fulfill papers metadata](../2.2.2-fulfill-papers-metadata.md). Do **not** run PMC Cloud inside the EFetch resource. Structured author entities are out of scope here.

### Idempotency

Default path: if `source_record_status` is not `not_started`, do not call EFetch. If `full_text_status` is not `not_started`, do not call PMC Cloud. `regenerate_paper` may force both. Behavior contract: [Fulfill papers metadata](../2.2.2-fulfill-papers-metadata.md).

## PMC Cloud enrichment

Used only by `inform_full_text` after `source_record_status = succeeded` for PubMed, when a PMCID was mapped. Status outcomes (`succeeded` / `unavailable` / `failed`) and column ownership: [Fulfill papers metadata](../2.2.2-fulfill-papers-metadata.md).

Implementation: a helper under `paper_reviewer.ingest.pubmed` (not Streamlit) talks to the **updated** PMC Cloud Service on AWS. Do **not** use legacy PMC FTP, the retiring OA Web Service API, or deprecated Cloud prefixes.

Official references:

| Resource | URL |
| --- | --- |
| PMC Cloud Service | https://pmc.ncbi.nlm.nih.gov/tools/cloud/ |
| Accessing PMC Article Datasets on AWS | https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/ |
| Bucket | `s3://pmc-oa-opendata` (anonymous HTTPS also available) |

### Resolution steps

1. Normalize PMCID from EFetch (ensure `PMC` prefix).
2. Discover article versions for that PMCID under the Cloud bucket (prefix `PMC{id}.`). Always select the **highest** numeric version (e.g. prefer `PMC11370360.2` over `.1`).
3. Load that version’s metadata JSON (Cloud metadata object / article JSON). Read at least: `is_pmc_openaccess`, `is_manuscript`, `text_url`, `pdf_url`, `license_code` (license stored only if useful for ops; compliance remains with operators — no v1 filter by license).
4. Set typed fields:
   - `pmcid`, `pmcid_version`
   - `is_open_access` ← `is_pmc_openaccess` (may be false for author manuscripts that still have `.txt`)
   - `pmc_article_url` ← `https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/`
5. If `text_url` is present: download the `.txt` body (JATS flatten) → `full_text_plain` when the body is **usable** (`strip()` is not empty). Persist `strip()` of the body. Empty, spaces-only, or newline-only body is the same as no `.txt`. Pull for Open Access Subset **and** Author Manuscript when Cloud returns usable text.
6. If `pdf_url` is present: store **HTTPS** form only in `open_access_pdf_url` (do not download bytes). Normalize `s3://pmc-oa-opendata/<key>` → `https://pmc-oa-opendata.s3.amazonaws.com/<key>`. Prefer a stable path suitable for a browser link; strip ephemeral query params such as `md5` unless required for access.
7. On no Cloud object, no `.txt`, or blank / whitespace-only `.txt` in steps 2–6: leave `full_text_plain` null; the full-text flow sets `full_text_status = unavailable`. On HTTP/parse error after in-run retries: leave `full_text_plain` null; the flow sets `failed`. Do **not** treat a Cloud miss or a blank `.txt` as source-record success (source record is already a separate flow). Do **not** convert HTTP/parse errors into `unavailable`.

Do **not** change `Paper.url` (PubMed). Search / ESummary path still ignores PMC ids except as ignored articleids today.

### Full-text status cases

| Case | Expected |
| --- | --- |
| No PMCID after source record | Do not call Cloud; `full_text_status = unavailable` |
| PMCID present but no Cloud version / no `.txt` | `full_text_status = unavailable`; `full_text_plain` null |
| Cloud `.txt` body empty or whitespace-only | Same as no `.txt`: `unavailable`; `full_text_plain` null |
| Cloud has usable `.txt` but no PDF | `full_text_status = succeeded`; stripped `full_text_plain` set; `open_access_pdf_url` null |
| Author manuscript, not OA, usable `.txt` present | `full_text_status = succeeded`; stripped `full_text_plain` set; `is_open_access=false` |
| Cloud HTTP / parse error after retries | `full_text_status = failed`; `full_text_plain` null |

## dlt resource

`paper_reviewer.ingest.pubmed` exposes a PubMed dlt source/resource that:

1. Accepts a facet (+ optional PubMed override).
2. Calls ESearch / ESummary as above.
3. Yields `PaperCandidate`-shaped rows for the search external sources merge step in `paper_reviewer.topic_brief_generation.search_external_sources` (see [2.1-search-external-sources.md](../2.1-search-external-sources.md)).

## Behavior notes

| Case | Expected |
| --- | --- |
| Zero ESearch hits | No candidates for that facet from PubMed |
| Missing DOI on DocSum | Mapper may emit `doi` null; [search external sources](../2.1-search-external-sources.md) **drops** that hit at merge so it never reaches [Paper archiving](../2.2.1-paper-archiving.md) |
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
| PMC Cloud Service | https://pmc.ncbi.nlm.nih.gov/tools/cloud/ | OA / AM dataset files on AWS |
| PMC Article Datasets on AWS | https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/ | HTTPS/S3 access, version prefixes, metadata JSON |
| Fulfill papers metadata (step) | [2.2.2-fulfill-papers-metadata.md](../2.2.2-fulfill-papers-metadata.md) | When to call EFetch / Cloud; which groups and enrichment columns store on `Paper` |
| Generate paper brief (step) | [2.2.3-generate-paper-brief.md](../2.2.3-generate-paper-brief.md) | How a global **paper brief** is created after full text `succeeded` |
