# Cell-Akamai modules 1–9 and local evidence audit

**Status: PARTIAL, with score custody failures.** Selected recovery archives and their file manifests verify, but the retained answer-ledger bytes fail their adjacent commitment hashes. Scores dependent on those ledgers are withheld. This audit covers the retained index and recovered snapshots available for this review; it is not a claim that every original or private run was recovered.

The audit is read-only. It did not run recovery scripts, read or print answer text, call an inference endpoint, start a GPU run, publish evidence, or modify the dashboard, narration, or canonical worktree. The output is sanitized: only relative artifact names, run labels, counts, states, and custody findings are included.

## Source checks

The retained `DASHBOARD_EVIDENCE_INDEX.v5.json` contains 450 catalog rows and six source groups. Three local copies of this index were byte-identical. Its source-manifest summaries report 7/7 handoff files, 21/21 six-dataset files, 27/27 evidence-export files, and 825/825 GitHub-evidence files. Independent checks against the retained full-workspace snapshot reproduced those four counts with no mismatches. The separate `akamai_run_001.zip` has no embedded file manifest; its outer archive digest matches the recovery inventory, and its 12 files match the corresponding extracted copy byte-for-byte. The outer workspace snapshot also passes its recorded CRC and inventory checks.

These checks establish consistency of the checked copies, not authenticity of the original execution host or completeness of all evidence. The v5 source list itself says the `ALL_EVIDENCE` archive was not recovered. The retained workspace snapshot is explicitly non-atomic; its license and secret audit remains pending. Neither condition permits an all-data completeness claim.

The v5 index is stale for Modules 8 and 9: its M08 before/after and M09 run rows still carry `NOT_TESTED` states from the earlier handoff source, while later recovered GitHub-evidence material contains M08/M09 execution artifacts. The later artifacts do not automatically make the v5 rows current or their result commitments valid.

## Module coverage

Saved notebook execution counters are descriptive metadata, not independent proof of execution. In the recovered original workshop bundle, Modules 1–9 have saved execution counters of zero. Separate executed copies and run receipts are listed independently below; their existence does not mean the original notebooks ran.

| Module | Evidence found | Audit assessment |
|---|---|---|
| 1 — Inference stack | Original notebook/source present; saved counter is zero; no module-specific result receipt found in the audited index | **NOT VERIFIED**. Implementation/source presence is not a measured run. |
| 2 — Units and memory budget | Original notebook/source present; saved counter is zero; no module-specific result receipt found | **NOT VERIFIED**. No measured module result established. |
| 3 — Prefill/decode and KV cache | Original notebook/source present; saved counter is zero; no module-specific result receipt found | **NOT VERIFIED**. No measured module result established. |
| 4 — Dense vs. MoE | Original notebook/source present; saved counter is zero; no module-specific result receipt found | **NOT VERIFIED**. No measured module result established. |
| 5 — Quantization | Original notebook/source present; saved counter is zero; no verified FP8 module receipt found. The separate Qwen reference records unknown precision | **NOT TESTED / UNKNOWN**. The reference receipt cannot stand in for an FP8 run. |
| 6 — Speculative decoding | Original notebook/source present; saved counter is zero; the separate Qwen reference records no drafter configuration | **NOT TESTED**. It is not a speculative-decoding comparison. |
| 7 — Inference-engine saturation | Original notebook counter is zero. A corrected executed notebook and separate recovered workshop/full-matrix run receipts exist | **RECOVERED OBSERVATIONS, NOT REEXECUTED HERE**. Aggregate service metrics are distinct from answer quality. The paired answer-ledger commitments fail in the recovered copy, so associated score claims are refused. |
| 8 — Tune and evaluate | Original notebook counter is zero. Separate successor execution contains before/after and quality artifacts; v5 still reflects older `NOT_TESTED` rows | **PARTIAL RECOVERED EXECUTION**. The two quality answer files fail their neighboring commit hashes; no score is accepted from those files. Do not infer improvement from the before/after label. |
| 9 — Optional agents on Kubernetes | Original notebook counter is zero. A separate executed successor copy and M09 ECA/six-dataset artifacts exist; one saved notebook has an error output. Recovered reporting records the optional agent deployment path as failed/not ready | **PARTIAL / FAILED PATHS RETAINED**. The M09 answer file commitment fails. The six-dataset package says model inference was not tested while a later comparison receipt says raw answers were committed; this scope conflict is unresolved. No M09 score is accepted. |

