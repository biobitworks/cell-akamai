# EXP-LANEB-GDAISY-001 — Preregistration (DRAFT v0.1, UNFROZEN)

**Status: DRAFT. Nothing here has been executed. No result exists.** Freezing requires
operator approval and a recorded freeze hash (see §11). Every `[UNFROZEN]` item must be
fixed before any scored run. Items marked `[RECOVERED]` come from existing artifacts and are
hash-referenced, not re-derived.

Owner lane: Lane B (Claude). Exchange file: `data/lane_b_results.jsonl`
(schema `cell_akamai.lane_b_result.v1`). Governance: GettingScienceDone / `gsigmad-*`
(`gsigmad-create-prompt`, `gsigmad-claim-ceiling`).

## 1. Question and hypotheses

Question: under an equal compute budget, does adding independent adversarial ("antigentic")
evaluation to an adaptive-orchestration policy change correctness on a deterministic-oracle
task, relative to (a) a fixed model, (b) adaptive orchestration alone, and (c) the same
extra compute spent on randomized (uninformative) challenges?

- H0-1 (primary): accuracy(B2) = accuracy(B3).
- H1-1: accuracy(B2) != accuracy(B3), paired by item.
- H0-2: accuracy(B1) = accuracy(B0). H0-3: accuracy(B2) = accuracy(B1).
- Directional predictions are NOT preregistered; two-sided tests only.

## 2. Task and frozen oracle

- Task family `[RECOVERED]`: elementary-cellular-automaton (ECA) next-state prediction,
  width 8, rules {30, 90, 110, 184}, from RUN001 policy `GENESIS_DAISY_PROSPECTIVE_MULTI_EVENT_V1_20261008`
  (RUN_POLICY_FREEZE.json sha256 `b43685f37e0ae0d3d9babbda111487dca557c82fdb163a26c3805ec0c1304a8a`;
  fixture sha256 `eb36c766cbf76353f9981cb3a3aa32137622d1de53b29d861c483742bcd4dec7`).
- Oracle: deterministic ECA evolution implemented independently of every arm. The oracle
  scores only; no arm receives oracle output, oracle code, or ground truth at any step.
- The four RUN001 panel questions (seeds 41031–41034) are **excluded** from scoring
  (calibration/exposure set). Scored items use a disjoint seed range `[UNFROZEN]`.
- Scope limit: this is a synthetic computational control. It says nothing about biology,
  scientific discovery, or general capability.

## 3. Arms (identical items, split, scorer, per-item budget)

| Arm | Definition |
|---|---|
| `B0_FIXED` | One model, one fixed prompt template, greedy decoding, single call per item. |
| `B1_GENESIS` | Genesis adaptive orchestration: policy may re-query or re-allocate budget based on its own prior outputs only. Policy code bound to a source commit `[UNFROZEN: bind recovered Genesis policy or specify new]`. |
| `B2_GENESIS_DAISY` | B1 plus a Vita DAISY antigentic stage: an independent challenger call critiques the candidate answer without oracle access; a pre-specified selection rule picks the final answer. |
| `B3_RANDOM_CONTROL` | B1 plus the same number/length of challenge calls as B2, but challenge content is randomized/uninformative (seeded shuffle of critique text). Controls for extra compute and extra context. |

No-leakage rule: the oracle result is computed after the final answer is hash-committed.

## 4. Models and hosts `[UNFROZEN]`

- Host A: Akamai workshop vLLM, Qwen3-4B (exact revision UNKNOWN until read from the endpoint).
- Host B (optional shakedown): magicSTUDIObox, same prompts/items, plus a Liquid AI model whose
  exact identifier and revision are UNKNOWN and must be recorded before use.
- Model revisions and tokenizer revisions stay `UNKNOWN` until bound to verified artifacts.
- Cross-host cost numbers are not comparable; report per host.

## 5. Compute budget

Equal across arms: per-item cap on total completion tokens `K` and on model calls `[UNFROZEN]`.
Arms may not exceed `K`; overruns count as the arm's failure on that item. B2 and B3 use identical
call counts. Sampling: temperature 0 unless an arm requires otherwise `[UNFROZEN]`; seeds frozen.

## 6. Sample size `[UNFROZEN]`

No power analysis has been run, so no confirmatory N is claimed. Proposed phases:
- Pilot (shakedown, **non-confirmatory**, results labeled PILOT): small fixed N to test the harness.
- Confirmatory: N set by power analysis from pilot variance, frozen before the confirmatory run.
Fixed N, no optional stopping, no peeking-based extension.

## 7. Metrics

Primary: exact-match accuracy of the predicted next row (fraction of items).
Secondary: mean Hamming error (fraction of cells); abstention rate; parse-failure rate;
total completion tokens; wall-clock seconds; request tokens/s (Lane A definition: completion
tokens / request wall duration).
Parse failures and over-budget outputs count as incorrect (not excluded). Abstention counts as
incorrect for accuracy and is also reported separately.

Anticube (operational) and ΔG* — see §9. Both default `NOT_COMPUTED`.

## 8. Analysis plan

Paired per-item correctness. Primary: exact McNemar test, B2 vs B3. Secondary: B1 vs B0,
B2 vs B1, Holm correction across the three secondary/primary contrasts, alpha 0.05 two-sided.
Report effect as paired difference with a bootstrap CI (seed frozen). Tokens/s² from Lane A is a
descriptive cost diagnostic only, not a correctness or knowledge measure.
Exclusions: none after freeze; failures are retained with status FAILED.

## 9. Anticube and ΔG*

- Anticube (operational, `[UNFROZEN]` predicates): proposed per-item decision via schema
  `anticube_assessment.schema.json` (v1.3.0) from deterministic predicates (well-formed output,
  source/prompt hash valid, within budget, no oracle access). Must include negative-control cases
  (tampered item, over-budget, oracle-leak attempt) before any "safe" classification is reported.
  Biological selfness/safety: NOT_TESTED. Until predicates are frozen: `NOT_COMPUTED`.
- ΔG*: **NOT_COMPUTED.** Recovered evidence: `GIBBS_DISCOVERY.json` reports
  `GIBBS_SCORING_STATE=PARTIAL` and multiple non-interchangeable G* formulas;
  `delta_graph_star.py` defines a six-component vector with scalarization forbidden without
  preregistration; RUN001 recorded `canonical_G_star=NOT_COMPUTED`. No formula ID is bound, so
  no numeric ΔG* will be reported. KL(q‖uniform) may be reported only under its own name and
  never as ΔG*. Not physical Gibbs energy.

## 10. Claim ceiling

PASS here would mean: on this synthetic deterministic task, under this budget, arm X's
observed accuracy differed from arm Y's by the measured amount. It does **not** show
generalization, causal superiority of antigentic evaluation outside this task, biological
validity, or scientific-intelligence claims. Chunk counts are not token counts; TTFC is not TTFT.

## 11. Freeze procedure and custody

1. Resolve all `[UNFROZEN]` items. 2. Operator approves. 3. Compute sha256 of this file and
`preregistration.draft.json`; record in `.../decision_log.jsonl` before running.
4. Independent evaluation: a separate script/process computes oracle scores from committed
answer hashes. 5. Each result row cites an `evidence_ref`; FCO occurrence ids are filled only
when a real FCO exists. Project MMR: NOT_COMMITTED. Signing: NOT_SIGNED.
