# Takeover checkpoint — 2026-10-12

Branch: `codex/demo-contributions-20261012`.
Verified pushed content commit: `d123ba76cf6b02d291bdabf77cd1f9de735a5dfd`.
Review: https://github.com/biobitworks/cell-akamai/pull/16 (base: `codex/signed-evidence-checkpoint`).

## Ready for demo
- `docs/FINAL_DEMO_SCRIPT.md`: timed problem / stack / demo+code narration.
- `docs/WORKSHOP_ADDITIONS.md`: local/cloud pilots, deterministic fixture reconstruction, controls, custody and measurement corrections.
- `docs/EVIDENCE_COVERAGE_AUDIT.md` and `evidence/attestation/COVERAGE_AUDIT.json`: module coverage, missing evidence, recovered commitment mismatches, null taxonomy and Merkle requirements.
- Local dashboard on http://127.0.0.1:8771/ has the contribution section; reload an existing tab to see it. Data comes from canonical ignored `runs/concurrency`, not fabricated fixtures.
- 14 focused tests passed, Python compilation and diff check passed. HTTP and browser checks verified contribution copy.

## Preserve
Do not reset Claude's dashboard branch, external narration or canonical uncommitted harness edits. Do not publish raw answers, private backup, credentials or kubeconfig. Existing frozen data and completed receipts are immutable.

## Blockers and limits
- Repository last verified PRIVATE. Main is initialization, not integrated release. This branch is pushed for review, not merged into main.
- Scoped license prep is on separate `codex/public-release-audit`, commit `a500c7f18c4651d5e0a2c15c4f3c06bc2ec866de`; original code Apache-2.0, original noncode CC BY-NC-ND 4.0, third-party rights preserved. Workshop material provenance still needs resolution before public release.
- History gitleaks finding classified as manifest SHA-256 false positive. A clean scan is not a full licensing/raw-data audit.
- Recovered answer-ledger commitments fail; do not promote their bundled scores to verified. Keep distinct from canonical small scored pilots.
- Project MMR integration, complete long-duration breakpoint evidence, training and scientific improvement remain unestablished.
- No sustained benchmark or puller was active at last direct check. Do not claim runs started. One shared-GPU workload only.

## Next safe actions
1. Fetch branch and verify remote SHA before using demo assets.
2. Reconcile recovered commitment failures against exact original bytes; never rewrite commitments to force acceptance.
3. Resolve release provenance; integrate reviewed branches via PR, then verify public visibility only after audit.
4. Resume authorized serialized inference only after frozen preview, preflight and idle checks pass; privately recover checkpoints while keeping raw outputs off GitHub.
5. Check HackerSquad recording/submission confirmation; saved project details are not a submitted video.
