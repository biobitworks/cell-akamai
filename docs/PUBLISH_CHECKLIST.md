# GitHub launch and lane handoff

**STOP before Git:** The MagicPro `cell-akamai` directory previously inherited a parent repository with remote `BioComputingUP/MobiDB-lite`. That parent has unrelated staged/unstaged state. Gum Doctor should diagnose *read-only* before any isolation; preserve original index, history, files.

1. Confirm MagicPro `git -C /Users/byron/projects/active/cell-akamai rev-parse --show-toplevel` is **exactly** `/Users/byron/projects/active/cell-akamai`. Do not use `git add .` until this passes.
2. Create private `biobitworks/cell-akamai` using authenticated `gh repo create biobitworks/cell-akamai --private --source=. --remote=origin` only after an isolated repo exists and has been reviewed for protected data.
3. Create `lane/a-akamai-telemetry` from updated `main`. Add only `AGENTS.md`, `CLAUDE.md`, `.gitignore`, `.github/`, `docs/`, `schemas/`, `cell_akamai/`, `notebooks/`, `tests/`, `pyproject.toml`, `README.md` and the empty-source dashboard. **Never add `runs/` or notebook checkpoint outputs.**
4. Run `python -m pytest tests -q` and `jupyter nbconvert --to notebook --execute notebooks/11_replay_offline.ipynb --output /tmp/cell_akamai_replay.ipynb`; require pass.
5. Push branch, open PR to `main` with executed tests and FCO/FCG root state.
6. Open Lane A and Lane B Issues using `.github/ISSUE_TEMPLATE/`. Comment schema path and commit SHA on Lane B Issue so Claude can pull before final scientific handoff.
7. Merge only after contract and provenance review. The generated public dashboard must not include restricted inputs, passwords, or uploaded notebook contents.

Target upstream Akamai workshop: `https://github.com/akamai-developers/akamai-workshop-ai-inference` (record exact commit before importing artifacts).
