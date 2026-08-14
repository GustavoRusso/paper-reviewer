# Paper Reviewer

Paper Reviewer is your assistant to explore biomedical and life sciences topics.

It takes a **topic statement** and produces a **topic brief**—an introduction that explains what is currently known about that topic—grounded in scientific papers.

## Who it is for

Researchers, authors, or reviewers who want help framing a topic: turn a free-form topic statement into a cited topic brief, based on related papers.

## Terminology

- **Paper** — Any scientific article, published or not. In the app, an archived `Paper` is the durable bibliographic record created or reused during **Paper archiving**. Its public id is the uppercase DOI. Source-record and full-text completeness live on the paper as stored statuses (not a single paper-wide status).
- **Paper sources** — Predefined online providers used to look up related papers
- **Topic statement** — Free-form text from the researcher that first defines the topic to brief
- **Topic facet** — One named slice of concepts distilled from the topic statement during Topic analysis (`TopicFacet`). Used to drive related-paper search and later writing.
- **Paper candidate** — A related paper found via a paper source during search: triage summary plus a source fetch handle so later steps can archive the paper and later fill its source record, full text, and **paper brief**. Not a paper brief; not a bibliographic reference. Candidate shape and identity rules: [docs/specs/03-related-paper-search.md](docs/specs/03-related-paper-search.md).
- **Bibliographic reference** — A link from one paper’s bibliography to another paper. Distinct from a paper candidate.
- **Paper archiving** — Workflow step that creates a `Paper` in this system from each candidate, or reuses an existing `Paper` when that article is already stored. Spec: [docs/specs/05-paper-archiving.md](docs/specs/05-paper-archiving.md).
- **Fulfill papers metadata** — Workflow step that fills two global paper aspects: **source record** (fuller publication details) and **full text** (article body when available). Spec: [docs/specs/06-fulfill-papers-metadata.md](docs/specs/06-fulfill-papers-metadata.md).
- **Paper brief** — The **result** artifact: a structured, topic-agnostic summary of one paper (`PaperBrief`). One brief per paper; reused in later topic-brief generations. Produced by **Generate paper brief**. Distinct from that workflow step.
- **Generate paper brief** — Workflow **step** that creates **paper briefs** for papers that have full text. Spec: [docs/specs/07-generate-paper-brief.md](docs/specs/07-generate-paper-brief.md).
- **Topic brief** — Cited summary that explains what is currently known about the topic
- **Topic brief generation** — One end-to-end run of the workflow below (Topic intake through Topic brief). In the app this is a `TopicBriefGeneration` record that owns artifacts from each step. `Paper` and `PaperBrief` are global and are not owned by that run.

## Paper sources

The first connected source is [PubMed](https://pubmed.ncbi.nlm.nih.gov/).

## Topic brief generation workflow

1. **Topic intake** — You provide a topic statement that defines what to investigate.
2. **Topic analysis** — The assistant extracts key concepts as **topic facets** that clarify the statement’s scope and focus for search and writing. Spec: [docs/specs/02-topic-analysis.md](docs/specs/02-topic-analysis.md).
3. **Related-paper search** — The assistant searches **paper sources** for related papers. Spec: [docs/specs/03-related-paper-search.md](docs/specs/03-related-paper-search.md).
4. **Retrieval triage** — Search results are presented; you confirm which papers continue before deeper analysis. Spec: [docs/specs/04-retrieval-triage.md](docs/specs/04-retrieval-triage.md).
5. **Paper archiving** — For each retained candidate, the assistant creates a `Paper` or reuses one with the same source handle. Spec: [docs/specs/05-paper-archiving.md](docs/specs/05-paper-archiving.md).
6. **Fulfill papers metadata** — For each archived paper, the assistant fills the **source record** and then **full text** (for PubMed: EFetch, then PMC Cloud when a body text exists). Spec: [docs/specs/06-fulfill-papers-metadata.md](docs/specs/06-fulfill-papers-metadata.md).
7. **Generate paper brief** — For each paper with full text, the assistant creates a **paper brief** (the result artifact), or reuses one that already exists. Spec: [docs/specs/07-generate-paper-brief.md](docs/specs/07-generate-paper-brief.md).
8. **Topic brief** — The assistant drafts a cited introduction that explains what is currently known about the topic, scoping each citation to the claims made in the text.

## Getting started

1. Install host tools: [docs/host-requirements.md](docs/host-requirements.md)
2. Copy [`.env.example`](.env.example) to `.env` and set local values there first (ports, Postgres, Prefect URLs, optional `NCBI_API_KEY`). Variable list and rules: [docs/local-development.md](docs/local-development.md#environment-configuration). PubMed key notes: [docs/specs/paper-sources/pubmed.md](docs/specs/paper-sources/pubmed.md).
3. Run the stack with `just up`: [docs/local-development.md](docs/local-development.md)
4. Open the services listed below (start on Home to see existing **Topic brief generations**, or create a new one)

## Services

After `just up`, these services are available:

| Service | URL | Description |
| --- | --- | --- |
| Paper Reviewer UI | [http://localhost:8501](http://localhost:8501) (default `UI_PORT`) | Streamlit UI; Home lists Topic brief generations from the database and links to create a new Topic brief |
| Prefect | [http://localhost:4200](http://localhost:4200) (default `PREFECT_PORT`) | Prefect API/UI (`prefect-server`); `prefect-worker` polls work pool `local-pool` for source-record, full-text, and later brief flows. Progress still from Postgres. |
| PostgreSQL | See [docs/local-development.md](docs/local-development.md#environment-configuration) | App relational database (port and credentials from `.env`) |
