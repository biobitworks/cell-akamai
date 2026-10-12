# Module 09 — Strands actor / antigent capstone (2026-10-12)

**State: IMPLEMENTED OFFLINE; 0 real Strands/GPU invocations.** Source: Akamai workshop module 9 at `akamai-developers/akamai-workshop-ai-inference@454b43269216c1f92dd8d7e2711649e38cb888cb`. Its capstone uses a *plain OpenAI client*, a Kubernetes Deployment and Service, a read-only GPU-pricing tool, port forwarding and six concurrent agent questions. Our candidate does **not** modify its manifest, endpoint, agent code or deployment; preserve it as the baseline.

## Scientific question

At a frozen model/precision/backend and equal task inputs, do a **Strands agent** and an **antigent challenger** improve ECA correctness or reduce failures compared with (a) the workshop's plain-client agent and (b) the same model-call budget with an uninformative challenge? How much does the added agent/antigent inference cost at concurrency 1, 2, 4 and 8?

The executable adapter reuses Claude PR #5's **unmodified** `lane_b/harness/run_lane_b.py` with policy arms B0 Fixed, B1 Genesis **PROXY** (three votes), B2 challenger + adjudicator, B3 randomized re-check. The B2 challenger **is not an independently trained model**; it is an independent fresh Strands context over the same served model. The B2/B3 prompts and B0's fewer calls require separate control analysis before making causal claims.

The run driver imports PR #7's existing `tools/concurrency/run_concurrency.py` helper for balanced frozen ECA items, per-arm execution and batch statistics. Both dependencies are explicitly supplied as paths so this branch does not mutate their PRs.

## Antigent contract v0

- **Actor**: proposes a candidate, may use the public task definition, never receives held-out oracle targets.
- **Challenger**: uses a new Strands Agent session (no previous conversation carryover) and critiques the candidate under an unchanged inference cap.
- **Adjudicator**: receives proposals from actor and challenger, picks a final answer; never receives oracle correctness feedback.
- **Negative control**: random re-check prompt under matched call count; purpose is extra-token/extra-call control, **not** actual Anticube classification.
- **Oracle evaluator**: distinct process after `answers.jsonl` SHA-256 commitment, using Claude's ECA independent scorer. No oracle code is imported or executed by this run driver.
- **Custody**: per-item response hashes, per-concurrency panel `COMMIT.json` (file hash), `bench_cells.json`, `run_manifest.json`, optional role traces (hashes only). FCO/FCG integration remains follow-up; no signatures or MMR roots invented.
- **Training**: prompts/challenge traces are **feedback candidates**. They do not alter model weights. A later successor requires versioned training data, held-out split, executed optimizer/weight update receipts, immutable predecessor, and independent evaluation.

## Reproducible execution (requires current PR #5 and #7 isolated checkouts)

Install on an authorized workstation or workshop Jupyter kernel:

```bash
python -m pip install 'strands-agents[openai]' requests numpy
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=. python -m pytest -q module9_antigents/tests
```

Confirm that the served Qwen model supports the Strands OpenAI-compatible provider. Strands SDK may change; pin the installed version in execution receipts. Use an explicit data config with `base_url: http://vllm:8000/v1`, `model: Qwen/Qwen3-4B`, `max_tokens_per_call`, `item_token_cap`, `item_call_cap`, `temperature: 0`, `decode_seed`, and `api_key_env` (env variable name only). Never commit secrets or full raw responses. Verify served model with `/v1/models`; do not infer precision from model name alone.

```bash
# PREVIEW, no inference
PYTHONPATH=. python -m module9_antigents.run_capstone \
 --dataset /path/to/pr7/dataset/eca_pilot_inputs_v1.jsonl \
 --manifest /path/to/pr7/dataset/eca_pilot_manifest_v1.json \
 --config /path/to/pilot_config.json \
 --harness /path/to/pr5/lane_b/harness/run_lane_b.py \
 --concurrency-helper /path/to/pr7/tools/concurrency/run_concurrency.py \
 --runtime strands --levels 1 2 4 8 --limit-items 8

# Add --execute only after preview, namespace verification and authorization.
# For runtime-control comparison repeat an identical epoch with --runtime plain.
```

A run produces `runs/module9/module09-<runtime>-.../` including `run_manifest.json`, `bench_cells.json`, per-concurrency `cXX_paired_for_scoring/{items.jsonl,answers.jsonl,COMMIT.json}`. **Do not score answers until the commitment exists**. Recompute dataset, answers and config digests independently before scoring. Scorer must validate complete item × arm coverage and cap overruns. The driver serializes benchmark cells on the shared GPU and only parallelizes independent items within each arm; it never runs Strands and plain-client workloads simultaneously. `--allow-contract-tool` is only for a *separate* Module 9 tool-use demonstration; its added model/tool work is not a cost-matched parity benchmark.

## Module 9 concurrency crosswalk

| Measurement | Workshop module 9 | Cell-Akamai Strands module 9 |
|---|---|---|
| Agent implementation | plain HTTP OpenAI client; pricing tool | Strands Agent with OpenAIModel targeting same vLLM; optional read-only ECA-contract tool |
| Batch pattern | 1 question vs 6 distinct questions | frozen ECA items at concurrency 1,2,4,8 by policy arm and runtime |
| Latency | one-session and six-session wall time | per-item p50/p95 ms, batch wall time |
| Work | six separate questions | balanced paired ECA inputs; same items for all arms |
| GPU/engine | running requests, KV-cache use | inherit Lane A `/metrics` for running/waiting/KV/preemptions; **not yet wired here** |
| Output tokens | workshop tools vary; beware SSE chunks | Strands `AgentResult.metrics.accumulated_usage['outputTokens']`, else NULL |
| tokens/s | total verified usage / measured batch wall time | aggregate completion tokens/s; separate from per-request rate |
| tokens/s² | not in Module 9 | NULL for overlapping requests; only Lane A's ordered requests get midpoint rate derivative |
| Safety & quality | in/out-of-scope conversation, pricing | exact ECA oracle accuracy, invalid/abstained cases, challenger/negative-control effects after independent scoring |

No improvement or self-training claim is permitted without executed controlled results. Avoid adding secrets, paths or model replies to Git. Keep old failed experiments and unknowns.

## Roles & next actions

- **Cursor/Codex (execution lane):** Confirm hardware, namespace, model, precision, deploy only after authorization, run original Module 9, then Strands vs plain-client with frozen inputs and isolated epochs. Capture model usage and vLLM metrics. Commit **sanitized** receipts and update dashboard through own PR.
- **Claude (scientific lane):** Independently validate every `cXX_paired_for_scoring` panel and negative control, score exact-match/Hamming/McNemar, bind real Genesis and future DAISY successor. Extend dashboard cards for runtime × policy × concurrency and show source/evidence limits.
- **Orchestrator:** Review lineage, failures, full verification, claims; do not merge unverifiable improvements.

**NEXT_ACTION:** On Akamai while GPU access lasts, run original Module 9 baseline and an 8-item Strands/plain pilot at c=1 and c=2 before expanding to c=4,8. Frozen 32-item dataset is a pilot only; confirmatory task power and genotype/biological data are not supplied.
