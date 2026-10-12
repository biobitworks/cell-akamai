# Cell-Akamai · Frozen ECA Concurrency Pilot (Orchestrator Lane)

- **Dataset**: 32 deterministic ECA next-row items, seed 50000–50031, 8 items per Wolfram rule (30,90,110,184); inputs only, SHA256 in `dataset/eca_pilot_manifest_v1.json`, NOT confirmatory or biological data.
- **Runner**: `tools/concurrency/run_concurrency.py` imports Claude's unmodified `lane_b/harness/run_lane_b.py` and drives bounded parallel items at concurrency 1/2/4/8; no oracle access; atomic per-cell answer hash commitment for later Claude scoring. Starts in `preview` mode, must pass `--execute` to contact endpoint.
- **Dashboard**: `tools/concurrency/serve_dashboard.py` serves sanitized cell aggregates via loopback, refreshes every 4s and exposes no raw replies.
- **Evidence index**: `docs/IMPORTED_EVIDENCE_INDEX.json` cites the operator-exported original Akamai runs and hash verification; archive bytes and secret-bearing telemetry were not committed.
- **Runbook**: `docs/EXECUTION_RUNBOOK.md`; **Claude handoff** `docs/CLAUDE_REVIEW_HANDOFF.md`.
- **Notebook**: `notebooks/40_concurrency_replay_dashboard.ipynb` reads the dataset and verified summary files, plots measured concurrency when available, and otherwise declares `NOT_TESTED`.
- **Tests**: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests`.

**Constraints:** benchmark without running the real endpoint cannot show inference improvement. `tokens/s²` remains null under concurrent item scheduling; project MMR and signed custody are not claimed. `B1` is Genesis-proxy, not canonical Genesis weights. This lane neither provisions Akamai GPU nor modifies Claude and Cursor's worktrees.
