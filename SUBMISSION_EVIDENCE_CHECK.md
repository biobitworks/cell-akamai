# Submission evidence check

**Checked source:** `721e325721509a612f9e58616c5ac6c651aa07ab` (full Git SHA; branch working tree also contains the pre-existing untracked `SUBMISSION_READY.md`). Related results PR: [#12](https://github.com/biobitworks/cell-akamai/pull/12). This note uses only the checked-in evidence package and local deterministic tests; recovered operator receipts are labeled as such and were not rerun here.

## Claims supported for a demo

- **Offline implementation and custody transforms:** `evidence/20261012/successor/OFFLINE_VERIFICATION_REPLAY.json` reports PASS. Three role fixtures have 32 rows each, exact payload reconstruction, and recorded SHA-256 digests; the nine-file local Merkle construction is explicitly not the project MMR. These are structured fixtures derived from the ECA pilot, not recovered historical Genesis/Vita DAISY/evaluator datasets. Actual Genesis and DAISY model execution remains untested.
- **Source test suite:** `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests/hour_scale tools/recovery/test_package_evidence.py evidence/20261012/successor/tests` → **42 passed** (0.45 s), with one environment warning: urllib3 reports LibreSSL 2.8.3. These deterministic tests do not establish GPU behavior.
- **Short Module 7 inference measurement:** the recovered workshop07 summary records Qwen/Qwen3-4B, BF16 target, 8/8/16/32 successful requests at concurrency 1/2/4/8, zero HTTP failures, and usage-token throughput of 38.25/74.73/142.85/269.01 completion tokens/s. At c=8 p95 request latency was 1,261.6 ms. It is a short workload-specific benchmark, not an hour-scale result. The source SHA is the upstream workshop commit `454b43269216c1f92dd8d7e2711649e38cb888cb`; deployment image digest and hardware are not attested.
- **Short Module 8 paired sample:** recovered before/after summaries each show 16/16 requests succeeding at c=1,4,8,16. At c=8 observed completion throughput is 273.25 tok/s before and 265.05 tok/s after; p95 latency 1,061.3 ms before and 1,130.5 ms after. The eight-request frozen quality panel scored **0/8 exact matches both before and after**. This does not support a performance or quality improvement claim; the receipt itself limits causal interpretation.
- **Negative pilot result:** recovered B0–B3 summaries report all 8 items failed, abstained, or exceeded budget in each arm; no arm demonstrates successful correctness. The ECA pilot is synthetic/non-confirmatory, B1 is a Genesis proxy, call budgets differ, and challenge information is not matched. The six-dataset paired run committed raw answers for 8 items but left them unscored (`RAW_ANSWERS_COMMITTED_UNSCORED`).

## Blockers and boundaries

- The hour-scale plan declares a 184 measured-GPU-hour matrix plus overhead, but there are **no hour-scale results**. Runner/dashboard tests and synthetic test metrics are implementation evidence only.
- Module 9 notebook status is FAILED: port-forward exited while checking pod/service readiness. Do not claim a live agent deployment or successful tool invocation from this evidence.
- The evidence export has incomplete/unknown provenance for some recovered receipts (including hardware, source commit, workload/config fields). These remain recovered receipts, not fresh reproducibility runs.
- Training, weight updates, self-training, `ΔG*`, causal improvement, project MMR, and signatures are not established. Keep raw model responses and private response ledgers off-screen; show only whitelisted aggregates and sanitized receipts.

## Primary local evidence references

- `evidence/20261012/recovered/CONSOLIDATED_RUN_INDEX.json`
- `evidence/20261012/recovered/runs_workshop07/workshop07-bf16-1eae5794b87a44a78ce767ae0750a8d4/summary.json`
- `evidence/20261012/recovered/successor/epochs/M08_before_20261012T205049Z_9edc4db/summary.json`
- `evidence/20261012/recovered/successor/epochs/M08_after_20261012T205246Z_ef7cf71/summary.json`
- `evidence/20261012/recovered/successor/epochs/M08_QUALITY_before_20261012T205112Z_44f9f53/quality_summary.json` and corresponding after summary
- `evidence/20261012/recovered/successor/epochs/M09_ECA_B0_B3_20261012T205324Z_56da8fa/COMMIT.json`
- `evidence/20261012/recovered/successor/epochs/M09_SIX_DATASET_COMPARE_20261012T205637Z_6c1963b/COMMIT.json`
- `evidence/20261012/recovered/successor/81_m09_agent_and_daisy_STATUS.json`
- `evidence/20261012/successor/OFFLINE_VERIFICATION_REPLAY.json`
