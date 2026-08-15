# Paper Reviewer

Paper Reviewer is your assistant to explore biomedical and life sciences topics.

It takes a **topic statement** and produces a **topic brief**—an introduction that explains what is currently known about that topic—grounded in scientific papers.

## Who it is for

Researchers, authors, or reviewers who want help framing a topic: turn a free-form topic statement into a cited topic brief, based on related papers.

## Terminology

- **Paper** — Any scientific article, published or not. In the app, an archived `Paper` is the durable bibliographic record created or reused during **Paper archiving**. Its public id is the uppercase DOI. Source-record and full-text completeness live on the paper as stored statuses (not a single paper-wide status).
- **Paper sources** — Predefined online providers used to look up related papers for **Paper ingestion**
- **Topic statement** — Free-form text from the researcher that first defines the topic to brief. Topic intake writes it on the **Topic scope**.
- **Topic scope** — Durable record of one topic you work on (`TopicScope`). Created by Topic intake with the topic statement. Aggregates phase results: topic facets, ingest activity for this topic, confirmed papers from Paper search, and the topic brief. `Paper` and `PaperBrief` are global and are not owned by the Topic scope.
- **Topic facet** — One named slice of concepts distilled from the topic statement during Topic analysis (`TopicFacet`). Stored in the database and related to the **Topic scope**. Used to get key terms for related-paper search and later writing.
- **Paper candidate** — A related paper found via a paper source during **Related-paper search**. It has a source fetch handle so **Paper ingestion** can archive the paper and fill its source record, full text, and **paper brief**. Not a paper brief; not a bibliographic reference. Candidate shape and identity rules: [docs/specs/2.1-related-paper-search.md](docs/specs/2.1-related-paper-search.md).
- **Bibliographic reference** — A link from one paper’s bibliography to another paper. Distinct from a paper candidate.
- **Paper archiving** — Ingest step that creates a `Paper` in this system from each candidate, or reuses an existing `Paper` when that article is already stored. Spec: [docs/specs/05-paper-archiving.md](docs/specs/05-paper-archiving.md).
- **Fulfill papers metadata** — Ingest step that fills two global paper aspects: **source record** (fuller publication details) and **full text** (article body when available). Spec: [docs/specs/06-fulfill-papers-metadata.md](docs/specs/06-fulfill-papers-metadata.md).
- **Paper brief** — The **result** artifact: a structured, topic-agnostic summary of one paper (`PaperBrief`). One brief per paper; reused in later topic-brief generations. Produced by **Generate paper brief**. Distinct from that ingest step.
- **Generate paper brief** — Ingest **step** that creates **paper briefs** for papers that have full text. Spec: [docs/specs/07-generate-paper-brief.md](docs/specs/07-generate-paper-brief.md).
- **Paper indexing** — Planned ingest step that indexes an ingested paper so **Paper search** can find it in the local database. Details later.
- **Paper search** — Phase that searches only papers already ingested in the local database.
- **Retrieval triage** — After **Paper search**, you confirm which locally found papers continue to **Topic brief**. Spec: [docs/specs/04-retrieval-triage.md](docs/specs/04-retrieval-triage.md).
- **Topic brief** — Cited summary that explains what is currently known about the topic
- **Topic brief generation** — The four-phase workflow below, run on a **Topic scope**. You can repeat a phase to refine its result.

## Paper sources

