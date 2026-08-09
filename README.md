# Paper Reviewer

Paper Reviewer is your assistant to explore biomedical and life sciences topics.

It takes a **topic statement** and produces a **topic brief**—an introduction that explains what is currently known about that topic—grounded in scientific papers.

## Who it is for

Researchers, authors, or reviewers who want help framing a topic: turn a free-form topic statement into a cited topic brief, based on related papers.

## Terminology

- **Paper** — Any scientific article, published or not
- **Paper sources** — Predefined online providers used to look up related papers
- **Topic statement** — Free-form text from the researcher that first defines the topic to brief
- **Topic facet** — One named slice of concepts distilled from the topic statement during Topic analysis (`TopicFacet`). Used to drive related-paper search and later writing.
- **Paper candidate** — A related paper found via a paper source during search: triage summary plus a source fetch handle so later steps can reload paper data and build a **paper brief**. Not a paper brief; not a bibliographic reference. Identity prefers **DOI** when present; otherwise paper source id plus that source’s record id.
- **Bibliographic reference** — A link from one paper’s bibliography to another paper. Distinct from a paper candidate.
- **Paper brief** — Structured summary of a paper related to the topic
- **Topic brief** — Cited summary that explains what is currently known about the topic
- **Topic brief generation** — One end-to-end run of the workflow below (Topic intake through Topic brief). In the app this is a `TopicBriefGeneration` record that owns artifacts from each step.

## Paper Sources

The first connected source is [PubMed](https://pubmed.ncbi.nlm.nih.gov/).

## Topic brief generation workflow

1. **Topic intake** — You provide a topic statement that defines what to investigate.
2. **Topic analysis** — The assistant extracts key concepts as **topic facets** that clarify the statement’s scope and focus for search and writing.
3. **Related-paper search** — The assistant searches **paper sources** for related papers.
4. **Retrieval triage** — Search results are presented; you can discard papers that do not apply, refining the set before deeper analysis.
5. **Paper briefs** — For each retained paper, the assistant builds a paper brief from that paper’s abstract and metadata (title, journal, publication dates, authors, and references). Prefer **DOI** as the paper identity when present; otherwise use the paper source id plus that source’s record id (for example PubMed PMID).
6. **Topic brief** — The assistant drafts a cited introduction that explains what is currently known about the topic, scoping each citation to the claims made in the text.

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
| PostgreSQL | `localhost:5432` | App relational database (local-dev credentials in [docs/local-development.md](docs/local-development.md)) |
