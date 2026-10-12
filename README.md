# cell-akamai

Akamai GPU inference measurement and scientific agent evaluation integration.

- **Lane A (ChatGPT + operator):** vLLM telemetry; deterministic request throughput (tokens/s) and inter-request acceleration (tokens/s²); FCO/FCG evidence projections; dashboard and notebook tests.
- **Lane B (Claude):** Genesis vs Vita DAISY/antigentic, held-out controls, scientific evaluation, and reproducible notebooks.
- **Runtime:** hosted Akamai JupyterLab (CPU notebook pod + separate GPU vLLM service).
- **Source of truth:** pinned commits, frozen inputs, raw receipts and GitHub PRs; not chat memory.

## Evidence boundaries
Existing offline Lane A tests passed 7/7 on 2026-10-12. Actual Akamai GPU execution, production model training, computed Anticube/ΔG* and committed MMR are **NOT_TESTED / NOT_COMPUTED** until supported by receipts. Local FCO/FCG projections are not authoritative admission. Stream chunks do not imply one tokenizer token per chunk.

## Workflow
Use isolated branches, reviewable PRs, and issues for handoffs. No secrets, private biological data, credentials, model weights or raw run data in Git.
