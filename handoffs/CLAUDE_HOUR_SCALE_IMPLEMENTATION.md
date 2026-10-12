# Claude: finish hour-scale runner, tests and live checkpoint support

You own implementation and local deterministic verification. Codex owns live workshop GPU execution, deployment changes, evidence intake and results-branch publication. You are not alone in this codebase: do not revert others' edits. Do not send any inference requests, patch Kubernetes or start benchmark workloads. Do not modify frozen datasets or prior receipts. Never expose raw responses, credentials or kubeconfig.

Repository: https://github.com/biobitworks/cell-akamai
Results PR: https://github.com/biobitworks/cell-akamai/pull/12
Results branch: lane/akamai-m08-m09-results-20261012
Verified remote checkpoint SHA:51ebbcef144d7016939f3fc0682806ddbcd0d01a
Issue reporting: https://github.com/biobitworks/cell-akamai/issues/1#issuecomment-6132552207

Use a NEW isolated worktree and branch codex/hour-scale-implementation-claude from that SHA. Fetch first. Read AGENTS.md, docs/CONCURRENCY_EXECUTION_RUNBOOK.md, docs/HOUR_SCALE_EXECUTION_PLAN.md, experiments/EXP_001_HOUR_SCALE.md, CLAUDE_HANDOFF.md and existing receipts. Preserve source provenance; no invented execution metrics. Write a JSON/JSONL handoff alongside Markdown.

Ownership: tools/hour_scale/, tests/hour_scale/, new implementation documentation. Do not edit tools/recovery/, frozen evidence/20261012/successor/data/, existing evidence or the results branch directly.

Current implementation: direct prompt runner supports usage-token HTTP traffic,60min minimum, warm-up exclusion, flock, deterministic cyclic inputs, private response ledgers and atomic aggregate snapshots. Dashboard whitelists fields and retains last valid snapshot.36 total local tests pass. This is incomplete and is NOT approved for live execution until your review/fixes pass. No hour-scale cell has started.184-hour proposed matrix is a declaration, not completed work.

Priority1: correctness/admission hardening
- Audit tools/hour_scale/runner.py. Fix failure/unknown-usage denominators, measured-duration vs budget exhaustion states, invalid parameter checks, preflight binding to current config/precision/source, ledger commitment and crash/failure checkpoint handling.
- A supplied preflight JSON alone is not proof of live identity. Design injectable live checks before each cell and a bounded watchdog for model/config drift, health/OOM and external load. Never infer competing traffic solely from total running requests when own traffic is active; document limitations.
- Validate actual token and request budgets before admission, including prompt sizes/context limits. Ensure warm-up cannot consume the measured budget silently.
- Avoid rereading/hashing the entire ledger or retaining all raw responses in memory on every checkpoint. Preserve replayability and exact commitment semantics.
- Add first measured interval, periodic15min, failure and final checkpoint events; UTC/PDT timestamps, measured/drain windows, run/parent IDs, source/config/dataset hashes, completed/expected cells and explicit states. Preserve append-only snapshots.
- Validate frozen dataset/schema, duplicate item/occurrence IDs, all links across roles and exact original/FCO/FCG reconstruction. Evaluator/oracle records must NEVER enter model prompts.

Priority2: adapters and metrics
- Implement hour-scale adapters for pinned Lane B B0–B3 without importing oracle/scorer into inference. Pin PR5 SHA73001e73eeada4aee4f3b32fa4a0671cca255601 and harness digest. Commit raw answers before independent scorer; scorer wrapper must verify answer/config/dataset SHA and coverage. Do not label direct fixture prompting as actual Genesis/DAISY policy execution.
- Implement original workshop Module07 adapter separately, pinned workshop454b43269216c1f92dd8d7e2711649e38cb888cb. Count verified usage tokens, never SSE chunks.
- Add optional streaming timing only with scientifically defensible token/chunk semantics. TTFC is not TTFT. If token timing cannot be verified, retain NULL metrics and explicit reasons. Keep output/input throughput[tokens/s], requests/s, p50/p95/p99 latency[ms], active/waiting[requests], concurrency[sessions], duration[s]. Label completion-attributed1s bins accurately. Do not fabricate tokens/s².
- Preserve HTTP/transport/timeouts, parse, truncation and quality failure categories. No hidden retries; distinguish emitted, HTTP-success and independently valid-answer throughput.
- Provide serial epoch orchestration contract for BF16/FP8/FP8+drafter/BF16one-knob and baseline restoration in finally. Implementation only: actual deployment transitions stay Codex-owned. Unsupported configurations are NOT_TESTED with reasons.

Priority3: checkpoint publication/dashboard
- Implement a LOCAL dry-run-first publication helper: aggregate schema validation, secret/raw-field scan, atomic snapshot, relevant tests, commit/push and ls-remote verification, Issue1 body artifact, Claude handoff. Publish only explicitly whitelisted sanitized aggregate files. Never include runs/ledgers/raw notebook outputs. A push failure retains checkpoint and reports unpublished state.
- Avoid self-referential commit SHA: handoff identifies the verified checkpoint commit; a following handoff commit may cite it. Do not claim a file contains its own resulting Git SHA.
- Improve live walkthrough dashboard: latest checkpoint SHA, last successful refresh, current cell, elapsed/target, completed/expected, provisional vs scored, failures/units; exact private-field allowlist including nested structures. Serve loopback only. Actual summary updates must change displayed data without GPU restart.

Tests: meaningful deterministic fixtures labelled SYNTHETIC_TEST_ONLY. Cover metrics denominators/units/percentiles/empty/failed/unknown samples; token-vs-chunk; concurrency and serialization; warm-up and budget exhaustion; no retries/duplicates; custody/links/oracle separation; tampered commitments/config/dataset; crash checkpoints; dashboard partial writes and redaction; export CRC/hash integrity. Test mocked transport failures, not just implementation-shaped happy paths.

Deliver in stages: first review findings + failing tests, then corrected minimal runner/admission, then adapters, then dashboard/publisher. Run local tests; commit and push YOUR implementation branch and open a reviewable PR referencing #12/#9/#1. Do not merge or cherry-pick into the results branch. Return full SHA, PR URL, tests, files changed, known limits and exact Codex integration steps. Include handoff JSON. No training/improvement claims.

Known pilot findings:16BF16cells executed,128/128 policy-item parse/budget failures. Module07 usage-token short baseline succeeded. Module08 max-num-seqs32→64 short pilot executed, no independent speedup established. Module09 sa-agent port-forward failed; code-server workspace namedagent is not the Solution Architect agent. Current live max-num-seqs was64 at last check; Codex must restore32 after confirming idle. Hardware query was launched but its result has not yet been recovered.
