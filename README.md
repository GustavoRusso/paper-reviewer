# Paper Reviewer

Paper Reviewer is your assistant to explore biomedical and life sciences topics.

It takes a **topic statement** and produces a **topic brief**—an introduction that explains what is currently known about that topic—grounded in scientific papers.

## Who it is for

Researchers, authors, or reviewers who want help framing a topic: turn a free-form topic statement into a cited topic brief, based on related papers.

## Terminology

- **Paper** — Any scientific article, published or not. In the app, an archived `Paper` is the durable bibliographic record created or reused during **Paper archiving**. Its public id is the uppercase DOI. Source-record and full-text completeness live on the paper as stored statuses (not a single paper-wide status).
- **External sources** — Predefined online providers used to look up related papers during **External sources ingestion**
- **Topic statement** — Free-form text from the researcher that first defines the topic to brief. Topic intake writes it on the **Topic scope**.
- **Topic scope** — Durable record of one topic you work on (`TopicScope`). Created by Topic intake with the topic statement. Aggregates phase results: topic facets, ingest activity for this topic, **References** from **References selection**, and the topic brief. `Paper` and `PaperBrief` are global and are not owned by the Topic scope.
- **Topic facet** — One named slice of concepts distilled from the topic statement during Topic analysis (`TopicFacet`). Stored in the database and related to the **Topic scope**. Used to get key terms for **Search external sources**, **Papers search**, and later writing.
- **Paper candidate** — A related paper found via an external source during **Search external sources**. It has a source fetch handle so **Paper Ingestion** can archive the paper and fill its source record, full text, and **paper brief**. Not a paper brief; not a bibliographic reference; not a **Reference**. Candidate shape and identity rules: [docs/specs/2.1-search-external-sources.md](docs/specs/2.1-search-external-sources.md).
- **Bibliographic reference** — A link from one paper’s bibliography to another paper. Distinct from a paper candidate and from a **Reference**.
- **Reference** — A durable link from one **Topic scope** to one ingested `Paper` selected for the topic brief. One Topic scope has many References; one Paper may be a Reference for many Topic scopes. Specs: [docs/specs/3.1-show-references.md](docs/specs/3.1-show-references.md), [docs/specs/3.2-add-reference.md](docs/specs/3.2-add-reference.md). Distinct from a **bibliographic reference** and from the UI caption **Reference id** (the Topic scope key).
- **Paper Ingestion** — Step group under **External sources ingestion** that archives candidates, fulfills metadata, generates paper briefs, and (later) indexes papers. Index: [docs/specs/2.2-paper-ingestion.md](docs/specs/2.2-paper-ingestion.md).
- **Paper archiving** — Paper Ingestion substep that creates a `Paper` in this system from each candidate, or reuses an existing `Paper` when that article is already stored. Spec: [docs/specs/2.2.1-paper-archiving.md](docs/specs/2.2.1-paper-archiving.md).
- **Fulfill papers metadata** — Paper Ingestion substep that fills two global paper aspects: **source record** (fuller publication details) and **full text** (article body when available). Spec: [docs/specs/2.2.2-fulfill-papers-metadata.md](docs/specs/2.2.2-fulfill-papers-metadata.md).
- **Paper brief** — The **result** artifact: a structured, topic-agnostic summary of one paper (`PaperBrief`). One brief per paper; reused in later topic-brief generations. Produced by **Generate paper brief**. Distinct from that ingest step.
- **Generate paper brief** — Paper Ingestion **substep** that creates **paper briefs** for papers that have full text. Spec: [docs/specs/2.2.3-generate-paper-brief.md](docs/specs/2.2.3-generate-paper-brief.md).
- **Paper indexing** — Planned Paper Ingestion substep that indexes an ingested paper so **Papers search** can find it in the local database. Spec: [docs/specs/2.2.4-paper-indexing.md](docs/specs/2.2.4-paper-indexing.md).
- **Papers search** — Capability that applies topic facets to the local ingested paper store (and later its index) to return `Paper`s. Used by **Add reference**. Spec: [docs/specs/papers-search.md](docs/specs/papers-search.md). Distinct from **Search external sources**.
- **References selection** — Phase that selects ingested papers as **References** for the **Topic scope**. Spec: [docs/specs/3-references-selection.md](docs/specs/3-references-selection.md).
- **Topic brief** — Cited summary that explains what is currently known about the topic
- **Topic brief generation** — The four-phase workflow below, run on a **Topic scope**. You can repeat a phase to refine its result.

## External sources

