# Paper Reviewer

Paper Reviewer is your assistant to explore biomedical and life sciences topics.

It takes a **research query** and produces a **topic brief**—an introduction that explains what is currently known about that topic—grounded in scientific papers.

## Who it is for

Researchers, authors, or reviewers who want help framing a topic: turn a free-form query into a cited topic brief, based on related papers.

## Terminology

- **Paper** — Any scientific article, published or not
- **Paper sources** — Predefined online providers used to look up related papers
- **Research query** — Free-form input that specifies what to investigate
- **Paper candidate** — A related paper found via a paper source during search: triage summary plus a source fetch handle so later steps can reload paper data and build a **paper brief**. Not a paper brief; not a bibliographic reference.
- **Bibliographic reference** — A link from one paper’s bibliography to another paper. Distinct from a paper candidate.
- **Paper brief** — Structured summary of a paper related to the topic
- **Topic brief** — Cited summary that explains what is currently known about the topic

## Paper Sources

The first connected source is [PubMed](https://pubmed.ncbi.nlm.nih.gov/).

## Topic brief generation workflow

1. **Query intake** — You provide a research query specifying what to investigate.
2. **Query analysis** — The assistant extracts key insights that clarify the query’s scope and focus for search and writing.
3. **Related-paper search** — The assistant searches **paper sources** for related papers.
4. **Retrieval triage** — Search results are presented; you can discard papers that do not apply, refining the set before deeper analysis.
5. **Paper briefs** — For each retained paper, the assistant builds a paper brief from that paper’s abstract and metadata (title, journal, publication dates, authors, and references). Each paper is identified by its **DOI**.
6. **Topic brief** — The assistant drafts a cited introduction that explains what is currently known about the topic, scoping each citation to the claims made in the text.

## Getting started

1. Install host tools: [docs/host-requirements.md](docs/host-requirements.md)
2. Run the stack with `just up`: [docs/local-development.md](docs/local-development.md)
3. Open the services listed below (start on the landing page, then create a **Topic brief**)

### Optional but recommended prerequisites:

Configure NCBI API key from NCBI account settings.
Without a key, E-utilities allow ~3 requests/sec; with a key, ~10/sec.
Pass it as api_key= — current code does not auto-read .dlt/secrets.toml



## Services

After `just up`, these services are available:

| Service | URL | Description |
| --- | --- | --- |
| Paper Reviewer UI | [http://localhost:8501](http://localhost:8501) | Streamlit UI; landing page links to create a new Topic brief (Query intake) |
| PostgreSQL | `localhost:5432` | App relational database (local-dev credentials in [docs/local-development.md](docs/local-development.md)) |
