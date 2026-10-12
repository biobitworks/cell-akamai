# Claude scientific lane — explicit review requests

Current Claude PR #5 owns Lane B. DO NOT let concurrent executor silently change scientific arms. The new orchestrator lane uses **your existing `run_lane_b.run_item()`** as the only policy source; this makes benchmark comparisons interpretable.

1. **Check arm fairness**: B0 one model call versus B1/B2/B3 three calls; note B2's blanket candidate critique versus B3's random specific-cell check may carry real information, so distinguish randomized-adversarial control from unrelated placebo. Do not describe B1 as the recovered Genesis policy (current `GENESIS_POLICY_PROXY_V0`).
2. **Independent scorer**: verify dataset hash, config hash and unique 4 arms × item coverage, and refuse unknown/missing arm rows prior to computing McNemar; currently `score_lane_b.py` only verifies `answers_sha256`, and its CLI source_class optional argument parsing is surprising. Label pilot `PILOT_NONCONFIRMATORY` and optionally compute tokens/correct item with explicit denominator.
3. **Anti-leakage**: no runner oracle import. Scorer should run only after answer commitment. Keep failed/over-budget answers incorrect even where syntax valid. Test fake model with oracle only as `SYNTHETIC_FIXTURE`, never counted as model performance.
4. **Live metrics**: consume `cXX_paired_for_scoring` from the new orchestrator concurrency lane and `bench_cells.json`; preserve stage/precision as verification-dependent, no performance claims before executed paired receipts.
5. **Science data**: ECA frozen 32 input records and SHA in `dataset/eca_pilot_manifest_v1.json`. Dataset has no ground truth. Work toward a separately held-out biologically meaningful oracle later; ECA does not validate biological science.
6. **Anticube / ΔG\***: maintain `NOT_COMPUTED` until explicit versioned predicates/formulas and controls. No weight updates => no DAISY training claim.

Report exact SHA, tests, failures and NEXT_ACTION in PR #5 or Issue #2. Preserve your active branch and upstream checkout.
