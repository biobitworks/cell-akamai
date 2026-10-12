# CELL-AKAMAI — LONG-DURATION SCIENTIFIC INFERENCE BENCHMARK

**Experiment:** `EXP-CAKM-MULTIMODEL-6DATA-LONGRUN-001`  
**Repository:** `biobitworks/cell-akamai`  
**Canonical local checkout:** `/Users/byron/projects/active/cell-akamai-gh`  
**Upstream workshop checkout:** `/Users/byron/projects/active/cell-akamai`  
**Execution:** Authorized Akamai GPU / vLLM / Kubernetes  
**Measurement duration:** At least 3,600 seconds of active inference per dataset representation per tested serving configuration.

## OBJECTIVE

Replace all relevant `NOT_TESTED` states with independently verifiable execution receipts where experiments actually succeed.

Perform long-duration, controlled measurements comparing original structured data against FCO/FCG representations, using the Akamai workshop's inference modules, metrics and units.

Evaluate:

- Genesis policy proxy versus baseline.
- Vita DAISY antigentic challenge versus randomized control.
- Strands Agents SDK versus plain vLLM/OpenAI-compatible clients.
- Sequential versus concurrent inference.
- BF16 versus FP8 where both precisions are supported.
- Speculative decoding disabled versus enabled.
- Scheduler and KV-cache tuning.
- Tokens/s, tokens/s², TTFT, TPOT, throughput, latency, quality and resource consumption.

Do not report improvement without independent evaluation and matched controls.

## 1. Synchronize time and recover evidence

Before execution, capture actual UTC and America/Los_Angeles timestamps from the execution host.

Do not use the current working directory, conversation timestamps, GitHub UTC timestamps, or a model's generated clock estimate as authoritative event time.

The event's submission deadline is October 12, 2026 at 16:00 PDT. Submit the available demonstration before the deadline; continue long-running verification afterward.

Fetch the current GitHub state and recover:

- PR #3 — telemetry and dashboard.
- PR #5 — Claude scientific evaluation and independent scorer.
- PR #7 — frozen ECA dataset and concurrency harness.
- PR #8 — Lane A concurrency successor.
- PR #10 — Strands agent/antigent implementation.
- Existing Akamai GPU receipts.
- All Module 8/9 input and output archives.

Use an isolated branch/worktree. Preserve failed Ollama pilots, previous Akamai results and all negative outcomes.

Do not use the upstream workshop checkout as the Git publication root.

## 2. Freeze and verify six dataset representations

Use the actual files from:

`CELL_AKAMAI_M08_M09_SIX_DATASETS_20261012.zip`

| Dataset ID | Representation |
|---|---|
| GEN-RAW | `data/original/genesis.jsonl` |
| GEN-FCG | `data/fco/genesis.jsonl` plus `data/fcg/genesis.jsonl` |
| DAISY-RAW | `data/original/vita_daisy.jsonl` |
| DAISY-FCG | `data/fco/vita_daisy.jsonl` plus `data/fcg/vita_daisy.jsonl` |
| EVAL-RAW | `data/original/evaluator.jsonl` |
| EVAL-FCG | `data/fco/evaluator.jsonl` plus `data/fcg/evaluator.jsonl` |

The source records are ECA-derived fixtures, not recovered historical biological data or historical Genesis/Vita DAISY model outputs.

Verify all package hashes, record counts, identities, FCG links and exact reconstruction.

Keep the three paired datasets matched by item ID. Never expose evaluator targets or oracle answers to actor/challenger prompts.

For each pair, benchmark both end-to-end retrieval-plus-inference and model-only inference. When testing representation overhead alone, preserve identical model-visible prompts.

Do not treat the 32 repeated ECA items as hundreds of independent examples. Track unique item count separately from request count.

## 3. Establish one-hour sustained measurement epochs

**Mandatory baseline:** At least 60 minutes of active measured inference for every one of the six representations.

**Mandatory first tuning comparison:** Repeat all six representations for at least 60 minutes per representation after exactly one authorized, documented serving-policy change.

**Recommended second tuning comparison:** Repeat after a different, separately controlled flag change for another 60 minutes per representation.

Minimum measured times:

- Baseline + one tuning configuration: 12 GPU-hours.
- Baseline + two separate tuning configurations: 18 GPU-hours.

Warm-up, interrupted windows, idle time and Kubernetes rollout time do not count toward these totals.

For each 60-minute epoch, use the following balanced design:

- Concurrency: 1, 2, 4 and 8 independent sessions.
- Three repetitions per concurrency level.
- Five minutes of sustained active measurement per repetition.
- Twelve valid windows × five minutes = 60 measured minutes.
- Randomize or counterbalance window order using a recorded seed.
- Use identical frozen inputs and decoding budgets across matched arms.
- Retain all retries, errors and incomplete windows.

Additional workshop-style saturation levels (16, 32, 64, 128) require a separate gated preflight and must be skipped or stopped if they exceed authorized capacity.

