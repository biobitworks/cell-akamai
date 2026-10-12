# Cell-Akamai concurrency and model-comparison pilot (piecewise)

**Current purpose:** Module 07 scheduling and Module 09 orchestration comparison for `workshop-s05`; no recreation of Modules 00–09. Use existing workshop helpers where available; the read-only experiment runs paired ECA tasks with B0–B3 across bounded concurrency, saving server-reported usage counts and Prometheus snapshots. Real Akamai experiment NOT_EXECUTED in this package.

## Important distinction
B1 is **GENESIS_POLICY_PROXY_V0**, not the recovered Genesis transformer. B2 is **DAISY_CHALLENGE_PROXY_V0**, not independently trained Vita DAISY/Antigence. B3 is a randomized cell recheck control that may still help accuracy. This is a nonconfirmatory **synthetic ECA task**, not biological proof. No Anticube, ΔG*, signed breakpoint or committed MMR.

## Upload/run
1. Upload `CELL_AKAMAI_CONCURRENCY_KIT.zip` and `AKAMAI_CONCURRENCY_RUN_THIS.ipynb` to the same JupyterLab folder. Notebook unpacks the ZIP and validates required file paths.
2. Open the notebook and **Run All**. It calls the live served model from `/v1/models` and records 8 pilot items per arm at concurrency 1 and 2. No Kubernetes write commands.
3. Review output tables and graph, download `CELL_AKAMAI_CONCURRENCY_RESULTS.zip` from the displayed FileLink; share identical archive with Lane A and Claude.
4. To extend only after successful pilot, change `CONCURRENCIES=(1,2,4)` and `MAX_ITEMS=32`. Note this increases requests, cost and GPU load.

## Dataset split
- 32 calibration ECA items (tuning allowed, separate oracle file)
- 32 pilot ECA items, exact Claude seed range 50000..50031 (nonconfirmatory)
- 64 proposed holdout items (NOT_FROZEN, no training or selection)
- No cross-split identical `(rule, initial_state)` pairs. Uses `numpy.default_rng(seed)`, exact Claude item contract. Gold labels are separate files and are never passed to model prompts.

## Measures
- Completion tokens: only `usage.completion_tokens` from nonstreaming API response, unknown when absent; never count chunks.
- `output_tokens_per_s`: sum server tokens for entire arm block / block wall time. Because B0 has one request and B1/B2/B3 have three per item, compare also `items_per_s`, `correct_items_per_s`, accuracy and total tokens per correct item.
- `tokens_per_s²`: inter-window difference is diagnostic only and NOT a direct per-token acceleration. Our pilot intentionally does **not** assert it until matched time windows and replicas are available.
- KV/queue: vLLM Prometheus gauge samples observed during each arm block, `None` when missing; not comparable to Ollama.

## Evidence and archive
Each arm + concurrency block is content-hashed. The scorer rejects changed bytes and independently recomputes the task oracle. ZIP verification protects against archive corruption, not external source attestation or signed custody.

See `docs/MODULE_STATUS.csv` and `docs/HANDOFF_CLAUDE_CODEX.md`.