The first connected source is [PubMed](https://pubmed.ncbi.nlm.nih.gov/).

## Topic brief generation workflow

The workflow has four phases. Each phase has its own result. You can repeat a phase to refine that result without a full restart. After **Topic definition**, you choose which later phase to run. You can open **Paper ingestion**, **Paper search**, or **Topic brief** without finishing the others.

### 1. Topic definition

- **Topic intake** — You declare a topic statement; the assistant creates a **Topic scope**. Spec: [docs/specs/1.1-topic-intake.md](docs/specs/1.1-topic-intake.md).
- **Topic analysis** — The assistant extracts key concepts as **topic facets** that clarify the statement’s scope and focus. Spec: [docs/specs/1.2-topic-analysis.md](docs/specs/1.2-topic-analysis.md).

**Result:** a list of **topic facets** stored on that **Topic scope**. The Topic scope page then offers the three later phases.

### 2. Paper ingestion

Landing: [docs/specs/2-paper-ingestion.md](docs/specs/2-paper-ingestion.md).

- **2.1 Related-paper search** — The assistant uses topic facets to get key terms and searches **paper sources** for papers that can be ingested. Spec: [docs/specs/2.1-related-paper-search.md](docs/specs/2.1-related-paper-search.md). This search is source discovery for ingest. It is not the search that feeds the topic brief.
- For each found paper, the assistant runs this ingest process:
  - **Paper archiving** — Creates a `Paper` or reuses one with the same source handle. Spec: [docs/specs/05-paper-archiving.md](docs/specs/05-paper-archiving.md).
  - **Fulfill papers metadata** — Fills the **source record** and then **full text** (for PubMed: EFetch, then PMC Cloud when a body text exists). Spec: [docs/specs/06-fulfill-papers-metadata.md](docs/specs/06-fulfill-papers-metadata.md).
  - **Generate paper brief** — Creates a **paper brief** (the result artifact), or reuses one that already exists. Spec: [docs/specs/07-generate-paper-brief.md](docs/specs/07-generate-paper-brief.md).
  - **Paper indexing** — Indexes the ingested paper for later **Paper search**. Details later.

**Result:** papers in the local database (archived, metadata filled, paper brief present, indexed when that step exists). Ingest activity for this topic is recorded on the **Topic scope**. `Paper` and `PaperBrief` stay global.

### 3. Paper search

Landing: [docs/specs/3-paper-search.md](docs/specs/3-paper-search.md) (local search not built yet).

- The assistant searches only papers already ingested in the local database.
- **Retrieval triage** — Today this confirm gate still follows related-paper search on the Paper ingestion path. Spec: [docs/specs/04-retrieval-triage.md](docs/specs/04-retrieval-triage.md). After local Paper search exists, triage belongs with that phase.

**Result:** a confirmed set of local papers for the topic brief, attached to the **Topic scope**.

### 4. Topic brief

Landing: [docs/specs/4-topic-brief.md](docs/specs/4-topic-brief.md) (drafting not built yet).

The assistant drafts a cited introduction that explains what is currently known about the topic, scoping each citation to the claims made in the text.

**Result:** the cited **topic brief**, attached to the **Topic scope**.

## Getting started

1. Install host tools: [docs/host-requirements.md](docs/host-requirements.md)
2. Copy [`.env.example`](.env.example) to `.env` and set local values there first (ports, Postgres, Prefect URLs, optional `NCBI_API_KEY`). Variable list and rules: [docs/local-development.md](docs/local-development.md#environment-configuration). PubMed key notes: [docs/specs/paper-sources/pubmed.md](docs/specs/paper-sources/pubmed.md).
3. Run the stack with `just up`: [docs/local-development.md](docs/local-development.md)
4. Open the services listed below (start on Home to see existing **Topic scopes**, or start Topic intake)

## Services

After `just up`, these services are available:

| Service | URL | Description |
| --- | --- | --- |
| Paper Reviewer UI | [http://localhost:8501](http://localhost:8501) (default `UI_PORT`) | Streamlit UI; Home lists Topic scopes from the database (each row opens the Topic scope hub) and links to Topic intake |
| Prefect | [http://localhost:4200](http://localhost:4200) (default `PREFECT_PORT`) | Prefect API/UI (`prefect-server`); `prefect-worker` polls work pool `local-pool` for source-record, full-text, and later brief flows. Progress still from Postgres. |
| PostgreSQL | See [docs/local-development.md](docs/local-development.md#environment-configuration) | App relational database (port and credentials from `.env`) |
