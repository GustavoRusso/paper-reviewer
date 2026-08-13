# Plan: paper aspect status and global brief

Apply the contract in [06-fulfill-papers-metadata.md](../specs/06-fulfill-papers-metadata.md) and [07-generate-paper-brief.md](../specs/07-generate-paper-brief.md).

Behavior lives in those specs. This file only sequences **implementation commits**. Do not treat this plan as a second behavior spec.

Each **step** below is one vertical slice ([dev-practices.md](../dev-practices.md)): UI or agreed outside edge through the layers that slice needs, TDD per [tdd.md](../tdd.md). Stop after each step. The human validates, then commits.

Do **not** start step N+1 in the same change as step N.

## Current code (before step 1)

- One Prefect flow `inform_paper_from_source` does EFetch then PMC Cloud.
- Progress uses `source_informed_at` / `source_inform_error_message`. Cloud miss still counts as inform success.
- `PaperBrief` and step 7 are specified but not implemented.

## Step 0 — Specs (this change)

**Already done in the docs commit that adds this plan.**

Validate: README terminology, spec 06/07, pubmed.md, and this plan match the locked contract (global brief, two `Paper` enums, full-text gate, force orchestrator only).

Commit when you accept the docs.

## Step 1 — Two statuses on Fulfill papers metadata

**Outside edge:** Fulfill papers metadata page.

**User-visible result:** Each archived paper shows **source record** status and **full text** status. Cloud miss is **Unavailable**, not success of a single fulfill marker. HTTP Cloud error is **Failed** on full text only.

**Includes (same commit):**

- `PaperAspectStatus` schema + ORM on `Paper` (`source_record_status`, `full_text_status`, per-aspect error messages).
- Alembic migration: add enums; map existing rows; drop `source_informed_at` and `source_inform_error_message`.
- Keep the current single Prefect deployment name for this step so Compose still works. The existing `inform_paper_from_source` job **writes both statuses** (EFetch → source record; Cloud → full text). Split into two flows in step 2.
- Page 6 progress table: two status columns; labels per spec 06.
- Update the step-6 smoke paragraph in [local-development.md](../local-development.md) so labels match the new columns. Keep the worker deployment name `inform_paper_from_source/default` until step 2.

**Migration map:**

| Old row | `source_record_status` | `full_text_status` |
| --- | --- | --- |
| `source_informed_at` set, `full_text_plain` set | `succeeded` | `succeeded` |
| `source_informed_at` set, `full_text_plain` null | `succeeded` | `unavailable` (old job always attempted Cloud after EFetch) |
| `source_inform_error_message` set, timestamp null | `failed` (copy message) | `not_started` |
| both null | `not_started` | `not_started` |

**Validate:**

- `just test` (narrow tests for this slice, then full suite).
- `just migrate` / `just up`. Open Fulfill papers metadata on a new archive: source record **Succeeded**; full text **Succeeded** or **Unavailable**.
- A paper that already had `source_informed_at` and no `full_text_plain` shows full text **Unavailable** after migrate.

**Do not in this step:** new flow names, `regenerate_paper`, `PaperBrief`, page 7.

### Step 1 spec grill (approved)

After Step 1 landed. Specs 06/07 stay the **target**. This plan did not rewrite them to name `inform_paper_from_source`. [local-development.md](../local-development.md) matches the running worker and labels.

The human **approved** these gaps as documented (no spec patch in the Step 1 commit). Later steps own the named follow-ups.

1. **Spec 06 vs running entry.** Spec names `inform_source_record` / `inform_full_text` / `fulfill_paper_metadata` and `skipped_already_terminal`. Code still uses `inform_paper_from_source` and `skipped_already_informed` / `skipped_already_failed`. **Unavailable** papers go in `skipped_already_failed` (wrong name). **Step 2** owns the rename and new entrypoints.
2. **Page 7 link.** Spec 06 wants `st.page_link` to **Generate paper brief** when both aspects are terminal. The page still has a caption only. Correct until **Step 3**. Do not pretend the link exists.
3. **`pmc_article_url` owner.** Spec 06 says Cloud writes `pmc_article_url`. Code still sets it from PMCID on source-record success, even when Cloud misses. Useful for the UI, but it is **not** what spec 06 says. Approved to **keep the derive rule**; a spec 06 patch can wait until Step 2 (when Cloud is its own flow) or a later docs pass.
4. **pubmed.md assumes split flows.** It says Cloud is only for `inform_full_text` and “do not treat a Cloud miss as source-record success.” Outcomes now match (two statuses). The **call path** is still one combined job. Leave pubmed.md as target. **Step 2** makes the call path match.
5. **No backfill in Step 1.** Spec 06 enqueues when source is `succeeded` and full text is `not_started`. This job still skips any source that is not `not_started`. Migrated “informed, no text” rows become full text `unavailable`, so they are not stuck as `not_started`. **Step 2** adds the backfill path.
6. **`InformOutcome.unavailable`** exists only for the combined job (unsupported source). Spec 06 aspect results do not use that combined outcome. Fine until **Step 2** deletes this type.