For Module 9's Kubernetes HTTP antigent service, respect its configured concurrency cap; do not silently treat rejected requests as completed workload.

Use monotonic elapsed time for performance measurements. Store UTC timestamps for provenance.

Restarted or resumed experiments must identify predecessor runs and remaining valid measurement duration.

## 4. Serving configuration experiments

Keep model, tokenizer, workload and serving policy fixed within each measured epoch.

Compare configurations in sequential GPU epochs, never as competing workloads on the same server.

**Configuration A — Baseline**

Record exact deployed model, model revision, precision, vLLM version, GPU type, GPU memory, cache settings, `max-model-len`, `max-num-seqs`, speculative configuration and scheduler settings.

**Configuration B — One-flag tuning**

From the Module 7 baseline evidence, select exactly one justified bottleneck-related flag, such as:

- `--max-num-batched-tokens`
- `--max-num-seqs`
- `--gpu-memory-utilization`

Select a value only after measuring the actual bottleneck. Do not tune `max-num-seqs` upward and attribute a difference to that flag if concurrency never reaches the original limit.

Preserve the complete before/after deployment manifests.

**Configuration C — Independent second hypothesis**

Restore the original baseline, then test a different single serving-policy flag with its own 60-minute epochs.

Do not accumulate untracked changes.

**Additional controlled experiments**

When supported and authorized, perform matched BF16-versus-FP8 and speculative-off-versus-speculative-on runs. Each new condition requires its own complete measurement allocation for every dataset being compared.

Model revisions, drafter configurations and deployment differences must be recorded. Unsupported configurations remain `NOT_TESTED`, not `FAILED`.

## 5. Module 9: Plain versus Strands

Before long-duration Strands testing, prove real SDK compatibility:

1. Install and pin `strands-agents[openai]`.
2. Resolve the actual vLLM `/v1/models` identity.
3. Execute a real Strands `OpenAIModel` request against that server.
4. Capture successful or failed response, duration and token usage.
5. Verify the original Akamai Module 9 agent separately.
6. Verify the optional Strands service in its own namespaced deployment.

The existing seven fixture tests are not proof of networked Strands execution.

Compare both runtimes on identical ECA tasks:

`PLAIN_CLIENT` versus `STRANDS_AGENT`

Within each runtime, execute:

- B0_FIXED
- B1_GENESIS (current Genesis proxy; label explicitly)
- B2_GENESIS_DAISY
- B3_RANDOM_CONTROL

Use matched call/token budgets wherever causal comparisons are intended. If call budgets differ, report that confound.

Separate tool-free runtime parity testing from demonstrations involving a Strands tool.

Measure actor, challenger and adjudicator latency individually. Commit answer files before independent scorer access.

## 6. Measurements and mathematical definitions

Measure and report:

**Verified aggregate generation throughput**

`R_j = (G_j - G_(j-1)) / (t_j - t_(j-1))`

Where `G` is the vLLM generation-token counter or an independently validated accumulated completion-token count.

Unit: `tokens/s`.

**Throughput change rate**

`A_j = (R_j - R_(j-1)) / (midpoint_j - midpoint_(j-1))`

Unit: `tokens/s²`.

Sample Prometheus counters and gauges throughout the run. Produce 10-second and 30-second throughput windows where counter resolution permits.

Report positive, zero and negative acceleration values. Exclude counter resets and invalid/missing samples rather than converting them to zero.

Treat tokens/s² as the measured change in serving throughput over time, **not** as model learning, training acceleration or a proof of continuous performance improvement.

Report warm-up and steady-state kinetics separately. Sustained throughput with acceleration approximately zero can be the correct outcome.

The official workshop's legacy loadtest counts nonempty SSE chunks. Preserve those values under `legacy_stream_chunks_per_s`; do not relabel them as token throughput.

Also measure:

- Prompt tokens and completion tokens.
- Per-request and aggregate throughput.
- Client first-content latency and server TTFT separately.
- TPOT/inter-token latency.
- p50, p95 and p99 end-to-end request duration.
- Request failure rate, timeout rate and retry count.
- GPU utilization, GPU memory and KV-cache usage.
- Running, waiting and preempted requests.
- Requests/s.
- Tokens per correct answer and total inference cost when supported.
- FCO lookup/rehydration overhead, separately from inference.

All dashboard values must include their units, data source and measurement method.

## 7. Independent scientific evaluation

Before model inference, freeze the input identities and control policy.

After model answers are committed, run the independent scorer in a separate evaluation process.

Evaluate correctness, coverage, abstention, unsafe admission, invalid output and error localization.

For paired correctness comparisons, use valid paired statistical tests and report discordant counts. For performance, compute uncertainty over independent workload blocks and preserve the correlation structure of repeated measurements.

Do not increase statistical sample size by counting repeated inference on the same ECA item as new biological or scientific examples.

Include negative controls:

