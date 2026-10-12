---
name: Lane A telemetry + dashboard
about: Akamai vLLM request telemetry, deterministic tokens/s², dashboard and readback
labels: ['lane-a', 'inference']
---

## Deliverable
Execute `notebooks/10_token_kinetics.ipynb` against the existing hosted vLLM Qwen3-4B endpoint; retain source digests and summary; review `lane_a_dashboard.html`.

## Acceptance
- [ ] Four real streamed requests with server-reported usage or explicit UNKNOWN
- [ ] Unmodified sampled Prometheus bytes with verified SHA-256
- [ ] tokens/s and inter-request tokens/s² locally recompute
- [ ] FCO content/occurrence and typed FCG edge local readback passes
- [ ] No fake results presented as OBSERVED
- [ ] No GPU or cluster mutations
- [ ] Links to run summary, SHA, notebook execution evidence and PR

## Claimed status
NOT_TESTED until run receipts are reviewed.
