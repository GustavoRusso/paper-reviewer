# Topic brief (phase landing)

This document is the specification for the **Topic brief** phase landing in [README.md](../../README.md). v1 is a **shell**. Cited topic-brief drafting is not built yet.

**Independent phases:** the user may open this landing without running External sources ingestion or References selection. Do not add cross-phase gates in v1.

## Glossary

| Term | Meaning |
| --- | --- |
| **Topic brief** | Phase 4 result: a cited introduction that explains what is currently known about the topic, attached to the `TopicScope`. Distinct from a **paper brief**. |
| **Phase landing** | Hidden Streamlit page reached from the [Topic scope hub](1.2-topic-analysis.md#topic-scope-hub). |

## Scope

### In scope (current v1)

- Dedicated landing page with title **Topic brief**.
- Caption that Topic brief drafting is not built yet.
- Page_link back to **Topic scope** (pass `topic_scope_key`).
- LLM section list and system prompt: [`topic_brief_template.md`](../../src/paper_reviewer/topic_brief_generation/topic_brief/topic_brief_template.md) (see [Structured content](#structured-content-llm-output)).

### Out of scope (v1)

- Calling an LLM to draft the cited topic brief.
- Pydantic `TopicBriefContent` (or any schema that parses the template JSON).
- Citation scoping to claims (beyond the prompt rules in the template).
- Attaching a topic-brief artifact to `TopicScope`.
- Generate paper brief (ingest step) — [2.2.3-generate-paper-brief.md](2.2.3-generate-paper-brief.md).

## Streamlit UI (v1)

Module: `paper_reviewer.ui.topic_brief` with `render_topic_brief()`.

| Property | Value |
| --- | --- |
| `key` | `topic_brief` |
| `title` | Topic brief |
| `url_path` | `topic-brief` |
| `in_sidebar` | false ([ui-style.md](../ui-style.md)) |

### Page behavior

1. Require `topic_scope_key`. Missing key → empty state + page_link to **Topic intake** and **Topic scope**.
2. Show title **Topic brief** and a caption that drafting the cited topic brief is not built yet.
3. Page_link to **Topic scope**.

Entry from the hub: [Topic analysis](1.2-topic-analysis.md#topic-scope-hub).

## Structured content (LLM output)

A later drafting job will persist a structured object (not a single free-form blob as the only field). v1 sections are **topic-conditioned** (topic statement, facets, and selected References).

**Owner of section list and prompt text:** [`topic_brief_template.md`](../../src/paper_reviewer/topic_brief_generation/topic_brief/topic_brief_template.md) in `paper_reviewer.topic_brief_generation.topic_brief`. YAML front matter lists JSON field ids and required flags. The Markdown body is the LLM system prompt. Do not copy that outline into this spec, AGENTS.md, or a skill.

The template imitates a Nature Reviews Perspective (title, unstructured abstract, introduction, headed main text, concluding section, numbered citations, key points). It is not a Nature research Article. A later job will load that file as the system prompt and send the topic statement, facets, and selected References (bibliographic facts plus succeeded paper briefs when present) in the user message. Field ids on a future `TopicBriefContent` schema must match the template front matter.

Do **not** store a topic-agnostic paper summary here. Paper briefs stay on `PaperBrief` ([Generate paper brief](2.2.3-generate-paper-brief.md)).
