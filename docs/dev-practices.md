# Development practices

Shared repository practices for contributors and coding agents. Add new sections here as more practices land.

## File moves and renames

For any **tracked** file or directory move/rename, use host `git mv`:

```bash
git mv src/paper_reviewer/old_name.py src/paper_reviewer/new_name.py
```

- Agents must use the Shell tool for that. Do **not** use filesystem-only moves (`mv` / `Move-Item` / `ren`) or Delete + Write: those look like delete + add and weaken rename tracking.
- After `git mv`, update imports and other references in a separate edit step.
- Untracked or new files may use a normal filesystem move; then `git add` the new path if they should be tracked.
- If a tool already created a delete+add pair for a tracked rename, fix it with `git add -A` on both paths (or re-do with `git mv`) before commit so `git status` shows rename when similarity allows.
