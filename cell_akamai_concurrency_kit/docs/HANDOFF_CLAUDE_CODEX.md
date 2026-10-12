# Concurrency pilot handoff to Claude/Codex

## Source of truth and responsibilities
- GitHub: `biobitworks/cell-akamai`, Lane A PR #3, Lane B PR #5. Do not overwrite Claude's lane; create successor PRs and preserve predecessors.
- Upstream Akamai workshop pinned: `454b43269216c1f92dd8d7e2711649e38cb888cb`.
- `EXP-AKAMAI-TOKEN-001`: four observed request completions, 68 server tokens each, verified internal zip hash `73c2c4ff7deb5c3e30b16f73ef6754c3b102cb0da8e4705a7ac8d485b7d38dad`.
- `qwen_original_reference`: user-reported 451 server completion tokens, zero speculative config; raw archive NOT_INSPECTED; do not treat chart export alone as a complete receipt.
- Lane B arm labels match Claude's B0..B3, but **both Genesis and DAISY are policy PROXIES**. Do not claim native model/policy training, scientific biological accuracy, or genuine Anticube.

## 1. Akamai Lane A
Execute the live notebook with namespace `workshop-s05`, vLLM endpoint `http://vllm:8000/v1`, serving model read from `/models` live. Do not restart model or alter Kubernetes; Module 07 comparison baseline is B0, where tokens/s from workshop chunk counts are explicitly NOT an equivalent token measure. Our `scripts/experiment.py` uses response `usage.completion_tokens`. Run per-arm sequentially, with concurrency within an arm, to avoid cross-arm interference. Capture same task IDs, seeds, timestamps, error/failure rows, raw Prometheus and evaluation receipts.

## 2. Claude Lane B
Review the frozen dataset items, oracle separation and the proxy policies. Calibration only on `calibration_items.jsonl`, nonconfirmatory pilot on `pilot_items.jsonl`. Freeze policy binding, inference revision/engine, token cap, n and seed before any `holdout_proposed` evaluation. No writeback or semantic promotion before controls.

## 3. Tuning gate
For any proposed Genesis or Vita DAISY change, retain prior policy FCO, create a successor policy candidate with declared typed `proposed_successor_of` edge, rerun calibration controls, preserve failures and compare accuracy-vs-cost Pareto. Report if no gain. ΔG*: NOT_COMPUTED. Anticube: NOT_COMPUTED until frozen operational predicates and negative controls. MMR: NOT_COMMITTED until ordered leaves, peaks/root, construction and independent verification. `sha256` is identity only.

## 4. Merge / dashboard
Only import run evidence after archive and raw snapshot verification. Graph trace: dataset-source -> task content/occurrence -> model execution -> answer -> independent oracle -> derived metrics -> bounded claim -> dashboard. Submit PR with tests, notebooks, evidence links and `NEXT_ACTION`. Never expose workshop credentials.
