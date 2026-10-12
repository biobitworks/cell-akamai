# Judges: quick review

Cell-Akamai extends the Akamai inference workshop with a Strands role-separated design, measured local/cloud pilots, reproducible data representations and auditable evidence. The user reported the HackerSquad submission completed; this repository is the source/evidence companion.

## 1. Problem

Can an agent challenge improve an answer at a measurable computational cost? We make inputs, comparison policies, measurements and scoring custody inspectable.

## 2. Stack and achieved results

- Strands actor/challenger/control/adjudicator design, fixture tests and a successful tool-free call to Akamai.
- Akamai vLLM Qwen3-4B serving experiments and separate local Ollama Llama 3.2 3B pilots.
- First sequential request-rate experiment: independently reproduced 0.19004143, 0.00768947 and 0.00554005 tokens/s² from recorded inputs. [Receipt](../evidence/20261012/TOKEN001_RECOMPUTED.json).
- Original Module 7 short c=8 run: approximately 269 output tokens/s, 1,262 ms p95, zero HTTP failures.
- Exact reconstruction of 32 frozen synthetic ECA tasks across original/FCO/FCG representations.
- Commitment checks, strict parsing, preserved negative findings and sanitized dashboards.

## 3. Demo and code

[Recording script](FINAL_DEMO_SCRIPT.md) · [Strands bridge](../module9_antigents/bridge.py) · [Scorer](../lane_b/harness/score_lane_b.py) · [Telemetry calculations](../cell_akamai/kinetics.py) · [Coverage audit](EVIDENCE_COVERAGE_AUDIT.md).

For an interactive **saved snapshot**, run from the repository root:

```bash
python3 -m http.server 8773 --bind 127.0.0.1 --directory judges
```

Open http://127.0.0.1:8773/ . This snapshot contains aggregate data and provenance, not a live GPU connection. It works without the operator’s private run directory. [Snapshot hashes](../judges/SNAPSHOT_MANIFEST.json). The operator’s live local dashboard is separately served on port 8771.

## Interpretation

Deterministic means repeatable data reconstruction, hashing and declared arithmetic; model responses may vary. Small scored pilots returned zero correct answers within their budgets. M08 preserved a negative short tuning result. Recovered ledger commitment mismatches exclude affected bundled scores; historical index labels are explained in the evidence view. Training, agent speedup and quality gains require separate evidence. Anticube/graph-state ΔG* calculations remain under reconciliation to these runs.

## Licensing and access

Original code: [Apache-2.0](../LICENSE). Original non-code: [CC BY-NC-ND 4.0](../LICENSE-NONCODE-CC-BY-NC-ND-4.0.txt). [Third-party exceptions](THIRD_PARTY_NOTICES.md). Private raw responses, credentials and the complete recovery backup are excluded. Repository was last verified private; judges need authorized repository access until redistribution review is resolved.
