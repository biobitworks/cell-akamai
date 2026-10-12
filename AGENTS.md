# cell-akamai agent contract

- **GitHub = coordination lane.** Pull before edits; push tested incremental commits; PR review governs integration. No separate chat transcript is canonical experimental state.
- Lane A owns `cell_akamai/`, `notebooks/10_token_kinetics.ipynb`, `notebooks/11_replay_offline.ipynb`, `tests/`, `schemas/`, and the dashboard template.
- Lane B (Claude) owns only separate scientific implementation, experiment specifications and `data/lane_b_results.jsonl` according to `schemas/lane_b_results.schema.json`.
- Cross-lane changes require an Issue and PR; don't write another lane's worktree. Never force-push.
- Preserve parent experiment, exact source revision, code/runtime identity, dataset/split, FCO occurrence/content identity, typed edges, and failure receipts. Hashes are identity keys, graph edges are declared relationships, Merkle inclusion is custody not truth, and intervention is needed for causal claims.
- Do not infer token count from stream chunk count. Do not equate TTFC with TTFT or claim tokens/s² as knowledge gain. Model revisions UNKNOWN unless verified.
- Store raw output under ignored `runs/`. No tokens, credentials, cookies, kubeconfig, protected datasets or raw personally identifying data in Git.
- All model training, Kubernetes writes and external submissions need separate authorization. This lane is read-only against hosted vLLM.
- Report `STATUS | COMMIT | TESTS | BLOCKERS | NEXT_ACTION` in the GitHub PR.
- Every experiment must have a Jupyter notebook executable by a human and a machine. Local fixture tests are never evidence of real Akamai execution.
