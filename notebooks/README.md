# Notebooks

These Jupyter notebooks run **inside Docker**, not on the host and not in the Cursor editor.

The host has no Python or Jupyter. If Cursor shows **Detecting kernels**, that is expected. Do not install a kernel on the laptop for this project.

## Start Jupyter Lab

1. Start Docker Desktop.
2. From the repository root:

```bash
just notebooks
```

3. Wait until the recipe prints the Jupyter URL.
4. Open [http://localhost:8888](http://localhost:8888) in a browser on the host (or the port in `JUPYTER_PORT` in `.env`).
5. Open the notebook under `notebooks/paper_brief_evaluation/`.

`just notebooks` starts the app stack (including Postgres) if it is not already up. Do **not** use `just sandbox` (no database). Do **not** run `docker compose` on the host by hand.

Stop Jupyter with the rest of the app stack:

```bash
just down
```

If the page does not load: `just status` and `just logs notebooks`.

Recipe and env details: [docs/local-development.md](../docs/local-development.md#offline-paper-brief-evaluation-notebooks).

## Notebooks here

| File | Step | Status |
| --- | --- | --- |
| [paper_brief_evaluation/01-build-corpus.ipynb](paper_brief_evaluation/01-build-corpus.ipynb) | Freeze full text from archived local Papers | Implemented |
| [paper_brief_evaluation/02-generate-briefs.ipynb](paper_brief_evaluation/02-generate-briefs.ipynb) | Generate briefs from the corpus | Implemented |
| [paper_brief_evaluation/03-evaluate-briefs.ipynb](paper_brief_evaluation/03-evaluate-briefs.ipynb) | Score those briefs and summarize generator token usage | Implemented |

Procedure, paths, and domain functions: [docs/specs/paper-brief-evaluation-offline.md](../docs/specs/paper-brief-evaluation-offline.md).

Output (corpus and later run results) is written under `data/paper_brief_evaluation/` on the bind-mounted repo. Those files can be committed. They are not copied into the production image.