The first connected source is [PubMed](https://pubmed.ncbi.nlm.nih.gov/).

## Topic brief generation workflow

The workflow has four phases. Each phase has its own result. You can repeat a phase to refine that result without a full restart. After **Topic definition**, you choose which later phase to run. You can open **External sources ingestion**, **References selection**, or **Topic brief** without finishing the others.

### 1. Topic definition

- **Topic intake** — You declare a topic statement; the assistant creates a **Topic scope**. Spec: [docs/specs/1.1-topic-intake.md](docs/specs/1.1-topic-intake.md).
- **Topic analysis** — The assistant extracts key concepts as **topic facets** that clarify the statement’s scope and focus. Spec: [docs/specs/1.2-topic-analysis.md](docs/specs/1.2-topic-analysis.md).

**Result:** a list of **topic facets** stored on that **Topic scope**. The Topic scope page then offers the three later phases.

### 2. External sources ingestion

Landing: [docs/specs/2-external-sources-ingestion.md](docs/specs/2-external-sources-ingestion.md).

- **2.1 Search external sources** — The assistant uses topic facets to get key terms and searches **external sources** for papers that can be ingested. Spec: [docs/specs/2.1-search-external-sources.md](docs/specs/2.1-search-external-sources.md). This search is source discovery for ingest. It is not the search that feeds the topic brief.
- **2.2 Paper Ingestion** — For each found paper, the assistant runs this ingest process (group index: [docs/specs/2.2-paper-ingestion.md](docs/specs/2.2-paper-ingestion.md)):
  - **2.2.1 Paper archiving** — Creates a `Paper` or reuses one with the same source handle. Spec: [docs/specs/2.2.1-paper-archiving.md](docs/specs/2.2.1-paper-archiving.md).
  - **2.2.2 Fulfill papers metadata** — Fills the **source record** and then **full text** (for PubMed: EFetch, then PMC Cloud when a body text exists). Spec: [docs/specs/2.2.2-fulfill-papers-metadata.md](docs/specs/2.2.2-fulfill-papers-metadata.md).
  - **2.2.3 Generate paper brief** — Creates a **paper brief** (the result artifact), or reuses one that already exists. Spec: [docs/specs/2.2.3-generate-paper-brief.md](docs/specs/2.2.3-generate-paper-brief.md).
  - **2.2.4 Paper indexing** — Indexes the ingested paper for later **Papers search**. Spec: [docs/specs/2.2.4-paper-indexing.md](docs/specs/2.2.4-paper-indexing.md) (not built yet).

**Result:** papers in the local database (archived, metadata filled, paper brief present, indexed when that step exists). Ingest activity for this topic is recorded on the **Topic scope**. `Paper` and `PaperBrief` stay global.

### 3. References selection

Landing: [docs/specs/3-references-selection.md](docs/specs/3-references-selection.md) (not built yet).

- **3.1 Show references** — Lists papers already selected as **References** for this **Topic scope**. Spec: [docs/specs/3.1-show-references.md](docs/specs/3.1-show-references.md). Offers a link to Add reference.
- **3.2 Add reference** — Runs **Papers search** on the local ingested paper store, shows which hits are already References, and lets you add one paper or all search results as References. Spec: [docs/specs/3.2-add-reference.md](docs/specs/3.2-add-reference.md). Papers search: [docs/specs/papers-search.md](docs/specs/papers-search.md).

**Result:** the set of **References** on the **Topic scope** (inputs for the topic brief).

### 4. Topic brief

Landing: [docs/specs/4-topic-brief.md](docs/specs/4-topic-brief.md) (drafting not built yet).

The assistant drafts a cited introduction that explains what is currently known about the topic, scoping each citation to the claims made in the text.

**Result:** the cited **topic brief**, attached to the **Topic scope**.

## Getting started

1. Install host tools: [docs/host-requirements.md](docs/host-requirements.md)
2. Copy [`.env.example`](.env.example) to `.env` and set local values there first (ports, Postgres, Prefect URLs, optional `NCBI_API_KEY`). Variable list and rules: [docs/local-development.md](docs/local-development.md#environment-configuration). PubMed key notes: [docs/specs/external-sources/pubmed.md](docs/specs/external-sources/pubmed.md).
3. Run the stack with `just up`: [docs/local-development.md](docs/local-development.md)
4. Open the services listed below (start on Home to see existing **Topic scopes**, or start Topic intake)

## Services

After `just up`, these services are available:

| Service | URL | Description |
| --- | --- | --- |
| Paper Reviewer UI | [http://localhost:8501](http://localhost:8501) (default `UI_PORT`) | Streamlit UI; Home lists Topic scopes from the database (each row opens the Topic scope hub) and links to Topic intake |
| Prefect | [http://localhost:4200](http://localhost:4200) (default `PREFECT_PORT`) | Prefect API/UI (`prefect-server`); `prefect-worker` polls work pool `local-pool` for source-record, full-text, and later brief flows. Progress still from Postgres. |
| PostgreSQL | See [docs/local-development.md](docs/local-development.md#environment-configuration) | App relational database (port and credentials from `.env`) |
