# Local LFM evidence review

Read-only review of safe run identity, commit, configuration, and already-recorded summary fields. No answer text, raw response, or individual verdict was displayed. No model scoring or inference was performed.

## Cell-Akamai LFM 1.2B run

Path reviewed: `/Users/byron/projects/active/cell-akamai-gh/runs/lane_b_pilot_lfm1.2b/`.

- `COMMIT.json` has `answers_sha256=e3b0c442…b855`, the SHA-256 of an empty byte stream, and `config_sha256=28318185…e32c`. The directory's `answers.jsonl` is 0 bytes. This is a commit marker for an empty answer artifact, not evidence that LFM answers were generated or scored.
- The directory contains `items.jsonl`, but no run manifest, model-identity receipt, scorer receipt, score file, or model configuration file. The config digest cannot identify a model without its preimage.
- Therefore the served model/artifact, quantization, provider, execution host, hardware, reasoning mode, and any serving contention are **unknown** for this run. The evidence does not establish whether the attempted run failed because of reasoning behavior, contention, or another cause. No explicit failure reason was found in the permitted receipts.
- This LFM run has no answer-level score to recover. A future populated run requires a hardened, independently reproducible scorer after answer/config/dataset commitment; this review did not score it.

## Separate MagicStudio recorded execution

Two manifests under `/Users/byron/projects/active/agent-foundry/demo/recorded/antigence_lfm/` were reviewed as separate exploratory local executions. They must not be joined to the Cell-Akamai run above.

`manifest_20260929T055759Z.json` records host name `LOCAL_HOST_REDACTED`, kind `REAL_EXECUTION_RECORDED`, and four rows each for model IDs `lfm350m`, `lfm1p2b`, and `lfm2p6b`. The LFM 1.2B config identifies Ollama model ID `5791ac70d52d` and tag `hf.co/LiquidAI/LFM2.5-1.2B-Instruct-GGUF:Q4_K_M`. Thus a Q4_K_M model tag is recorded for this separate local run. The host string is recorded, but no GPU/CPU inventory or independently verified hardware identity is present in the inspected manifest.

The manifest already contains per-row summary fields. Aggregating only those existing booleans, without opening individual verdicts, gives LFM 1.2B: 4/4 `output_valid`, 0/4 recorded failures, 3/4 agreement with the recorded core verdict, and 3/4 agreement with the recorded expected result. Latency values span 939–34,300 ms. These are exploratory summary counts from four inputs, not a general benchmark or an independent scorer receipt. The manifest's limits state `n=1` execution per cell, that inputs were copied from Antigence's own tests, and that `num_predict=64` may truncate reasoning-style models before JSON. That note identifies a possible confound; the evidence reviewed does not attribute a particular row's behavior to reasoning or truncation. The manifest does not establish concurrent-load contention.

`manifest_20260929T060115Z.json` is a different model/configuration: `lfm2p6b_np512` resolves to `hf.co/LiquidAI/LFM2.5-2.6B-GGUF:Q4_K_M`, with `num_predict=512`, on the same recorded host. Its pre-recorded summary has 0/4 valid outputs and 4/4 failure flags. This is not the LFM 1.2B run. Its failure summary cannot explain the empty Cell-Akamai answer ledger.

## Dashboard recommendation

Keep these evidence states distinct:

| Item | Safe status to display | Metric state |
|---|---|---|
| Cell-Akamai `lane_b_pilot_lfm1.2b` | Commit marker present; empty answer file; model identity and outcome reason unknown | Score missing; not a neutral score |
| Separate MagicStudio LFM 1.2B | Recorded local execution; Q4_K_M tag; four exploratory rows | Existing summary counts available; no independent hardened scorer receipt |
| Separate MagicStudio LFM 2.6B, 512-token limit | Recorded local execution; Q4_K_M tag; distinct model | Existing summary reports 0/4 valid and 4/4 failures |

Use `null` with a specific reason for unavailable or mathematically undefined metrics. Missing answers, missing score files, and unverified identities should be represented as **MISSING** or **UNKNOWN**, with a reason; do not render them as numeric zero or neutral performance. The Cell-Akamai empty-answer hash means no score can be computed from this artifact. No claim about reasoning failure or hardware contention is supported.

## Scope and files

Reviewed only the Cell-Akamai `COMMIT.json`, safe file sizes and directory inventory, plus safe identity and pre-existing aggregate fields from the two named MagicStudio manifests. `answers.jsonl`, `items.jsonl`, individual model verdicts, raw responses, and private logs were not read or displayed. No files outside `docs/LOCAL_MODEL_EVIDENCE_REVIEW.md` were changed by this task.
