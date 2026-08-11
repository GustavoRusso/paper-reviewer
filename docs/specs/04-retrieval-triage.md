# Retrieval triage

This document is the specification for step 4 of the Topic brief generation workflow in [README.md](../../README.md).

In this step, the system presents **paper candidates** from [related-paper search](03-related-paper-search.md) for human review. The user confirms the set that continues to [Paper archiving](05-paper-archiving.md). In v1 every search candidate is retained; the step is a review gate with an explicit confirm action, not a filter.

## Glossary

| Term | Meaning |
| --- | --- |
| **`PaperCandidate`** | In-memory search hit from [related-paper search](03-related-paper-search.md). Shape owned by that spec. |
| **Retrieval triage** | Workflow step that reviews search candidates and produces a retained set for Paper archiving. |
| **Retained candidates** | The `list[PaperCandidate]` passed to Paper archiving after the user confirms triage. |

## Topic brief generation

A **Topic brief generation** (`TopicBriefGeneration`) is one full workflow execution (product steps in [README.md](../../README.md)). This document specifies only step 4 (Retrieval triage) for that run.

Paper archiving, **Complete papers data**, **Generate paper brief** (and its **paper brief** results), and topic brief drafting are out of scope here — see [Paper archiving](05-paper-archiving.md), [Complete papers data](06-complete-papers-data.md), [Generate paper brief](07-generate-paper-brief.md), and the later steps in the README.

For the application runtime stack, see [technology-stack.md](../technology-stack.md).

## Scope

### In scope (current v1)

- Accept the output of related-paper search for one `TopicBriefGeneration`.
- Present candidates for human review (title, authors, journal, year, url, source handle, facet).
- Require an explicit user action (button) to confirm and produce the retained set.
- Return a structured result for the orchestrator / next step.
- Pass through every input candidate unchanged (order preserved).

### Out of scope (v1)

- Per-paper manual discard or inclusion toggles (deferred to a later revision).
- DOI validation or rejection (owned by [related-paper search merge](03-related-paper-search.md); Paper archiving also skips blank DOI as defense-in-depth).
- Running Paper archiving on this page (owned by the dedicated [Paper archiving](05-paper-archiving.md) page).
- Creating **paper briefs** ([Generate paper brief](07-generate-paper-brief.md)) or topic brief construction.
- Persisting triage decisions to Postgres.
- Re-running related-paper search from the triage page.

## Position in the workflow

```mermaid
flowchart TB
  search[3 Related-paper search]
  triage[4 Retrieval triage]
  archive[5 Paper archiving]
  complete[6 Complete papers data]
  briefs[7 Generate paper brief]
  topic[8 Topic brief]
  search --> triage
  triage -->|"user confirms"| archive
  archive --> complete
  complete --> briefs
  briefs --> topic
```

1. **Related-paper search** produces a global `PaperCandidate` list (hits without DOI are already dropped; see that spec) plus `source_runs` metadata.
2. **Retrieval triage** (this specification) presents those candidates and waits for an explicit confirm. v1 retains every candidate.
3. **Paper archiving** receives `RetrievalTriageResult.retained` and creates or reuses `Paper` records.
4. **Complete papers data**, **Generate paper brief**, and **Topic brief** continue on archived papers — see [Complete papers data](06-complete-papers-data.md) and [Generate paper brief](07-generate-paper-brief.md).

Today, Topic intake runs analysis and search on one page. This step owns a **dedicated Streamlit page** for review and confirm. Intake remains responsible for starting the generation and running search; after search succeeds it links to triage.

## Input

| Input | Required | Description |
| --- | --- | --- |
| `search_result` | Yes | `RelatedPaperSearchResult` from [related-paper search](03-related-paper-search.md): `candidates`, `source_runs`, optional `notes`. |
| `generation_public_id` | Yes (UI) | Public id of the current `TopicBriefGeneration` (session / orchestrator context). Not an argument of the pure confirm function. |

`PaperCandidate` shape is owned by [related-paper search](03-related-paper-search.md). This step does not redefine it.

An empty `candidates` list is valid input.

## Public API

Package path (when implemented): `paper_reviewer.topic_brief_generation.retrieval_triage` — see [project-structure.md](../project-structure.md). Stub exists until implementation.

```text
confirm_retrieval_triage(search_result: RelatedPaperSearchResult) -> RetrievalTriageResult
```

| Rule | Behavior |
| --- | --- |
| Pure function | No database session. Caller owns later archiving commit. |
| Idempotent | Same input yields the same `retained` list. Safe to call again after confirm. |
| Empty candidates | Return `retained=[]`, `rejected=[]`. Do not raise. |
| Raise | Raise only on invalid input shape (Pydantic). |

Pydantic types live under `paper_reviewer.schemas.topic_brief_generation.retrieval_triage` (when implemented).

### Output

