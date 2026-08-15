# Web UI style (semantic controls)

This document owns **interaction semantics** and **visual intent** for the Paper Reviewer Streamlit UI. Feature step specs own **which** action exists on a page; this document owns **how** that action is presented.

Stack boundary (Streamlit is presentation only): [technology-stack.md](technology-stack.md).

Industry practice this follows: links navigate; buttons act; one look per intent ([GOV.UK Buttons](https://design-system.service.gov.uk/components/button/), [GOV.UK Links](https://design-system.service.gov.uk/styles/links/), [Nielsen Norman Group on links vs buttons](https://www.nngroup.com/articles/command-links/), [WAI APG Button](https://www.w3.org/WAI/ARIA/apg/patterns/button/)).

## Rules (must)

1. **Link = navigate only.** A control that only moves the user to another in-app page must be a link. It must **not** create, update, delete, or confirm app/session data as its primary effect.
2. **Button = change data (or commit an action).** A control that starts a mutation, confirmation, submit, cancel of an in-progress edit, or destructive action must be a button.
3. **One look per intent.** All controls of the same intent use the same Streamlit widget and `type` (see tables below). Do not invent a one-off style for a single page.
4. **Label matches job.** Button labels name the action (“Confirm…”, “Submit”, “Cancel”). Link labels name the destination (“Continue to Paper archiving”, “Go to Topic intake”). Do not label a mutating button like a navigation link.

## Control choice

| User intent | Control | Streamlit API |
| --- | --- | --- |
| Go to another **in-app** page | Navigation link | `st.page_link` |
| Open an **external** URL (external source, DOI, PMC, PDF) | Content link | Markdown / title link via `url` (or equivalent); not `st.page_link` |
| Commit / confirm / start work that changes data | Button (confirm intent) | `st.button` or `st.form_submit_button`, `type="primary"` |
| Ordinary non-destructive action (when not the page’s main commit) | Button (default intent) | `st.button` / `st.form_submit_button`, `type="secondary"` (default) |
| Back out / dismiss / cancel without committing | Button (cancel intent) | `st.button`, `type="tertiary"` |
| Delete or other irreversible harm | Button (danger intent) | `st.button` — see [Danger](#danger-destructive) |

### Do / do not

| Do | Do not |
| --- | --- |
| Use `st.page_link` for “Continue to …”, “Go to …” | Use `st.button` only to change pages |
| Use a primary button to submit a form, enqueue work, or confirm a selection | Use `st.page_link` to confirm, save, or enqueue |
| Keep one primary commit control per page section | Place two primary buttons side by side for competing commits |
| After a successful confirm, show a **separate** `st.page_link` to the next page | Combine “confirm + navigate” into one control when confirm must mutate first |

## Visual intents

Same intent → same style everywhere.

| Intent | Meaning | Look (goal) | Streamlit mapping (v1) |
| --- | --- | --- | --- |
| **Confirm / primary** | Positive commit: confirm, submit, start the main safe action | Strong filled **blue** (`primaryColor`) | `type="primary"` |
| **Default** | Secondary action that still changes something, or a quiet commit when primary is elsewhere | Standard button fill | `type="secondary"` (Streamlit default) |
| **Cancel** | Regret / back out: leave without committing | Low emphasis, muted (gray / plain) | `type="tertiary"` |
| **Danger** | Destructive or hard to undo | Colour that signals risk (**red**) | No native Streamlit `type`; see below |

### Danger (destructive)

Streamlit buttons expose only `primary` / `secondary` / `tertiary`. There is **no** built-in danger type.

Until the project adds a shared danger presentation (for example one approved `st.markdown` CSS block or a small UI helper):

- Prefer a **confirm dialog pattern** (second step) for irreversible deletes.
- Do **not** style danger as `type="primary"` (that reads as a safe commit).
- Do **not** invent per-page red CSS.
- When a shared danger style exists, document the single helper or CSS owner **here** and use only that.

v1 product flows today have no delete buttons; reserve danger for a future need.

## Forms

- Prefer `st.form` + `st.form_submit_button` when several fields must submit together.
- The submit control follows the same intents as buttons (`primary` for the main commit).
- A form submit is still a **button** (mutates / starts work), never a `st.page_link`.

## Sidebar and chrome

This section owns **which pages appear in the left Streamlit navigation**. Step specs own whether a given page opts in (`in_sidebar` on that page’s register table). They must not restate the global sidebar list.

- Streamlit `st.navigation` is the left chrome. Do not build a custom `st.sidebar` page list.
- **Default off.** Registering a page in `build_app_pages()` is required for routing and `st.page_link`. It does **not** put the page in the sidebar. `AppPage.in_sidebar` defaults to `False` → `st.Page(..., visibility="hidden")`. Hidden pages stay in `st.navigation` so they remain reachable by URL, `st.page_link`, and `st.switch_page` (Streamlit 1.61).
- **Opt-in.** Only pages with `in_sidebar=True` appear in the sidebar (`visibility="visible"`). A spec must set `in_sidebar: true` on that page’s register table, and `AppPage(in_sidebar=True)` in `paper_reviewer.ui.navigation`.
- **Current opt-in list (this order):** Home, Topic intake. Later Topic brief generation pages are registered but hidden; the user moves with in-page `st.page_link` (and Topic intake `st.switch_page` to Topic analysis — see below).
- In-page CTAs and empty-state “Go to …” targets still use `st.page_link` per this document.

## Phase chrome

Phase landings may show a **shared in-page header** on the landing and on every step of that phase: the phase title (`st.title`), a short phase description, and a progress stepper. When the Topic scope key is present, the header may also show the Reference id caption after the phase title.

- The stepper is **not** a second sidebar. Do not put it in `st.sidebar`. Do not use `st.tabs`, `st.pills`, or `st.segmented_control` to change pages.
- Other steps are `st.page_link`s (navigate only; pass `topic_scope_key`). Link labels name the destination (the step title).
- The **current** step is not a link. Mark it with a **Current** badge (`st.badge`). On the phase landing, no step is current.
- Step pages keep the step name after the shared header as `st.header` (smaller than the phase `st.title`).
- Do not invent per-page stepper CSS. First owner: External sources ingestion ([2-external-sources-ingestion.md](specs/2-external-sources-ingestion.md)). Later phases may reuse the same pattern with their own step list.

## Topic scope key in the URL

Workflow pages carry the current `TopicScope` key in a **URL query parameter**, not in Streamlit session state.

| Rule | Detail |
| --- | --- |
| Query key | `topic_scope_key` (UUID string) |
| Write | Topic intake Submit sets the param on the **Topic analysis** destination URL after a successful start (see [Topic intake switch to analysis](#topic-intake-switch-to-analysis)) |
| Read | Each workflow page parses the key from `st.query_params` for captions and prerequisite checks |
| Navigate | Every in-workflow `st.page_link` and `st.switch_page` must pass `query_params` with that key. If `query_params` is omitted, Streamlit **clears** existing query parameters and the Topic scope key is lost |
| Out of sidebar | Sidebar Home / Topic intake may clear the query string (Streamlit default). That is acceptable for starting a new Topic scope |

Helpers live in `paper_reviewer.ui.topic_scope_url`. They must read and write `topic_scope_key`. Use `workflow_page_link` and `workflow_switch_page` so navigation always passes `query_params`. Step specs link here; they must not restate the clear rule.

Session caches (`topic_statement`, search / archiving results, enqueue caches) stay in `st.session_state`. The URL key alone does **not** resume a Topic scope after the session is gone.

Identifier naming (`id` vs `key`): [dev-practices.md](dev-practices.md#identifier-naming-id-vs-key).

### Topic intake switch to analysis

ui-style normally uses a mutating Submit, then a **separate** `st.page_link` to the next page.

**Exception (Topic intake only):** after a successful persist, Topic intake must `st.switch_page` to **Topic analysis** so analysis can auto-run. Set `topic_scope_key` on the destination URL (must not drop the query). Do not use `switch_page` after Topic analysis (that page uses a page_link to the Topic scope hub).

## Mapping to current workflow pages

Illustrative only; step specs remain the behavior contract.

| Situation | Intent | Control |
| --- | --- | --- |
| Home → Topic intake | Navigate | `st.page_link` |
| Home Topic scope list → Topic scope hub | Navigate | `st.page_link` (label = topic statement; pass `topic_scope_key`) |
| Topic intake Submit | Confirm / primary | `st.form_submit_button(..., type="primary")` then `st.switch_page` to Topic analysis |
| Topic analysis → Topic scope hub | Navigate | `st.page_link` |
| Topic scope hub → External sources ingestion / Paper search / Topic brief | Navigate | `st.page_link` |
| External sources ingestion phase stepper → another ingest step | Navigate | `st.page_link` (current step is not a link) |
| External sources ingestion → Search external sources | Navigate | `st.page_link` |
| Search external sources → Paper archiving | Navigate | `st.page_link` |
| Empty-state “Go to …” | Navigate | `st.page_link` |
| Paper title → PubMed / PMC / PDF | Content link | URL on the paper, not `st.page_link` |
| Per-paper Regenerate (Fulfill papers metadata / Generate paper brief) | Default | `st.button("Regenerate", type="secondary")` |

## Theme

Colour tokens live in [`.streamlit/config.toml`](../.streamlit/config.toml) (repo root; Streamlit loads `$CWD/.streamlit/config.toml`). Light and Dark are both defined so the user can switch in the app Settings menu. Default mode is Light.

Do **not** copy these values into step specs. Change colours only here and in that TOML file.

| ui-style intent | Streamlit token | Light | Dark |
| --- | --- | --- | --- |
| Confirm / primary buttons | `primaryColor` | `#1d4ed8` | `#1f6feb` |
| Content links (paper titles, PMC, PDF) | `linkColor` | `#1d4ed8` | `#58a6ff` |
| Page background | `backgroundColor` | `#ffffff` | `#0d1117` |
| Widget / contrast fill | `secondaryBackgroundColor` | `#f6f8fa` | `#161b22` |
| Body text | `textColor` | `#1f2328` | `#e6edf3` |
| Danger / `st.error` | `redColor` | `#cf222e` | `#f85149` |
| Success / `st.success` | `greenColor` | `#1a7f37` | `#3fb950` |
| Muted / cancel-adjacent chrome | `grayColor` | `#656d76` | `#8b949e` |

`primaryColor` must stay dark enough for **white** label text on filled primary buttons (Streamlit always uses white there). Do not set `primaryColor` to red — red is reserved for danger and errors.

Tertiary/cancel buttons stay Streamlit `type="tertiary"`. This theme does not add a danger button type.

## What feature specs may say

Step specs under `docs/specs/` may name the control class (“primary confirm button”, “page link to …”). They must **not** redefine colours or invent a second style system. Link here instead.

## Out of scope

- Asserting widget chrome in tests ([tdd.md](tdd.md)).
- Non-Streamlit surfaces.
- Custom CSS or a shared danger-button helper (still reserved; see [Danger](#danger-destructive)).

## References (external)

| Topic | Reference |
| --- | --- |
| Button roles and variants | [GOV.UK Design System — Buttons](https://design-system.service.gov.uk/components/button/) |
| Link role | [GOV.UK Design System — Links](https://design-system.service.gov.uk/styles/links/) |
| Why link ≠ button | [Nielsen Norman Group — Command links / links vs buttons](https://www.nngroup.com/articles/command-links/) |
| Accessibility pattern | [WAI ARIA Authoring Practices — Button](https://www.w3.org/WAI/ARIA/apg/patterns/button/) |
| Streamlit API | [st.button](https://docs.streamlit.io/develop/api-reference/widgets/st.button), [st.page_link](https://docs.streamlit.io/develop/api-reference/widgets/st.page_link), [st.form_submit_button](https://docs.streamlit.io/develop/api-reference/execution-flow/st.form_submit_button) |
| Streamlit theming | [Theming](https://docs.streamlit.io/develop/concepts/configuration/theming), [Colors and borders](https://docs.streamlit.io/develop/concepts/configuration/theming-customize-colors-and-borders) |
