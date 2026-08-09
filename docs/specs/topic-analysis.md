# Topic analysis

This document is the specification for step 2 of the Topic brief generation workflow in [README.md](../../README.md).

In this step, the system extracts key data from a **topic statement**. Later steps use that data to search papers and to write text.

## Glossary

| Term | Meaning |
| --- | --- |
| **`TopicFacet`** | One named slice distilled from the topic statement (`id`, `label`, `intent`, `concepts`, …). |
| **`TopicAnalysisResult`** | Pydantic wrapper with `facets: list[TopicFacet]` for one `TopicBriefGeneration`. |
| **`SearchCriteria`** | Related-paper search envelope: a `TopicAnalysisResult` plus optional `source_overrides`. Built in step 3, not here. |

## Topic brief generation

A **Topic brief generation** (`TopicBriefGeneration`) is one full workflow execution. It includes all steps in [README.md](../../README.md):

1. Topic intake
2. Topic analysis
3. Related-paper search
4. Retrieval triage
5. Paper briefs
6. Topic brief

This document specifies only step 2 (Topic analysis) for that `TopicBriefGeneration`.

Related-paper search wraps the analysis result in `SearchCriteria`. See [related-paper-search.md](related-paper-search.md).

For the technology stack, see [technology-stack.md](../technology-stack.md). That stack includes Pydantic schemas, SQLAlchemy persistence, and scispaCy for biomedical NER.

## Scope

### In scope

- Analyze the `topic_statement` text of an existing `TopicBriefGeneration`.
- Make a `TopicAnalysisResult` with one or more `TopicFacet` objects via scispaCy NER.
- Write each facet as a database row with a foreign key to that `TopicBriefGeneration`.
- If you analyze the same `TopicBriefGeneration` again, replace the facet rows for it.

### Out of scope

- Validation of Topic intake (step 1 of the same `TopicBriefGeneration` does that work).
- Build of a full `SearchCriteria` object with `source_overrides`.
- Other workflow steps (related-paper search, triage, paper briefs, topic brief).
- Analysis with an LLM.
- Analysis that uses a custom stopword or token heuristic as the primary method.
- Larger scispaCy models (`md`, `lg`, or specialty NER), unless a later change adopts them.
- A separate ORM table for `TopicAnalysisResult` (v1: in-memory/API aggregate of facet rows).

## Position in the workflow

```mermaid
flowchart TB
  subgraph tbg [TopicBriefGeneration]
    intake[1 Topic intake]
    analyze[2 Topic analysis]
    facets[Persisted TopicFacet rows]
    search[3 Related-paper search]
    later[4 and later steps]
    intake --> analyze
    analyze --> facets
    facets --> search
    search --> later
  end
```

1. **Topic intake** starts a `TopicBriefGeneration` and stores the `topic_statement`.
2. **Topic analysis** (this specification) operates on that `TopicBriefGeneration`. It reads the `topic_statement`. It extracts concepts. It makes facets. It writes the facets with a foreign key to the same `TopicBriefGeneration`.
3. **Related-paper search** and the later steps continue on the same `TopicBriefGeneration`. Those steps use the facets from this step (as a `TopicAnalysisResult`). In tests, you can also inject fixtures.

## Input

| Input | Required | Description |
| --- | --- | --- |
| `TopicBriefGeneration` | Yes | The workflow execution that owns this analysis. It must have a `topic_statement` that is not empty. |
| `topic_statement` | Yes | Free-form text that Topic intake already accepted for that `TopicBriefGeneration`. |

After you normalize the text, empty text or text that has only whitespace is not valid for analysis. Raise a `ValueError`.

Topic intake must reject empty statements. Topic analysis must also reject empty text after normalize.

## Analyzer: scispaCy

