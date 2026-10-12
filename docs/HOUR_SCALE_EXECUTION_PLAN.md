# Superseded plan — preserved for provenance

The authoritative protocol is LONG_DURATION_PROTOCOL.md, experiment EXP-CAKM-MULTIMODEL-6DATA-LONGRUN-001. The older184-hour per-concurrency allocation below is superseded by twelve300-second windows per representation/configuration. No hour-scale traffic was executed under the old plan.

# Hour-scale evaluation declaration

Declared before any hour-scale traffic. Prior short pilot runs are preserved and do not satisfy this study.

## Matrix and budget

Each valid cell requires >=3,600 measured seconds, plus 60 seconds of warm-up and request drain. Closed-loop deterministic cyclic scheduling; temperature 0, maximum completion 256 tokens, no automatic retries. Concurrency 1,2,4,8; c16 excluded pending independent capacity verification.

Four separate serving epochs: BF16 baseline; FP8 without drafter; FP8 with a supported drafter (single speculation change from FP8); BF16 with max-num-seqs 64 (single change from baseline32). All need freshly verified live identity, hardware, permission and idle receipts. Restore each epoch's parent baseline after the experiment. Unsupported configurations receive NOT_TESTED receipts, never substitute measurements.

- Genesis and Vita/DAISY fixture roles × original/FCO/FCG resolution × four concurrency levels =24 cells/epoch,96 hours across four epochs.
- Frozen ECA B0–B3 policy workloads × four concurrency levels =16 cells/epoch,64 hours. These need the independently pinned Lane B harness adapter; the direct prompt runner must not be labeled B1/B2/B3.
- Original workshop Module07 fixed workload × four levels × four epochs =16 hours, separately measured with usage tokens.
- Eight independent repeat cells: two baseline and two candidate cells at c1 and c8 =8 hours. Freeze their exact selection before candidate results are opened.
- Total planned measured GPU time:184 hours. Warm-up:184 minutes (3h04m), plus rollout, readiness, drains, scoring and publication. Execution is serialized; this cannot finish in one event afternoon.
- Per-cell hard cap:100,000 requests,25,600,000 completion tokens at max256. Whole declared matrix upper bound:18,400,000 requests and4,710,400,000 completion tokens. Actual input usage is recorded; input budget needs tokenizer-verified prompt sizes before each adapter is admitted. These are safety bounds, not predicted traffic or billed cost.

FCG files are edge lists. FCG-resolution cells resolve linked FCO payloads; they do not feed graph edges as a replacement prompt. Original/FCO/FCG resolve identical prompt bytes, so this measures custody/lookup paths with equal model inputs, not prompt compression. Evaluator originals/FCO/FCG contain oracle answers: OFFLINE_ONLY, prohibited GPU inputs. Historical actual Genesis/DAISY model-role execution remains NOT_VERIFIED; these fixtures do not establish those roles.

## Admission and stopping

Preview all dataset digests/reconstruction and exact payload sizes. Require preflight <=5minutes old, namespace workshop-s05, served model, verified precision, actual GPU identity, get/patch permissions, deployment argument SHA and idle state. Every benchmark process must respect the shared flock; additionally check cluster metrics for noncooperating loads. Existing recovery pipeline must finish before this runner starts.

Stop immediately on lost namespace/model identity, GPU OOM/server health failure, overlapping external workload, custody/hash failure, operator cancellation or hard budget exhaustion. Preserve partial receipts as INCOMPLETE/FAILED. Never shorten duration and label it complete. On timeout preserve the failure without retry. Before a new cell, refresh health/identity/idle and admission. Initial implementation provides direct prompt cells; policy/original-workshop hour adapters and live health watchdog remain pending validation and must not start until implemented.

## Metrics and checkpoints

Usage tokens / unrounded measured wall time are tokens/s. A request completing after the admission window is counted with its drain time included in the denominator. Warm-up requests are excluded. HTTP success is not scientific answer validity. Missing usage makes usage-derived throughput unknown. Current nonstreaming adapter reports TTFT/inter-token/decode timing NULL; completion-binned tokens are explicitly attributed at completion and are not token-emission timing.

Checkpoints: preflight/tests; warm-up; first measured result; every15minutes; each cell; failures/config changes; scoring/archive verification. Atomic aggregate-only JSON snapshots carry monotonic checkpoint IDs. Keep raw responses in ignored private runs; commit their digests before independent scoring. Dashboard retains last valid snapshot on partial writes. Publish verified partial evidence and label it PROVISIONAL. No improvement/training claims.
