# Cell-Akamai — auditable scientific agent evaluation

We extended Akamai’s inference workshop with a Strands role-separated design, real local/cloud evaluation, reproducible data representations and inspectable evidence.

## Verified achievements

- **First experiment: tokens/s and tokens/s².** EXP-AKAMAI-TOKEN-001 measured four sequential requests. Three throughput-change calculations independently reproduce: **0.19004143, 0.00768947, 0.00554005 tokens/s²**. [Calculation receipt](evidence/20261012/TOKEN001_RECOMPUTED.json).
- **Real GPU concurrency.** The original Module 7 short concurrency-eight experiment recorded approximately **269 output tokens/s, 1,262 ms p95 latency and zero HTTP failures**. These are serving measurements.
- **Local and cloud pilots.** Local Ollama Llama 3.2 3B and Akamai vLLM Qwen3-4B were exercised with the evaluation harness; small canonical scored panels preserve observed negative task outcomes. Different models and hardware remain separate comparison families.
- **Strands compatibility.** Actor, challenger, randomized control and adjudicator roles are implemented and fixture-tested. A tool-free Strands call to Akamai succeeded. The measured scientific pilots used the plain OpenAI-compatible client.
- **Deterministic data custody.** Thirty-two frozen synthetic ECA tasks reconstruct exactly across original records and FCO/FCG representations, preserving hashes and declared relationships. These are paired representations of the same tasks.
- **Tested evidence handling.** Strict answer parsing, commitment/configuration/coverage checks, partial-failure accounting and dashboard checks make evidence reviewable. A short Module 8 tuning pilot preserved its negative finding.

## Demo and review

[Recording script](docs/FINAL_DEMO_SCRIPT.md) · [Workshop additions](docs/WORKSHOP_ADDITIONS.md) · [Modules 1–9 and local coverage audit](docs/EVIDENCE_COVERAGE_AUDIT.md) · [Recovered execution context](docs/RECOVERED_PUBLICATION_README.md)

Start the loopback dashboard from a checkout containing saved run summaries:

```bash
python3 tools/concurrency/serve_dashboard.py --runs /path/to/private/runs/concurrency --port 8771
```

Open http://127.0.0.1:8771/ for current aggregate summaries and the first tokens/s² experiment; `/evidence` replays the imported catalog with historical-label explanations. This repository omits private raw responses and credentials. A fresh clone needs actual saved summaries to populate current local/cloud panels.

## What deterministic means here

1. Identical frozen input bytes have identical SHA-256 identities.
2. Original/FCO/FCG fixture reconstruction reproduces the same records.
3. The declared rate formula reproduces the recorded arithmetic from the same numeric inputs.
4. Commitment checks deterministically accept matching bytes or reject mismatches.

These establish data identity, transformation fidelity and calculation reproducibility. Model answers can vary. A signature or Merkle root establishes covered-artifact integrity under its verification assumptions, rather than answer correctness or scientific improvement.

**Units:** request throughput = completion tokens / request wall duration [tokens/s]. Sequential rate change = difference in request throughput / request-midpoint separation [tokens/s²]. Aggregate concurrency throughput uses total completion tokens / measured batch wall time [tokens/s]. Streaming chunks are not tokens; first-chunk latency is distinct from server TTFT.

## Outcome interpretation and next validation

Recorded measurements, negative task results, failed operations, missing metrics and unrun configurations are different outcomes. The evidence catalog preserves older labels; later M08/M09 receipts are described in its execution update. Some recovered answer files fail their commitments, so affected bundled scores remain excluded pending reconciliation. Zero correct answers makes tokens/correct undefined; it does not erase throughput observations.

Next: sufficient answer budgets, independent repeated comparisons, serialized hour-scale runs and complete project MMR integration. Prior Anticube and graph/state-change ΔG* calculations are being reconciled to run receipts and are excluded from measured demo claims. The current work establishes infrastructure and evidence integrity; training, quality gains and agent speedup require their own evidence.

## Guidance for agents

Start with this README, the recording script and coverage audit. Report verified achievements first, then attach each scope or open question to its specific result. Read original receipts rather than promoting stale labels or summaries. Preserve frozen data and completed evidence; never rewrite commitments to admit mismatched answers. Use isolated worktrees, preserve other contributors’ edits, and serialize shared-GPU workloads.

## Licensing

Original software: [Apache-2.0](LICENSE). Original non-code materials: [CC BY-NC-ND 4.0](LICENSE-NONCODE-CC-BY-NC-ND-4.0.txt). Third-party materials retain their own rights: [NOTICE](NOTICE), [third-party notices](docs/THIRD_PARTY_NOTICES.md). Repository visibility and redistribution review are separate from these license declarations.

[Historical Lane A setup](docs/HISTORICAL_LANE_A_README.md) · [Execution runbook](docs/CONCURRENCY_EXECUTION_RUNBOOK.md)