Use [scispaCy](https://allenai.github.io/scispacy/) with the **`en_core_sci_sm`** pipeline. That pipeline is the smallest full biomedical spaCy model.

| Rule | Behavior |
| --- | --- |
| Normalize | Remove leading and trailing whitespace. Collapse adjacent whitespace. Do this before NLP. |
| Model load | Load with `spacy.load("en_core_sci_sm")`. Keep the model in a process-level cache. For tests, you can inject an `nlp` object. |
| Primary concepts | Get unique entity surface forms from `doc.ents` in first-seen order. |
| Dedupe | Remove duplicates. Keep a stable order. Do not change case of display text only to remove duplicates. |
| Fallback | If `doc.ents` is empty, make one or more concepts from noun chunks or from important tokens that are not stopwords. Short statements must still yield a facet. |
| Validation | Each facet must validate as a Pydantic `TopicFacet`. The collection must validate as `TopicAnalysisResult`. |

Do not use an LLM as the primary method. Do not use a custom stopword tokenizer as the primary method.

## Output: `TopicAnalysisResult`

The contract is `paper_reviewer.schemas.search.TopicAnalysisResult`, which holds `facets: list[TopicFacet]`. Related-paper search uses the same models.

This step makes a **`TopicAnalysisResult`**. This step does not make a full `SearchCriteria`.

### v1 emission rules

Always make **one or more** facets. In v1, make exactly one facet with these values:

| Field | v1 value |
| --- | --- |
| `id` | `core-concepts` |
| `label` | `Core concepts` |
| `intent` | Narrow topical match from biomedical entities (you can use fixed wording) |
| `concepts` | List that is not empty. Get the list from NER. Use the fallback if NER finds no entities. |
| `synonyms` | `[]` |
| `filters` | `{}` |
| `date_from` / `date_to` | `null` |
| `retmax` | `null` |

Do not add other facets (for example `broad-concepts`) until a later revision of this specification defines when they occur.

### Example

Topic statement: `glioblastoma immunotherapy outcomes`

This is one possible result. The entity strings can change with the model. When you use the real model in tests, make sure that the concepts include the expected biomedical spans:

```json
{
  "facets": [
    {
      "id": "core-concepts",
      "label": "Core concepts",
      "intent": "Narrow topical match from biomedical entities",
      "concepts": ["glioblastoma", "immunotherapy"],
      "synonyms": [],
      "date_from": null,
      "date_to": null,
      "filters": {},
      "retmax": null
    }
  ]
}
```

In unit tests with an injected fake `nlp`, you can check for an exact `concepts` list. With the real model, make sure that known entity substrings occur in `concepts`. Make sure that the output validates as `TopicAnalysisResult`.

## Persistence

Write each facet as one row in a child table. The parent is the `TopicBriefGeneration` where Topic analysis operated. `TopicAnalysisResult` is the in-memory/API aggregate of those rows (no separate parent table in v1).

| Concern | Rule |
| --- | --- |
| Relationship | Each facet row has a foreign key to `topic_brief_generations.id`. |
| Columns | Map the Pydantic fields. Store the facet `id` as `facet_id` so it does not conflict with the primary key. Also store `label`, `intent`, `concepts`, `synonyms`, `date_from`, `date_to`, `filters`, `retmax`, row `id`, and `created_at`. |
| Round-trip | Convert between ORM and Pydantic `TopicFacet` with no loss of list or object fields. Reload rows for a `TopicBriefGeneration` into a `TopicAnalysisResult`. |
| Source of truth | After a successful analysis step, the database is the source of truth. The UI can show the data. The UI must not be the only copy. |

### Re-analysis

If you run Topic analysis again for the same `TopicBriefGeneration`, replace the facet rows for it. First remove the old rows. Then write the new rows. Do not add duplicate rows.

## Behavior

| Case | Expected result |
| --- | --- |
| Valid biomedical statement with entities | A `TopicAnalysisResult` with one or more facets. `concepts` is not empty. Concepts come from `ents`. |
| Valid statement with no NER hits | A `TopicAnalysisResult` with one or more facets. `concepts` come from the fallback rule. |
| Empty text or whitespace-only text | Raise an error. Do not write rows. |
| Second analysis of the same `TopicBriefGeneration` | Replace the previous facet rows. The row count must match the new analysis. |

## Orchestration boundary

| Responsibility | Owner |
| --- | --- |
| Change text into a `TopicAnalysisResult` | Analyzer (`analyze_topic_statement` or an equivalent function) |
| Analyze and write for a `TopicBriefGeneration` | Domain helper (`run_topic_analysis` or an equivalent function). The helper takes a database session and a `TopicBriefGeneration`. |
| When to start analysis | After a successful Topic intake on that `TopicBriefGeneration`. Use the same session or transaction when it is practical. Keep intake tests and analysis tests separate. |

The build of `SearchCriteria` (`topic_analysis` plus optional `source_overrides`) for paper-source extract is not part of this step. See [related-paper-search.md](related-paper-search.md).

## Testability

- Inject a fake spaCy `nlp` that returns controlled `ents`. Use this for unit tests that must be deterministic. Those tests do not need a model download.
- You can add an optional integration check with the real `en_core_sci_sm` model. Make sure that expected entity substrings occur in `concepts`.
- Write and reload through the foreign key relationship. Make sure that re-analysis replaces rows.
- Related-paper search must continue to accept injected `SearchCriteria` fixtures. Those tests do not need this step.

## Non-goals (v1)

Do not do this work in v1:

- Make PubMed `source_overrides` or MeSH-specific markup.
- Orchestrate analysis with Prefect.
- Use specialty NER models (for example `en_ner_bc5cdr_md`).
- Use facet ids other than `core-concepts`.
