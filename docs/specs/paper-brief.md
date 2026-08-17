# Paper brief

This document owns the shared **Paper brief** reader: load a succeeded global `PaperBrief` by DOI and show its structured content. When evaluation succeeded, the header also shows the overall `evaluation_score`. It is not a workflow phase step number.

Primary consumer: [Show references](3.1-show-references.md) (References selection step 3.1). Creation of the brief stays in [Generate paper brief](2.2.3-generate-paper-brief.md).

For the application runtime stack (Streamlit presentation, SQLAlchemy persistence), see [technology-stack.md](../technology-stack.md).

## Glossary

| Term | Meaning |
| --- | --- |
| **Paper brief** / **`PaperBrief`** | Global, topic-agnostic structured summary of one `Paper`. One row per paper. Product meaning: [README.md](../../README.md) Terminology. |
| **Paper brief page** | Hidden Streamlit page that shows one succeeded paper brief. Distinct from **Paper archiving**, which enqueues ingest and shows progress. |
| **DOI** | Public identity of the ingested `Paper`. Domain identifier, not a minted `key` ([dev-practices.md](../dev-practices.md#identifier-naming-id-vs-key)). |

## Scope

### In scope (current v1)

- Dedicated Streamlit page that shows one succeeded `PaperBrief` by DOI.
- Require query `doi` (strip surrounding whitespace; uppercase). Preserve `topic_scope_key` when present so Streamlit does not drop it ([ui-style.md](../ui-style.md#topic-scope-key-in-the-url)).
- Load with `load_paper_brief_for_read`. Do **not** put private `Paper.id` in the URL.
- Bibliographic header (title as a content link to `url`; caption `authors · journal · year · DOI`, em dash when authors/journal/year are missing). When evaluation succeeded, a second caption with the overall `evaluation_score` (two decimals, for example `evaluation 4.25`). Then `PaperBriefContent` sections.
- Skip empty optional content fields. List `key_findings` as bullets.
- Empty states: missing `doi`; paper not found; no succeeded brief; succeeded row with invalid JSON.
- Page_link **Go to Show references** when `topic_scope_key` is present.

### Out of scope (v1)

- Creating, rewriting, or enqueueing `PaperBrief` rows (owned by [Generate paper brief](2.2.3-generate-paper-brief.md)).
- Per-paper **Regenerate**.
- Add reference cards (those keep status badges; [3.2](3.2-add-reference.md)).
- Phase header/stepper (this page is not a workflow step).
- Topic-brief drafting ([Topic brief generation](4-topic-brief-generation.md)).
- The four G-Eval criterion scores, `evaluation_status`, or failed-evaluation errors (this page is for succeeded brief prose). The overall mean is in scope above; the judge job is [Paper brief evaluation](2.2.4-paper-brief-evaluation.md).

## Streamlit UI (v1)

Module: `paper_reviewer.ui.paper_brief` with `render_paper_brief()`.

| Property | Value |
| --- | --- |
| `key` | `paper_brief` |
| `title` | Paper brief |
| `url_path` | `paper-brief` |
| `in_sidebar` | false ([ui-style.md](../ui-style.md)) |

### Page behavior

1. `st.title` **Paper brief**. Do **not** show a phase header or stepper.
2. Parse `doi` from the URL. Missing or blank `doi` → empty-state caption; page_link **Go to Show references** when `topic_scope_key` is present.
3. Load with `load_paper_brief_for_read`.
4. When status is `ready`: title as a content link to `url`; bibliographic caption; when `evaluation_score` is set, a second caption with that mean to two decimals (same wording as [Paper archiving](2.2.1-paper-archiving.md), for example `evaluation 4.25`); then content sections in template field order. Skip optional fields that are empty. Show `key_findings` as a bullet list. Omit the evaluation line when the score is null.
5. When the paper is missing: empty-state caption that no ingested paper matches this DOI.
6. When there is no succeeded brief: empty-state caption that this paper has no succeeded paper brief yet.
7. When status is `succeeded` but stored JSON is invalid or missing: bibliographic header when the paper exists; warning that stored content could not be displayed.
8. Page_link **Go to Show references** when `topic_scope_key` is present (every outcome that still shows the page).

Entry from Show references: [3.1](3.1-show-references.md). URL query helpers: [ui-style.md](../ui-style.md#topic-scope-key-in-the-url).

## Public API

Package path: `paper_reviewer.topic_scope.paper_brief`.

```text
load_paper_brief_for_read(session, doi) -> PaperBriefRead
```

| Argument | Type | Role |
| --- | --- | --- |
| `session` | SQLAlchemy `Session` | Read. **Caller owns commit.** |
| `doi` | `str` | Already-normalized uppercase DOI. |

Schemas: `paper_reviewer.schemas.topic_scope.paper_brief`.

| Type | Fields |
| --- | --- |
| `PaperBriefReadStatus` | `ready`, `paper_missing`, `brief_unavailable`, `invalid_content`. |
| `PaperBriefRead` | `status`, `doi`, `title`, `url`, `authors`, `journal`, `published_year`, `content`, `evaluation_score`. Identity is `doi`. Do **not** put private `Paper.id` on the result. `content` is set only when `status` is `ready`. `evaluation_score` is set only when `evaluation_status` is `succeeded` and the score is stored; otherwise null. Do **not** put `evaluation_status` or the four criterion objects on this type. |

`brief_unavailable` covers no `PaperBrief` row and any status other than `succeeded`. `invalid_content` covers a `succeeded` row whose JSON is missing or does not validate as `PaperBriefContent`.

Bibliographic fields (`title`, `url`, `authors`, `journal`, `published_year`) are set when the `Paper` row exists. They are empty when `status` is `paper_missing`.

A missing or failed evaluation must **not** block reading the brief (`ready` still depends only on succeeded content).

Do not reuse `ReferencedPaper` (that type carries `referenced_at` and `paper_brief_available`).

## Related

| Concern | Spec |
| --- | --- |
| List of current References | [3.1-show-references.md](3.1-show-references.md) |
| Paper brief creation | [2.2.3-generate-paper-brief.md](2.2.3-generate-paper-brief.md) |
| Paper brief evaluation | [2.2.4-paper-brief-evaluation.md](2.2.4-paper-brief-evaluation.md) |
| Content fields / LLM prompt | [`paper_brief_template.md`](../../src/paper_reviewer/topic_scope/generate_paper_brief/paper_brief_template.md) |
| URL query (`topic_scope_key`, extra `doi`) | [ui-style.md](../ui-style.md#topic-scope-key-in-the-url) |
| Identifier naming | [dev-practices.md](../dev-practices.md#identifier-naming-id-vs-key) |