The recovered original workshop notebook bundle includes Modules 00–09 with zero saved execution counters. Separate executed notebook copies exist for corrected Module 7 and later successor M08/M09/offline-verification work. Counters and outputs on those copies are not independent validation of the retained run data.

## Local runs kept separate

- The canonical local LFM 1.2B pilot has an empty answer ledger. Its commit hash equals the SHA-256 of an empty file. It has no run manifest, model-identity receipt, scorer receipt, or score artifact in the inspected directory. This is **MISSING**, not a zero score; its config digest alone does not identify the model or execution environment.
- The separate `EXP-AKAMAI-TOKEN-001` local export records four request records for Qwen/Qwen3-4B. Its declared same-host replay passed and all eight referenced metrics-file hashes match. Independent-host reexecution was not tested; model revision and precision are unknown; it is unsigned and has no project MMR. This is an observed receipt, not independent reproduction.
- The separate `EXP-AKAMAI-SPEC-001` record is a four-record Qwen no-drafter reference with unknown precision. It is not an FP8 or speculative run and does not provide a matched comparison. The two exported copies of the token run are duplicates, not independent replications.
- Local Ollama Lane B pilot rows remain a distinct local model/workload family. They are not merged with the hosted Akamai Qwen receipts or the empty LFM ledger. Any later analysis must preserve their separate model identity and run states.

## Answer commitment and score refusal

I compared file bytes by hash only; no answer contents were read. In the retained GitHub-evidence archive, all 20 full-matrix answer files that had neighboring `COMMIT.json` declarations failed the declared answer hash. The three recovered M08/M09 answer files with neighboring commit declarations also failed. Two other adjacent answer-ledger pairs failed as well. These results concern the retained archive copies; they do not identify why the copies differ from their original commitments.

The bundled independent-scoring receipt says four paired panels were scored, but the four retained paired-panel answer files do not match their commit hashes. The index separately labels 48 bundle-reported score fields as `BUNDLE_REPORTED_UNVERIFIED`. I therefore refuse those score values pending recovery of bytes that match the declared commitments and a rerun of the frozen scorer against those exact bytes. The existence of a scoring receipt does not override the failed custody check.

Service throughput and latency summaries that do not depend on answer bytes remain reported observations with their recorded provenance limits; they do not validate answer quality. This audit does not promote any bundled score, comparative improvement, causal claim, or biological claim.

## Null and failure-state interpretation

| State | Meaning in this audit |
|---|---|
| `NOT_TESTED` / `AFTER_NOT_TESTED` | No evidence of execution for that condition/arm; never substitute numeric zero. |
| `NOT_COMPUTED` | The metric or formula was not computed. Anticube and ΔG* remain in this state. |
| `NOT_RECOVERED` | The expected artifact was absent from the audited recovery; it is not a negative experimental result. |
| `UNKNOWN` | Identity or value is unavailable or unverified; it is not zero and cannot be inferred from a digest alone. |
| `UNDEFINED_ZERO_CORRECT` | A derived ratio with zero correct items has an undefined denominator; retain null plus reason, not zero. |
| `FAILED` | A failure receipt is retained. It is evidence of that failed attempt, not a successful run or a scientific negative result. |
| `BUNDLE_REPORTED_UNVERIFIED` | A value is present in the bundle but its required answer-byte custody check fails; withhold it. |
| `OBSERVED` | A source recorded an observation. This state alone does not establish independent reproduction or a causal/scientific claim. |

