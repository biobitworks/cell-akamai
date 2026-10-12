# EXP_001: hour-scale controlled inference

State: IMPLEMENTATION_AND_PREFLIGHT_PENDING. Parent: concurrency-07-bf16_fullmatrix_reference-20261012T203417Z-225f0b49. Prior pilot results are separate.

Protocol: ../docs/HOUR_SCALE_EXECUTION_PLAN.md. User instruction in this chat is prompt provenance. Source SHAs are recorded at checkpoint publication and per run. Claim ceiling: observed inference measurements only; no training or causal scientific improvement.

Validation:36 deterministic unit tests pass locally. Direct runner excludes oracle datasets and warm-up, checks duplicate IDs/custody/identity, writes private answer ledger and public aggregate snapshots. No hour-scale GPU run has started. Policy/original-workshop adapters and live health watchdog remain pending. Hardware identity needs fresh hosted verification.

Decision: finish/recover existing serialized GPU pipeline first; publish current evidence; admit new traffic only after complete preflight and remaining runner validation.

Protocol update: EXP-CAKM-MULTIMODEL-6DATA-LONGRUN-001 in docs/LONG_DURATION_PROTOCOL.md supersedes184-hour design. Twelve300-second active windows/representation/configuration. No laptop cluster deployment; existing hosted workshop only. Evaluator inference admission unresolved; oracle targets prohibited. No new hour-scale GPU traffic.
