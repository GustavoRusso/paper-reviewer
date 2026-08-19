# Paper Reviewer

Paper Reviewer is an assistant to explore biomedical and life sciences topics.

It takes a **topic statement** and produces a **topic brief**—an introduction that explains what is currently known about that topic—grounded in scientific papers.

## Who it is for

Researchers, authors, or reviewers who want help framing a topic by turning a free-form topic statement into a cited topic brief, based on related papers.

## Terminology

- **Paper** — Any scientific article, published or not. In the app, an archived `Paper` is the durable bibliographic record created or reused during **Paper archiving**. Its public ID is the uppercase DOI. Source-record and full-text completeness live on the paper as stored statuses (not a single paper-wide status).
- **External sources** — Predefined online providers used to look up related papers during **External sources ingestion**.
- **Topic statement** — Free-form text from the researcher that first defines the topic to brief. Topic intake writes it on the **Topic scope**.
- **Topic scope** — Durable record of one topic you work on (`TopicScope`). Created by Topic intake with the topic statement. Aggregates phase results: topic facets, ingest activity for this topic, **References** from **References selection**, and the topic brief. `Paper` and `PaperBrief` are global and are not owned by the Topic scope.
- **Topic facet** — One named slice of concepts distilled from the topic statement during Topic analysis (`TopicFacet`). Stored in the database and related to the **Topic scope**. Used to get key terms for **Search external sources**, **Papers search**, and later writing.
- **Paper candidate** — A related paper found via an external source during **Search external sources**. It has a source fetch handle so **Paper Ingestion** can archive the paper and fill its source record, full text, and **paper brief**. Not a paper brief; not a bibliographic reference; not a **Reference**. Candidate shape and identity rules: [docs/specs/2.1-search-external-sources.md](docs/specs/2.1-search-external-sources.md).
- **Bibliographic reference** — A link from one paper’s bibliography to another paper. Distinct from a paper candidate and from a **Reference**.
- **Reference** — A durable link from one **Topic scope** to one ingested `Paper` selected for the topic brief. One Topic scope has many References; one Paper may be a Reference for many Topic scopes. Specs: [docs/specs/3.1-show-references.md](docs/specs/3.1-show-references.md), [docs/specs/3.2-add-reference.md](docs/specs/3.2-add-reference.md). Distinct from a **bibliographic reference** and from the UI caption **Reference id** (the Topic scope key).
- **Paper Ingestion** — Step group under **External sources ingestion** that archives candidates, fulfills metadata, generates paper briefs, evaluates paper briefs, and indexes papers for **Papers search**. Index: [docs/specs/2.2-paper-ingestion.md](docs/specs/2.2-paper-ingestion.md).
- **Paper archiving** — Paper Ingestion substep that creates a `Paper` in this system from each candidate, or reuses an existing `Paper` when that article is already stored. The same page then runs ingest (source record, full text, paper brief, evaluation) for new papers. Spec: [docs/specs/2.2.1-paper-archiving.md](docs/specs/2.2.1-paper-archiving.md).
- **Fulfill papers metadata** — Paper Ingestion substep that fills two global paper aspects: **source record** (fuller publication details) and **full text** (article body when available). Spec: [docs/specs/2.2.2-fulfill-papers-metadata.md](docs/specs/2.2.2-fulfill-papers-metadata.md).
- **Paper brief** — The **result** artifact: a structured, topic-agnostic summary of one paper (`PaperBrief`). One brief per paper; reused in later topic-brief generations. Produced by **Generate paper brief**. Distinct from that ingest step.
- **Generate paper brief** — Paper Ingestion **substep** that creates **paper briefs** for papers that have full text. Spec: [docs/specs/2.2.3-generate-paper-brief.md](docs/specs/2.2.3-generate-paper-brief.md).
- **Paper brief evaluation** — Paper Ingestion substep that scores a succeeded **paper brief** with an LLM-as-judge against the paper’s full text. Spec: [docs/specs/2.2.4-paper-brief-evaluation.md](docs/specs/2.2.4-paper-brief-evaluation.md).
- **Paper indexing** — Paper Ingestion substep that keeps a local full-text search document on each ingested paper (v1: keywords from the source record) so **Papers search** can find it. Spec: [docs/specs/2.2.5-paper-indexing.md](docs/specs/2.2.5-paper-indexing.md).
- **Papers search** — Capability that applies topic facets to the local ingested paper store to return `Paper`s. Used by **Add reference**. Spec: [docs/specs/papers-search.md](docs/specs/papers-search.md). Distinct from **Search external sources**.
- **References selection** — Phase that selects ingested papers as **References** for the **Topic scope**. Spec: [docs/specs/3-references-selection.md](docs/specs/3-references-selection.md).
- **Topic brief** — Cited summary that explains what is currently known about the topic (`TopicBrief`). The **result** of phase 4; distinct from that phase’s name.
- **Topic brief generation** — Phase 4 of the **Topic scope workflow**: draft and store the cited **topic brief**. Spec: [docs/specs/4-topic-brief-generation.md](docs/specs/4-topic-brief-generation.md).
- **Topic scope workflow** — The four-phase workflow below, run on a **Topic scope**. You can repeat a phase to refine its result.



