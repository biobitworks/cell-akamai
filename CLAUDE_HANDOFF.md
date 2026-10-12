# Claude handoff — checkpoint001

Branch: lane/akamai-m08-m09-results-20261012
Verified remote checkpoint commit: b2a02922ad985af683e0867dacc450e6c7c53c31
Checkpoint: evidence/20261012/CHECKPOINT_001.json (path correction included in following commit).

Fetch this branch in an isolated worktree. Read docs/HOUR_SCALE_EXECUTION_PLAN.md. Frozen datasets must remain unchanged. Do not start a competing GPU benchmark.

Actual pilot dashboard: http://127.0.0.1:8766/ on operator Mac. Verified17 actual aggregate rows after full BF16 matrix import. Start tools/concurrency/serve_dashboard.py with --runs pointing at recovered/runs_fullmatrix/concurrency for a standalone16-cell view. Refresh polling requires no GPU restart.

BF16:16/16 pilot cells executed;128/128 items failed parsing/within-budget answer criteria. Independent scorer receipt is committed. Module07 corrected usage-token baseline completed separately. Module08 one-flag pilot executed; no improvement claim. Module09 agent port-forward failed; ECA execution continued, retained notebook failure. Hour-scale:0/184 cells completed, implementation and preflight pending.36 deterministic tests pass.

Next safe action: review aggregate receipts, finish hour-run admission/watchdog, verify actual hardware and idle state, restore max-num-seqs32 after the tuning pilot, then start one admitted BF16 cell. FP8/speculation remain NOT_TESTED pending live support verification. Current runner cannot measure streaming token timing, so TTFT/ITL remain null.