- Randomized challenger.
- Token-matched additional inference without useful challenge.
- Raw-versus-FCO reconstruction equivalence.
- Missing FCG edge.
- Corrupted digest.
- Duplicate occurrence identity.
- Stale model configuration.
- Counter reset.
- Failed inference and missing usage.

Preserve predecessor results and every failure.

No weight-update receipt means self-training is `NOT_TESTED`. Anticube and ΔG* remain `NOT_COMPUTED` until genuine independent computations exist.

## 8. Unit tests and workshop module coverage

Provide executable pytest tests and human/machine reproducible notebooks. Map every assertion to its corresponding workshop module.

| Module | Required validation |
|---|---|
| 00 | Endpoint, namespace, credentials availability without revealing secrets |
| 01 | Exact model identity, response integrity and request schema |
| 02 | Byte/bit/GiB conversion, memory budget and KV sizing |
| 03 | Prefill/decode separation, TTFT, TPOT and cache counters |
| 04 | Dense/MoE analytical assumptions and model-specific calculation limits |
| 05 | BF16/FP8 precision verification and matched quality evaluation |
| 06 | Speculative decoding off/on, drafter identity, acceptance and fallback |
| 07 | Saturation knee, queue growth, concurrency and completion rate |
| 08 | Controlled one-flag tuning, rollout, matched before/after statistics |
| 09 | Real agent requests, tool calls, Strands interoperability and concurrent sessions |

Additional Cell-Akamai tests must check:

- Correct `tokens/s²` differentiation on synthetic numerical traces.
- Missing, out-of-order and reset counter handling.
- Correct tokens/s versus chunks/s labeling.
- Frozen dataset hash verification.
- Original-to-FCO exact reconstruction.
- FCG pointer and edge validity.
- Preventing held-out oracle leakage.
- Exact item × arm result coverage.
- Equal-budget control enforcement.
- Test failures preserved across retries.
- Run-resume idempotency.
- ZIP extraction and archive-integrity verification.
- Dashboard data import and live/replay state separation.

First run offline tests without GPU. Then run real endpoint integration tests. Finally execute the sustained benchmarks.

A mocked test may pass while the corresponding real deployment remains `NOT_TESTED`.

## 9. Safety and resource controls

Require explicit authorization for every vLLM deployment or Kubernetes configuration change.

Do not interrupt other agents' active runs.

Implement preflight limits for VRAM, max requests, concurrency, context length, token budgets, cost and time.

Stop and record the failure if GPU OOM, server crash, repeated request timeouts, unacceptable error rate, namespace violation or a configured safety threshold occurs.

Do not automatically retry a failed high-cost configuration without bounded retry authorization.

Use checkpointed append-only output after every measurement window. A Jupyter kernel disconnect must not erase completed valid windows.

Use an authorized durable process runner rather than assuming the browser tab will remain open for 12–18 hours.

## 10. Evidence artifacts and dashboard

Each measured window must emit an immutable, uniquely identified receipt with:

`run_id, parent_run_id, dataset_id, dataset_sha256, representation, model_id, model_revision, precision, runtime, policy_arm, concurrency, serving_config_sha256, workload_sha256, start_utc, end_utc, elapsed_monotonic_s, prompt_tokens, completion_tokens, metric_values, units, failures, evidence_state`.

Export:

- Raw safe metrics and time series.
- Benchmark results JSONL/Parquet.
- Per-item predictions and independently produced scores.
- Executed notebooks with outputs.
- Configuration diffs.
- FCO/FCG projection and exact source pointers.
- Test logs.
- Statistical results and plots.
- Anomaly and failure receipts.
- Complete hashes and manifest.
- Dashboard-ready data index.

Build dashboard visualizations for throughput versus concurrency, tokens/s² versus time, latency distributions, cache/queue pressure, Module 8 before/after, and Strands versus plain-client scientific controls.

The dashboard must identify completed, partial, failed and untested conditions separately.

## 11. GitHub publication and handoff

Commit and push only verified, sanitized code, tests, notebooks, manifests and report indexes from an isolated branch.

Preserve full evidence in a separately downloadable ZIP. Exclude credentials, kubeconfigs, secrets, large private raw traces and sensitive materials from GitHub.

Open a PR against canonical `main` and report:

- Branch and full commit SHA.
- Actual pytest results.
- Experiment duration **per dataset and configuration**.
- Number of completed requests and unique evaluation items.
- Exact model and GPU identity.
- Confirmed experimental comparisons.
- Unsupported claims and negative results.
- Artifact ZIP path and SHA-256.
- PR URL.
- NEXT_ACTION.

Never claim an hour-long successful experiment when the active measured inference interval was shorter than 3,600 seconds.

**Final success condition:** Every completed dataset/configuration experiment has at least one hour of usable inference, actual unit-correct measurements, validated controls, independent evaluation and reproducible custody receipts.

**Immediate priority:** Secure the HackerSquad video submission before the event deadline. Long-duration validation may continue afterward without changing the historical submission state.