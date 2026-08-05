# Paper Reviewer

Paper Reviewer is your assistant to explore biomedical and life sciences topics.

It takes a **research query** and produces a **topic brief**—an introduction that explains what is currently known about that topic—grounded in scientific papers.

## Who it is for

Researchers, authors, or reviewers who want help framing a topic: turn a free-form query into a cited topic brief, based on related papers.

## Terminology

- **Paper** — Any scientific article, published or not
- **Paper sources** — Predefined online providers used to look up related papers
- **Research query** — Free-form input that specifies what to investigate
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
2. Run the stack with `just`: [docs/local-development.md](docs/local-development.md)





