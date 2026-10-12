---
name: Lane B Genesis/Vita DAISY scientific evaluation
about: Claude science lane and versioned cross-lane export
labels: ['lane-b', 'msm']
---

## Deliverable
Recover predecessor R3 checkpoint and MSM protocol, freeze controls/held-out split, compare B0/B1/B2/B3. Output `data/lane_b_results.jsonl` conforming to `schemas/lane_b_results.schema.json`.

## Acceptance
- [ ] Scientific preregistration and checkpoint/dataset exact identities
- [ ] Frozen test oracle and negative controls
- [ ] Human/machine reproducible notebook and tests
- [ ] Explicitly distinguish actual weight training from policy-only adaptation
- [ ] Real Anticube/ΔG* only with recovered calculation and independent validation
- [ ] State `NOT_COMPUTED` where absent; no invented model improvements
- [ ] Commit SHA and reviewed PR supplied to Lane A