```text
RetrievalTriageResult
  retained: list[PaperCandidate]
  rejected: list[TriageRejection]
  confirmed_at: datetime | None
```

| Field | Description |
| --- | --- |
| `retained` | Candidates that continue to Paper archiving. |
| `rejected` | Candidates the user discarded. Reserved for future manual discard. |
| `confirmed_at` | Set when the user confirms via the UI. Null for programmatic / test pass-through. |

| v1 rule | Behavior |
| --- | --- |
| `retained` | Copy of all input `candidates`, preserving order (pass-through; same papers as search). |
| `rejected` | Always `[]`. |
| Empty input | `retained=[]`; UI still allows confirm (Paper archiving becomes a no-op success). |

Paper archiving still reads only `retained`, not the raw search list.

`TriageRejection` shape (when implemented for a later revision): enough identity to debug (`source_id`, `source_uid`, `doi` when known) plus a reason. Not used in v1.

## Streamlit UI

Dedicated page module (when implemented): `paper_reviewer.ui.retrieval_triage`.

Register in `paper_reviewer.ui.navigation`:

| Property | Value |
| --- | --- |
| `key` | `retrieval_triage` |
| `title` | Retrieval triage |
| `url_path` | `retrieval-triage` |

### Page behavior (v1)

1. **Prerequisites** — Require Streamlit session state from Topic intake:
   - `topic_brief_generation_public_id`
   - `related_paper_search_result`
   - If either is missing: show a message and a link to **New Topic brief**; do not render the confirm button.
2. **Context header** — Show the generation reference id and an optional topic statement snippet from session.
3. **Source runs** — Show per-source status from `search_result.source_runs` (same pattern as Topic intake’s per-source rendering today). Implementation may later extract a shared display helper.
4. **Candidate list** — One block per `PaperCandidate`: title (linked via `url`), authors, journal, year, `source_uid`, `facet_id`, and DOI when present.
5. **Counts** — Show how many papers will continue (e.g. “N papers to archive”).
6. **Primary button** — Label along the lines of **Continue to paper archiving** (exact copy left to implementation).
   - On click: call `confirm_retrieval_triage(search_result)`; store `RetrievalTriageResult` in session (`retrieval_triage_result`); clear `paper_archiving_result` so Paper archiving re-runs on the latest retained set; show a short success message and `st.page_link` to the **Paper archiving** page. Do **not** call `archive_papers` on this page.
7. **Empty candidates** — Still show source-run diagnostics; keep the confirm button enabled (archiving is a no-op). Caption explains that search returned no retainable papers.

### Topic intake handoff (when implemented)

After related-paper search succeeds on the Topic intake page:

- Do not keep the full candidate list as the primary triage surface on intake.
- Show a summary and an `st.page_link` to the **Retrieval triage** page as the required next step.

Persistence for v1 is Streamlit session state only (same pattern as topic analysis and search results today). No triage DB tables.

## Orchestration boundary

| Responsibility | Owner |
| --- | --- |
| Search, merge, drop no-DOI hits at merge | [related-paper search](03-related-paper-search.md) |
| User review + confirm gate; produce `retained` | Retrieval triage (this specification) |
| Create or reuse `Paper` rows from `retained` | [Paper archiving](05-paper-archiving.md) |
| `PaperCandidate` field shape | [related-paper search](03-related-paper-search.md) |
| Pydantic `RetrievalTriageResult` / confirm API | `paper_reviewer.schemas` / `paper_reviewer.topic_brief_generation.retrieval_triage` (when implemented) |
| Streamlit page and navigation | `paper_reviewer.ui` (when implemented) |

Paper archiving input is **`RetrievalTriageResult.retained`**, not the raw search list.

## Behavior

| Case | Expected |
| --- | --- |
| Search returned N candidates | Triage retains all N; UI lists all N. |
| Search returned 0 candidates | `retained=[]`; confirm allowed; Paper archiving empty success. |
| User opens triage without prior search | Guard message; no confirm button. |
| User confirms twice | Replace session triage result; clear `paper_archiving_result` so Paper archiving re-runs on the latest retained set. |
| Search had source errors (fail-soft) | Show `source_runs` errors; retain whatever candidates search produced. |

## Testability

When implementation starts (TDD per [tdd.md](../tdd.md)):

- `confirm_retrieval_triage` with a fixture `RelatedPaperSearchResult` → `retained` equals input `candidates`, `rejected=[]`.
- Empty `candidates` → empty `retained`, no raise.
- Optional UI tests: page guard without session keys; confirm button stores triage result (mirror patterns under `tests/ui/` when present).

## Non-goals (v1)

Do not do this work in the Retrieval triage v1 slice:

- Manual per-paper discard UI.
- DOI rejection or re-validation in triage.
- DB persistence of triage outcomes.
- Calling `archive_papers` or showing full Paper archiving results (owned by [Paper archiving](05-paper-archiving.md)).
- Re-running related-paper search from the triage page.