## Merkle and breakpoint compliance

| Requirement | Available implementation/evidence | Status |
|---|---|---|
| Unique receipt per measured window | `tools/hour_scale/sustained.py` writes numbered window receipts and a mutable latest pointer | **Designed; no successful sustained run to audit.** The latest pointer is mutable; numbered receipts are the intended immutable record. |
| Local Merkle root over receipt digests | `sustained.py` hashes canonical window receipts into a local Merkle tree; the receipt labels it unsigned and not a project MMR | **Implementation present; no live roots produced by a completed run.** |
| Pull-side leaf/root verification | `tools/hour_scale/pull_publish.py` recomputes each receipt digest and local root before accepting a checkpoint | **Code path present; not exercised against a completed sustained run in this audit.** |
| Project MMR integration and signature | v5 claims `mmr=NOT_COMMITTED` and `signature=NOT_SIGNED`; local preflight receipts also record no MMR. The `9f99db…` local Git checkpoint contains an SSH signature header, but default Git verification is unavailable because the allowed-signers file is not configured. A detached manifest signature is verified by the current local attestation. Neither establishes project MMR integration | **PROJECT MMR NOT INTEGRATED.** Preserve the artifact-level signature claims separately; do not characterize the Git checkpoint as unsigned or treat these signatures as an MMR anchor. |
| Fifteen-minute/hourly checkpoint breakpoints | `docs/HOUR_SCALE_EXECUTION_PLAN.md` requires checkpointing at preflight, warm-up, first measured result, every 15 minutes, each cell, failures/config changes and scoring/archive verification. The direct runner defaults to 900-second snapshots. The queue dispatches `sustained.py`, which writes a receipt at each 300-second measured window boundary | **Cadence is specified and the queue design is more frequent than 15 minutes; run compliance is unverified.** The queue has produced no successful measured window receipt here. |
| One-hour measured duration per represented dataset/configuration | The sustained design targets 12 × 300-second windows for four non-oracle dataset representations. Earlier queue receipts show zero completed windows and failed/paused preflight states | **NOT FULFILLED.** No 3,600-second dataset/configuration epoch is evidenced. The queue also does not cover all six protocol representations or tuning configurations. |
| Score only after committed answer validation | `INDEPENDENT_SCORING_RECEIPT.json` exists, but retained answer files do not match their adjacent commits | **BLOCKED.** No affected score is accepted. |

The local tree/checkpoint code is custody machinery, not evidence that the hour-scale workload ran. No execution in this audit satisfies the long-duration protocol's 3,600-second per-condition success criterion, and no 15-minute breakpoint was observed in a completed long run.

## Safe integration steps

1. Preserve this audit and the failed custody findings as-is; do not rewrite old commits or silently repair hashes.
2. Recover the exact original answer bytes whose hashes appear in each run's commit marker, or declare those outputs unrecoverable. Re-run the frozen independent scorer only after a byte-for-byte commitment match.
3. Rebuild the dashboard index from the latest recovered receipts. Keep the old v5 snapshot identifiable as stale; distinguish recovered M08/M09 artifacts from the handoff's earlier `NOT_TESTED` entries.
4. Keep absent, unknown, undefined, failed, and unverified measures as explicit `null`/status values with reasons. Do not collapse them into zero.
5. Keep MMR `NOT_INTEGRATED` until the project MMR protocol, signed root, and verifier are actually integrated and exercised. A signed Git commit would still not substitute for the project MMR.
6. Do not mark an hour-scale condition complete until it has 3,600 seconds of usable measured inference, valid checkpoints, validated answer commitments, independent scoring, and reproducible custody. Preserve publication hold and separate local model runs from hosted Akamai runs.

## Audit limits

This report verifies selected package hashes, manifest entries, saved metadata, local receipt summaries, and answer-file hashes. It does not read model answers, independently rerun the GPU experiments, establish the full set of local/private files, verify the original remote host, or resolve missing source archives. The full evidence universe remains incomplete.
