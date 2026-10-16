# Hackathon Protocol A — Agentic vs Antigentic, a falsifiable comparison

**Status:** PREREGISTRATION PROPOSAL / NOT_EXECUTED. Event mapping: `NEEDS_OPERATOR_CONFIRMATION`. **Owner:** Cell-Akamai. **Source:** current Cell-Akamai branch, not shared federation storage. **Coordination:** Claude Code as experiment implementer; ChatGPT/Ollarma as non-signing hypothesis challenger/PI-PM coordination only.
**Parent:** CHAT-CELLICO-GOLDEN-DATASET-STRESS-20261016-001.

## Question and controls
Does governed antigentic challenge improve independently verified correctness **at matched ordinary compute budget**, beyond merely giving an agent more inference?
Use frozen task groups, not cases selected posthoc for a demo:
- **A BASELINE:** one proposing agent + unchanged deterministic validation.
- **B EXTRA-COMPUTE:** proposal + additional neutral self-review/retry tokens/time matched to C.
- **C ANTIGENTIC:** proposal + distinct critic trying to falsify claims, followed by bounded correction and deterministic admission gate.
Keep identical underlying model, task, prompt prefix, allowed context, scorer, infrastructure and randomized arm order. Freeze budgets, tokens, wall time and task eligibility.

## Precommit H0/H1 before running
- Primary outcome: independently recomputable correct-and-admissible task outcome at source-task-group level, counting abstention separately.
- H0: mean paired (C-B) improvement <= minimum useful delta, where delta is justified and frozen before seeing outcomes. H1: improvement > delta.
- Safety: false admission in C is not worse than B beyond preregistered noninferiority margin; required gate for promotion.
- Secondary: latency, money/tokens, abstention, recovery after poisoning, rate of invalid roots, score/calibration and failure distribution.
- Use at least three distinct stochastic seeds (`17,42,73` only if preregistered); each same-seed rerun is REPEATABILITY, not an independent biological study. For correlated tasks, resample independent task groups; never treat repeated messages/tokens as independent N.
- Paired randomization or exact McNemar if assumptions permit; cluster-level bootstrap CI, effect size, corrected p where planned; quantify power/precision. Never assert significance based only on three seeds or a few demonstration examples.

## Golden dataset / protocol fixtures
Select a minimal independently checkable, license-valid frozen source; include clean, poisoned, stale, missing, fabricated-claim and valid-but-unusual tasks. Record frozen source/answer/oracle identity and leakage review. No customer/private messages, provider secrets or competition holdout leakage. Synthetic fixtures test governance, NOT biology.

## Implementation order for Claude Code
1. Recover this repo's `AGENTS.md`, lane A/B ownership, existing preregistration `lane-b`, source commit and current worktree. **Do not overwrite ongoing GPU/hour-long inference jobs**.
2. Define `ExperimentFCO` with dataset freeze, allocation algorithm, arms, seed schedule, independent unit, assumptions, H0/H1, MESI, margin, primary metric, null control, exact test command and falsification/failure criteria; freeze before measuring.
3. Implement/execute the **smallest local bounded offline pilot** using existing authorized fixtures, if independent oracle available; no paid provider calls or external hackathon form submissions without authorization.
4. Record **each** raw run outcome and failures: signed/not-signed status, exact code revision, run seed, token/cost usage, structured trace SHA, observation, independent judge record, `ABSTAIN`, `FAIL`, `NOT_TESTED` or `SUPPORTED`.
5. Produce one 2D effect plot and a Markdown results table only if numerical evidence actually exists; use exact CI/test formulas, multiple-testing family, and outcome counts.
6. Commit only to a clean isolated branch/worktree; expose cross-project handoff by verified commit and hashes; do not alter old releases.
7. End with mandatory ConversationFCO breakpoint, predecessor identity, verification output, unresolved tests and no inflated claims.

**Not authorized:** human PI signoff, new VCC submission, uncontrolled spend, changed provider credentials, live credential dumps, live project graph write or PublicationMMR append.

## Handoff
Return `GOLDEN_ROUTE_HACKATHON_A_EXPORT.json` with `repo_head, dataset_fco, prereg_fco, run_fcos[], negative_fcos[], statistical_result_fco, analysis_status, root_kind, merkle_root_if_verified, verification_receipt, operator_review_needed`.