## External sources

The first connected source is [PubMed](https://pubmed.ncbi.nlm.nih.gov/).

## Topic scope workflow

The workflow has four phases. Each phase has its own result. You can repeat a phase to refine that result without a full restart. After **Topic definition**, you choose which later phase to run. You can open **External sources ingestion**, **References selection**, or **Topic brief generation** without finishing the others.

### 1. Topic definition

- **Topic intake** — You declare a topic statement; the assistant creates a **Topic scope**. Spec: [docs/specs/1.1-topic-intake.md](docs/specs/1.1-topic-intake.md).
- **Topic analysis** — The assistant extracts key concepts as **topic facets** that clarify the statement’s scope and focus. Spec: [docs/specs/1.2-topic-analysis.md](docs/specs/1.2-topic-analysis.md).

**Result:** a list of **topic facets** stored on that **Topic scope**. The Topic scope hub then offers the three later phases. Spec: [docs/specs/topic-scope-hub.md](docs/specs/topic-scope-hub.md).

### 2. External sources ingestion

Landing: [docs/specs/2-external-sources-ingestion.md](docs/specs/2-external-sources-ingestion.md).

- **2.1 Search external sources** — The assistant uses topic facets to get key terms and searches **external sources** for papers that can be ingested. Spec: [docs/specs/2.1-search-external-sources.md](docs/specs/2.1-search-external-sources.md). This search is source discovery for ingest. It is not the search that feeds the topic brief.
- **2.2 Paper Ingestion** — For each found paper, the assistant runs this ingest process (group index: [docs/specs/2.2-paper-ingestion.md](docs/specs/2.2-paper-ingestion.md)):
  - **2.2.1 Paper archiving** — Creates a `Paper` or reuses one with the same source handle, then enqueues ingest for new papers and shows progress. Spec: [docs/specs/2.2.1-paper-archiving.md](docs/specs/2.2.1-paper-archiving.md).
  - **2.2.2 Fulfill papers metadata** — Fills the **source record** and then **full text** (for PubMed: EFetch, then PMC Cloud when a body text exists). No dedicated page. Spec: [docs/specs/2.2.2-fulfill-papers-metadata.md](docs/specs/2.2.2-fulfill-papers-metadata.md).
  - **2.2.3 Generate paper brief** — Creates a **paper brief** (the result artifact), or rewrites one when `ingest_paper` runs. No dedicated page. Spec: [docs/specs/2.2.3-generate-paper-brief.md](docs/specs/2.2.3-generate-paper-brief.md).
  - **2.2.4 Paper brief evaluation** — Scores a succeeded paper brief with an LLM-as-judge (four G-Eval scores on the whole brief; overall mean on `PaperBrief`). Spec: [docs/specs/2.2.4-paper-brief-evaluation.md](docs/specs/2.2.4-paper-brief-evaluation.md).
  - **2.2.5 Paper indexing** — Keeps a local full-text search document on the ingested paper for **Papers search**. Spec: [docs/specs/2.2.5-paper-indexing.md](docs/specs/2.2.5-paper-indexing.md) (no page).

**Result:** papers in the local database (archived, metadata filled, with an LLM generated paper brief, searchable by **Papers search** when the keyword index exists). Ingest activity for this topic is recorded on the **Topic scope**. `Paper` and `PaperBrief` stay global.

### 3. References selection

Phase overview (docs-only; no landing page): [docs/specs/3-references-selection.md](docs/specs/3-references-selection.md). The [Topic scope hub](docs/specs/topic-scope-hub.md) opens **Show references**.

- **3.1 Show references** — Lists papers already selected as **References** for this **Topic scope**. Spec: [docs/specs/3.1-show-references.md](docs/specs/3.1-show-references.md). Offers a link to Add reference.
- **3.2 Add reference** — Runs **Papers search** on the local ingested paper store, shows which hits are already References, and lets you add one paper or all search results as References. Spec: [docs/specs/3.2-add-reference.md](docs/specs/3.2-add-reference.md). Papers search: [docs/specs/papers-search.md](docs/specs/papers-search.md).

**Result:** the set of **References** on the **Topic scope** (inputs for the topic brief).

### 4. Topic brief generation

Landing: [docs/specs/4-topic-brief-generation.md](docs/specs/4-topic-brief-generation.md).

The assistant drafts a cited introduction that explains what is currently known about the topic, with literal `[n]` markers in the prose and a numbered citation list (`DOI — title`). Generation needs at least one **Reference** with a succeeded **paper brief** (button disabled otherwise). The page offers **Generate topic brief** (overwrite-on-click); a Prefect job writes a `TopicBrief` from those briefed References.

**Result:** the cited **topic brief**, attached to the **Topic scope**.

## Getting started

1. Install host tools: [docs/host-requirements.md](docs/host-requirements.md)
2. Copy `[.env.example](.env.example)` to `.env` and set local values there first (ports, Postgres, Prefect URLs, optional `NCBI_API_KEY`). Variable list and rules: [docs/local-development.md](docs/local-development.md#environment-configuration). PubMed key notes: [docs/specs/external-sources/pubmed.md](docs/specs/external-sources/pubmed.md).
3. Choose how **paper brief** jobs call an LLM (see below), then run the stack with `just up`: [docs/local-development.md](docs/local-development.md)
4. Open the services listed below (start on Home to see existing **Topic scopes**, or start with Topic intake)



### LLM for paper briefs (OpenAI or local)

Paper brief generation (`create_paper_brief`), topic brief generation (`create_topic_brief`), and evaluation need a chat model. The default `.env.example` is preconfigured for the **local Ollama** runtime that ships with `just up`.

**Default — Local Ollama (no API key required)**

`just up` starts **Ollama** and automatically pulls `llama3.1:8b` and `gemma4:e4b` (first startup downloads several GB and can take a few minutes). The `.env.example` already contains the correct settings — no extra steps needed:

```bash
OPENAI_API_KEY=ollama
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama3.1:8b
```

Set `OPENAI_MODEL=gemma4:e4b` to use Gemma instead (recommended — see [Paper brief quality](#paper-brief-quality-offline-evaluation)). Confirm the models are ready: `curl http://localhost:11434/v1/models`. To re-pull both models manually: `just pull-model`. Details: [docs/local-development.md](docs/local-development.md#local-llm-ollama).

**NVIDIA GPU:** the Ollama service in [compose.yml](compose.yml) is set up for **NVIDIA** GPUs (Compose `deploy.resources.reservations.devices`). You need the NVIDIA Container Toolkit and a compatible driver on the host. If you do not have an NVIDIA card, comment out the GPU `deploy` block on `ollama` in [compose.yml](compose.yml) and expect slower CPU inference, or switch to the OpenAI API below.

**Alternative — OpenAI API (cloud)**

To use the public OpenAI API instead of local Ollama, change these three variables in `.env`:

```bash
OPENAI_API_KEY=sk-...        # your OpenAI key
OPENAI_BASE_URL=              # empty — routes to https://api.openai.com/v1
OPENAI_MODEL=                 # empty — defaults to gpt-4o-mini (or set a specific model)
```

Leave all three empty to skip live LLM drafts (jobs will be recorded as Failed).

## Paper brief quality (offline evaluation)

We measured paper-brief quality on a frozen corpus of **109 archived biomedical papers** (full text from local PubMed ingest). For each paper, a local LLM drafts a structured brief; the **same in-app judge** used in production ([2.2.4](docs/specs/2.2.4-paper-brief-evaluation.md)) scores the whole brief on four criteria — **faithfulness**, **completeness**, **conciseness**, and **topic-agnostic wording** — each 1–5. The overall score is the mean of those four (also 1–5). Scores are **advisory**; they do not block ingest or topic-brief generation.

We compared two local Ollama models ([notebook 04](notebooks/paper_brief_evaluation/04-compare-runs.ipynb); full procedure: [offline eval spec](docs/specs/paper-brief-evaluation-offline.md)):

- **gemma4:e4b** — mean **4.83** on 96 scored briefs; ~92% scored ≥ 4.5; no briefs ≤ 3.0.
- **llama3.1:8b** — mean **4.31** on 109 scored briefs; ~60% scored ≥ 4.5; 2 briefs scored 1.0 (judge flagged serious faithfulness problems).

**Conclusion:** both models produce generally usable briefs, but **gemma4:e4b is the better default** — higher quality with similar token cost (~3.1–3.3k tokens per brief). Llama is acceptable for local dev, but watch for rare bad summaries on data-heavy papers. To reproduce or compare new runs: `just notebooks` → run notebooks 01–04; results land under `data/paper_brief_evaluation/`.

## Services

After `just up`, these services are available:


| Service           | URL                                                                                  | Description                                                                                                                                           |
| ----------------- | ------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| Paper Reviewer UI | [http://localhost:8501](http://localhost:8501) (default `UI_PORT`)                   | Streamlit UI; Home lists Topic scopes from the database (each row opens the Topic scope hub) and links to Topic intake                                |
| Prefect           | [http://localhost:4200](http://localhost:4200) (default `PREFECT_PORT`)              | Prefect API/UI (`prefect-server`); `prefect-worker` serves the flows (`ingest_paper` at most 5 concurrent runs). Progress still from Postgres.        |
| PostgreSQL        | See [docs/local-development.md](docs/local-development.md#environment-configuration) | App relational database (port and credentials from `.env`)                                                                                            |
| Ollama            | [http://localhost:11434](http://localhost:11434)                                     | Local LLM runtime with OpenAI-compatible `/v1` API (`ollama`); models persist in Docker volume `ollama_data`. Default [compose.yml](compose.yml) targets NVIDIA GPUs. |




## LLM good-practices evaluation map

Paper Reviewer is an end-to-end LLM application: it ingests papers from PubMed, retrieves local ingested papers, then drafts a cited topic brief from selected References. This project aims to follow good practices for LLM projects, as defined in the [LLM Zoomcamp project evaluation criteria](https://github.com/DataTalksClub/llm-zoomcamp/blob/main/project.md):


| Criterion                            | Where defined                                                                                                                                                                         | Notes                                                                                                                                                                                                                                  |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Problem description                  | This README (intro + [Who it is for](#who-it-is-for))                                                                                                                                 |                                                                                                                                                                                                                                        |
| Retrieval flow                       | [docs/specs/papers-search.md](docs/specs/papers-search.md), [docs/specs/4-topic-brief-generation.md](docs/specs/4-topic-brief-generation.md)                                          | Use of **PostgreSQL full-text search** over a local knowledge base to generate the References that will be used by the LLM to generate the topic brief. Indexing is done during ingestion: [2.2.5](docs/specs/2.2.5-paper-indexing.md) |
| Retrieval evaluation                 | [docs/specs/papers-search.md](docs/specs/papers-search.md)                                                                                                                            | No retrieval evaluation was run.                                                                                                                                                                                                       |
| LLM evaluation                       | [docs/specs/2.2.4-paper-brief-evaluation.md](docs/specs/2.2.4-paper-brief-evaluation.md)[docs/specs/paper-brief-evaluation-offline.md](docs/specs/paper-brief-evaluation-offline.md) | Run an online evaluation on each generated paper brief. Run an offline evaluation using in-app G-Eval + offline judge runs. Offline results: [Paper brief quality](#paper-brief-quality-offline-evaluation)                                                                                                             |
| Interface                            | [docs/ui-style.md](docs/ui-style.md)[docs/specs/topic-scope-hub.md](docs/specs/topic-scope-hub.md)                                                                                   | Streamlit UI; default URL in [Services](#services)                                                                                                                                                                                     |
| Ingestion pipeline                   | [docs/specs/2.1-search-external-sources.md](docs/specs/2.1-search-external-sources.md)[docs/specs/2.2-paper-ingestion.md](docs/specs/2.2-paper-ingestion.md)                         | dlt extract + Prefect `ingest_paper`; stack: [technology-stack.md](docs/technology-stack.md)                                                                                                                                           |
| Monitoring                           | [docs/local-development.md](docs/local-development.md)                                                                                                                                | Prefect UI / worker only; No user-feedback or chart monitoring                                                                                                                                                                         |
| Containerization                     | [docs/host-requirements.md](docs/host-requirements.md)[docs/local-development.md](docs/local-development.md)                                                                         | Full app stack in `compose.yml` via `just`                                                                                                                                                                                             |
| Reproducibility                      | [Getting started](#getting-started), [docs/host-requirements.md](docs/host-requirements.md), [docs/local-development.md](docs/local-development.md)                                   | Versions in `pyproject.toml` / `uv.lock`                                                                                                                                                                                               |
| Hybrid search (best practice)        | [docs/specs/papers-search.md](docs/specs/papers-search.md)                                                                                                                            | v1 is PostgreSQL keyword FTS only; no vector search                                                                                                                                                                                    |
| Document re-ranking (best practice)  | [docs/specs/papers-search.md](docs/specs/papers-search.md)                                                                                                                            | Ranking is out of scope in v1                                                                                                                                                                                                          |
| User query rewriting (best practice) | [docs/specs/1.2-topic-analysis.md](docs/specs/1.2-topic-analysis.md)                                                                                                                  | Topic statement → facet concepts as search terms (NER; not an LLM query-rewrite step)                                                                                                                                                  |
| Deployment to the cloud (bonus)      | —                                                                                                                                                                                     |                                                                                                                                                                                                                                        |
| Extra bonus                          | —                                                                                                                                                                                     |                                                                                                                                                                                                                                        |