## Step 2 — Split source-record and full-text flows

**Outside edge:** Same page 6. Enqueue `fulfill_paper_metadata` (one run per paper) instead of the combined inform flow.

**User-visible result:** Default skip rules. A paper with source record already `succeeded` and full text `not_started` still runs Cloud (backfill). Page 6 does **not** retry `failed` / `unavailable` or overwrite `succeeded`.

**Includes (same commit):**

- Domain helpers `inform_source_record` and `inform_full_text`.
- Flows `inform_source_record`, `inform_full_text`, `fulfill_paper_metadata`.
- Worker `serve` + submit wiring; remove `inform_paper_from_source` as the page-6 entry (thin wrapper only if a short deprecation is required).
- Enqueue selection per spec 06.
- Update [local-development.md](../local-development.md) smoke text and worker deployment names to match the running code.

**Validate:**

- `just test` then `just up`. Worker serves `fulfill_paper_metadata` (and leaf flows if served).
- Revisit page 6 for a paper with source record `succeeded` and full text `not_started`: only full text runs.
- Revisit when both are terminal: no new runs.
- Unsupported `source_id`: source record **Unavailable**; full text stays **not_started**.

**Do not in this step:** `create_paper_brief`, `regenerate_paper`, page 7.

## Step 3 — Generate paper brief (global, full-text gate)

**Outside edge:** Generate paper brief page (register in navigation).

**User-visible result:** Page 7 enqueues briefs **only** for papers with `full_text_status = succeeded`. One global `PaperBrief` per `Paper`. A later generation that reuses the archived paper shows **Skipped (already done)** if the brief is already `succeeded`. Blocked rows for no full text. Content is topic-agnostic (no `relevance_to_topic`).

**Includes (same commit):**

- ORM `PaperBrief` (unique `paper_id`), migration, 1:1 from `Paper`.
- `create_paper_brief` domain + Prefect flow (`force=false` only from this page).
- Enqueue helper and progress UI per spec 07.
- LLM behind a stubbable boundary (no live LLM in tests).

**Validate:**

- `just test` then `just up`. Navigation shows **Generate paper brief**.
- Paper with full text **Unavailable**: blocked; no Prefect brief run.
- Paper with full text **Succeeded** and no brief: status moves to **Succeeded** (or **Failed** on LLM error).
- Second generation that archives the same paper: brief skipped.

**Do not in this step:** `regenerate_paper` or a force button.

## Step 4 — Force regenerate orchestrator

**Outside edge:** Prefect flow `regenerate_paper` (no v1 Streamlit page; agreed in spec 06).

**User-visible result:** On-demand run may unfreeze `succeeded` and retry `failed` / `unavailable`, then rewrite the brief if full text is `succeeded`.

**Includes (same commit):**

- `regenerate_paper` flow: force source record, force full text, then `create_paper_brief(..., force=true)` per spec.
- A documented way to submit one run (Prefect UI or a `just` recipe if one already fits; do not add a v1 page).
- Tests for force vs default skip.

**Validate:**

- Default page 6/7 still skip `succeeded` / `failed` / `unavailable`.
- After `regenerate_paper` on a paper with full text **Unavailable**, statuses may change; if full text becomes **Succeeded**, brief is rewritten.
- No new Streamlit control.

## After step 4

Topic brief (step 8) is a separate feature. It consumes succeeded global briefs and cites papers in prose (no relevance field on `PaperBrief`).

Later aspects (rich authors, extra full-text providers) follow spec 06 Future work: new enum + flow, or fold into `inform_full_text`.

## Rules for whoever implements a step

1. Read the spec sections for that step first; this plan does not repeat field lists.
2. Tests before production code at each layer of the slice.
3. Run `just test` before handing the step to the human.
4. Update [local-development.md](../local-development.md) in the same step that changes worker deployments or smoke steps.
5. Do not commit unless the human asks.
