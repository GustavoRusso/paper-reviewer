# Paper Reviewer

Paper Reviewer is your assistant to explore biomedical and life sciences topics.

It takes a **topic statement** and produces a **topic brief**—an introduction that explains what is currently known about that topic—grounded in scientific papers.

## Who it is for

Researchers, authors, or reviewers who want help framing a topic: turn a free-form topic statement into a cited topic brief, based on related papers.

## Terminology

- **Paper** — Any scientific article, published or not. In the app, an archived `Paper` is the durable bibliographic record created or reused during **Paper archiving**. Its public id is the uppercase DOI.
- **Paper sources** — Predefined online providers used to look up related papers
- **Topic statement** — Free-form text from the researcher that first defines the topic to brief
- **Topic facet** — One named slice of concepts distilled from the topic statement during Topic analysis (`TopicFacet`). Used to drive related-paper search and later writing.
- **Paper candidate** — A related paper found via a paper source during search: triage summary plus a source fetch handle so later steps can archive the paper and later build a **paper brief**. Not a paper brief; not a bibliographic reference. Candidate shape and identity rules: [docs/specs/03-related-paper-search.md](docs/specs/03-related-paper-search.md).
- **Bibliographic reference** — A link from one paper’s bibliography to another paper. Distinct from a paper candidate.
- **Paper archiving** — Workflow step that creates a `Paper` in this system from each candidate, or reuses an existing `Paper` when that article is already stored. Spec: [docs/specs/05-paper-archiving.md](docs/specs/05-paper-archiving.md).
- **Paper brief** — The **result** artifact: a structured summary of one paper for the current topic (`PaperBrief`). Produced by **Paper briefs generation**. Distinct from that workflow step.
- **Paper briefs generation** — Workflow **step** that source-informs archived papers and creates their **paper briefs**. Spec: [docs/specs/06-paper-briefs-generation.md](docs/specs/06-paper-briefs-generation.md).
- **Topic brief** — Cited summary that explains what is currently known about the topic
- **Topic brief generation** — One end-to-end run of the workflow below (Topic intake through Topic brief). In the app this is a `TopicBriefGeneration` record that owns artifacts from each step.

## Paper sources

The first connected source is [PubMed](https://pubmed.ncbi.nlm.nih.gov/).

## Topic brief generation workflow

1. **Topic intake** — You provide a topic statement that defines what to investigate.
2. **Topic analysis** — The assistant extracts key concepts as **topic facets** that clarify the statement’s scope and focus for search and writing.
3. **Related-paper search** — The assistant searches **paper sources** for related papers.
4. **Retrieval triage** — Search results are presented; you confirm which papers continue before deeper analysis. Spec: [docs/specs/04-retrieval-triage.md](docs/specs/04-retrieval-triage.md).
5. **Paper archiving** — For each retained candidate, the assistant creates a `Paper` or reuses one with the same source handle. Spec: [docs/specs/05-paper-archiving.md](docs/specs/05-paper-archiving.md).

6. **Paper briefs generation** — Workflow step that, for each archived paper, source-informs the `Paper` (for PubMed: EFetch) and creates a **paper brief** (the result artifact). Spec: [docs/specs/06-paper-briefs-generation.md](docs/specs/06-paper-briefs-generation.md).

7. **Topic brief** — The assistant drafts a cited introduction that explains what is currently known about the topic, scoping each citation to the claims made in the text.

## Getting started

1. Install host tools: [docs/host-requirements.md](docs/host-requirements.md)
2. Run the stack with `just up`: [docs/local-development.md](docs/local-development.md)
3. Open the services listed below (start on the landing page, then create a **Topic brief**)

An optional NCBI API key is recommended for PubMed rate limits; see [docs/specs/paper-sources/pubmed.md](docs/specs/paper-sources/pubmed.md).

## Services

After `just up`, these services are available:

| Service | URL | Description |
| --- | --- | --- |
| Paper Reviewer UI | [http://localhost:8501](http://localhost:8501) | Streamlit UI; landing page links to create a new Topic brief (Topic intake) |
| PostgreSQL | See [docs/local-development.md](docs/local-development.md) | App relational database (port and local-dev credentials) |
