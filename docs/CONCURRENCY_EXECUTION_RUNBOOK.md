# Cell-Akamai — concurrency execution, scientific scoring and dashboard (PILOT)

**Status:** source and 32-item deterministic ECA input dataset implemented and locally tested; **NO real concurrent model execution in this lane**. Akamai original smoke and Qwen no-drafter reference receipts were independently rechecked from operator's export, not reproduced remotely. Recorded `INTER_REQUEST_TOKENS_PER_S2` for concurrent experiments is **NULL**, because within-overlapping-request rate derivatives are not the sequential derivatives measured in the upstream notebook.

## Owners and dependencies

- **Executor / Codex / Cursor:** Akamai vLLM notebook/canary, mutable precision/drafter transitions only with explicit namespace authorization, actual concurrent inference, sanitized local/dashboard snapshots, append-only run receipts. Own separate branch/worktree; do not modify PR #5's scientific harness.
- **Claude:** Lane B PR #5 nd real policy binding, oracle separation, scoring **after** answer commitment, frozen protocols, scientific comparison. Own separate branch/worktree. Current B1 is **Genesis proxy**, and B2/B3 have different challenge specificity. Do not promote them to equivalent-compute causal comparison without fixing controls.
- **Orchestrator:** independent dataset/evidence/hash checks, measurement semantics, PR review. Input ECA seeds 50000–50031; 32 tasks across rules 30/90/110/184, periodic boundaries, standard Wolfram bit order. No oracle/answers committed in dataset.

## Local read-only setup

Use a separate canonical clone, not the MagicPro inherited Akamai workshop checkout. This PR branch may be checked out independently from Lane B (source is unmerged); pass the Claude harness path via `--harness`.

```bash
git clone https://github.com/biobitworks/cell-akamai.git /tmp/cell-akamai-concurrency
git -C /tmp/cell-akamai-concurrency fetch origin
git -C /tmp/cell-akamai-concurrency switch --track origin/lane/orchestrator-concurrency-dataset-20261012
# Separate Claude worktree, never modify its branch
mkdir -p /tmp/cell-akamai-claude
git clone --branch lane/claude-msm https://github.com/biobitworks/cell-akamai.git /tmp/cell-akamai-claude
cd /tmp/cell-akamai-concurrency
cp dataset/eca_pilot_config.example.json /tmp/cell-akamai-pilot.json
python tools/concurrency/run_concurrency.py \
  --dataset dataset/eca_pilot_inputs_v1.jsonl \
  --manifest dataset/eca_pilot_manifest_v1.json \
  --config /tmp/cell-akamai-pilot.json \
  --harness /tmp/cell-akamai-claude/lane_b/harness/run_lane_b.py \
  --limit-items 8 --concurrency 1 2 4 8
```

**The preview makes no model requests and no output folders.** First compare the planned request/call budget (320 model calls for 8 items × four arms × four concurrency levels) to permitted Akamai capacity. Check `GET http://vllm:8000/v1/models` from within authorized JupyterLab, actual model and vLLM config, and readiness. If another lane already benchmarks the same server, do not overlap runs. Parallel **agent development**, sequential **GPU experiment epochs**, otherwise external load contaminates throughput and latency.

## Actual execution (authorized workload only)

```bash
# In Akamai's hosted JupyterLab container or an authorized node with access to vLLM;
# project and Lane B harness directories must be present inside that environment.
python tools/concurrency/run_concurrency.py \
  --dataset dataset/eca_pilot_inputs_v1.jsonl \
  --manifest dataset/eca_pilot_manifest_v1.json \
  --config /tmp/cell-akamai-pilot.json \
  --harness /tmp/cell-akamai-claude/lane_b/harness/run_lane_b.py \
  --module-id 07 --stage bf16_reference --backend AKAMAI_VLLM \
  --limit-items 8 --concurrency 1 2 4 8 \
  --output-root runs/concurrency --execute
```

This drives 4 arms with 1 or 3 serial calls per item, but up to `c` independent items concurrently. Each `cXX_paired_for_scoring/` contains `answers.jsonl`, `items.jsonl`, `COMMIT.json`; use Claude's **independent scorer after the file commitment**, not in the inference runner. Its scientific `source_class` must reflect actual execution (use `SYNTHETIC_FIXTURE` only in fixture tests). Beware current Claude scorer CLI optional-argument parsing needs review; calling its `main(config_path,run_dir,source_class)` explicitly is safer until fixed. The upstream Claude script checks `answers_sha256` but currently does not independently validate `config_sha256` or `dataset_sha256`; it should fail closed on both before any scientific claim.

## Local dashboard (read-only, no raw responses)

```bash
python tools/concurrency/serve_dashboard.py --runs runs/concurrency --port 8765
# open http://127.0.0.1:8765/
```

The server binds loopback and returns only whitelisted aggregate values (`/data.json`), with refresh polling; it never exposes run source files or raw model text. It refreshes after each completed `c × arm` cell. Publish an external dashboard only after adding authentication or a fully sanitized immutable export. Local execution paths must remain ignored by Git.

## Workshop alignment and controlled run schedule

- Original Module 07 `common/loadtest.py` computes SSE **chunks/s** mislabeled `throughput_tok_s`; **do not compare that numeric column to verified usage tokens/s**. Re-run original workload using verified usage counts or explicitly label `chunks/s` as non-comparable.
- Modules 00–04 establish inference, memory, prefill and reference cost identities. Module 05 baseline Qwen BF16 `Qwen/Qwen3-4B`, then authorized FP8 `RedHatAI/Qwen3-4B-FP8-dynamic`. Module 06 FP8 *no drafter* vs FP8 + drafter. Module 07 same fixed workload concurrency. Module 08 one-flag serving tuning. Module 09 agents B0–B3 with ECA inputs. Assign `--stage` and `--module-id` for each configuration only after verifying live deployment identity.
- Compare B0 fixed versus B1 Genesis-proxy versus B2 candidate+antigentic challenge versus B3 randomized control **within each exact serving configuration and concurrency level**. Quantization/config effects and scientific policy effects are orthogonal; mixing magicstudio and Akamai hosts is not a controlled precision experiment.
- Main metrics: total completion tokens; total batch wall seconds; aggregate completion tokens/s = sum usages / batch wall time; items/s; p50/p95 per-item latency; actual call count; missing usages as null; failed/timeouts/abstentions. Later Claude scorer: per-item exact accuracy, Hamming error, McNemar paired discordance and tokens per correct item. Never call time derivative under concurrency a validated tokens/s² advantage.
- Pilot sample N=8 at each concurrency has low power, intended to prove plumbing. Confirmatory study requires freeze and adequate independently established sample size.
- Do not assert **antigentic training** without executed weight updates. DAISY challenge stage here is inference-time evaluation and answer revision, not model training. Anticube and ΔG* remain **NOT_COMPUTED** until validated formulas, negative controls, oracle separation, and independent tests.

## Failure/reproducibility requirements

- Tests: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests` (local code tests, not real GPU execution).
- Persist `run_manifest.json`, each `cXX_*` raw answers and SHA-256 commitments, and `bench_cells.json` under ignored `runs/concurrency` (no private data in Git). Restore all failures, do not prune empty/failed cells. Module receipts should cite workshop SHA, dataset SHA, Claude harness code SHA, endpoint model revision where known, and serving parameters when available.
- `NEXT_ACTION`: executor runs authorized Akamai BF16 concurrency first; Claude scores the committed paired outputs; after review, run FP8 and FP8 speculative configurations as separate phases; rerun exact same dataset and concurrency matrix; update judge dashboard with evidence and non-results.
