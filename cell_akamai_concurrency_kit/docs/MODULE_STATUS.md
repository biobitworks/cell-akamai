# Workshop 00–09 × Cell-Akamai status (successor, 2026-10-12)

Statuses distinguish operator-observed, independently inspected, implemented, and unexecuted states. The full CSV and machine-readable dataset contract ship in `CELL_AKAMAI_CONCURRENCY_KIT.zip`.

| Module | Existing upstream foundation | Cell-Akamai state | Next piece |
|---|---|---|---|
| 00 Connect | namespace/workshop runtime | PARTIAL_OBSERVED (pods/models API) | bind pinned environment |
| 01 Inference stack | model service and request tracing | PARTIAL_OBSERVED (two predecessor run descriptions) | trace agent request graph |
| 02 Units/memory | arithmetic | NOT_REVIEWED | memory budget w/ assumptions |
| 03 Prefill/KV | telemetry/time metrics | PARTIAL_OBSERVED (token kinetics reference) | in-flight KV monitoring |
| 04 Dense/MoE | roofline analysis | NOT_TESTED | no unsupported live MoE |
| 05 Quantization | FP8 workshop benchmark | NOT_TESTED | matched precision experiment |
| 06 Speculative decoding | FP8+0.6B drafter workshop | NOT_TESTED | matched on/off only |
| 07 Saturation | `common/loadtest.py` + `/metrics` | PILOT_READY_NOT_EXECUTED | bounded B0–B3 concurrency |
| 08 Tune/evaluate | serving-policy tuning | NOT_TESTED | observed quality guardrails |
| 09 Agents | workshop agent path + Claude B0–B3 draft harness | PILOT_READY_NOT_EXECUTED | pilot ECA accuracy/cost |

**Corrections:** Module 07's upstream helper increments its token counter per nonempty stream chunk; our server-token metric uses `usage.completion_tokens`, which is not equivalent. B1/B2 are labeled PROXY, not trained native Genesis/Vita DAISY. Existing original-model runs are predecessors, not proof of speculative or FP8 gains. `qwen_original_reference` is user-reported 451 server tokens with no speculation; full second ZIP not independently inspected. The user-local `/Users/byron/Downloads/CELL_AKAMAI_EVIDENCE_EXPORT.zip` was inaccessible in this ChatGPT runtime.

**Upstream pin:** `akamai-developers/akamai-workshop-ai-inference@454b43269216c1f92dd8d7e2711649e38cb888cb`. **GitHub Lane A branch:** `lane/a-concurrency-eca`; source includes ECA calibration/pilot task items and proposed holdout task items, separate evaluation script, local breakpoint. **Holdout answer key** remains only in separate user-deliverable ZIP to reduce cross-lane leakage.
