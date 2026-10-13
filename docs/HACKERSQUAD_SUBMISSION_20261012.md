# Cell-Akamai — HackerSquad Submission Pack (2026-10-12)
**Deadline: Monday 2026-10-12 16:00 PDT.** Event: [Akamai — Build AI Agents That Own Their Inference](https://luma.com/sf-agents-owning-inference). Hosted at AWS Builder Loft, San Francisco. Demo recording duration MUST be <=5 minutes.

## Ready-to-paste project fields
**Name:** Cell-Akamai: Governed Antigentic Agents on Owned GPU Inference

**Description:** Cell-Akamai extends Akamai's vLLM inference workshop with reproducible telemetry, provenance-aware model orchestration, and a controlled scientific agent-evaluation harness. It links request-level completion-token usage, latency and sampled GPU-serving metrics to inspectable FCO/FCG evidence records. A Strands-enabled Module 9 prototype adds a bounded actor, an antigent challenger and an equal-cost randomized control, scored independently on a frozen cellular-automaton pilot dataset. The dashboard explicitly distinguishes observed source receipts from offline synthetic tests and not-yet-run experiments. The prototype tests whether critique improves correctness enough to justify extra model calls; **it does not claim demonstrated antigentic superiority, trained weights or committed MMR**.

**Technologies:** Akamai Cloud hosted GPU vLLM; Qwen3-4B; Python, OpenAI-compatible inference, Strands Agents SDK (reference implementation/offline-tested; GPU deployment unverified), Kubernetes, Prometheus `/metrics`, Jupyter notebooks, GitHub, SHA-256 FCO/FCG local custody projections, deterministic ECA (rules 30/90/110/184), HTML dashboard.

**GitHub:** https://github.com/biobitworks/cell-akamai (PRIVATE; organizers/judges require access). Source not merged to main yet; review PR #3 dashboard, #5 scientific Lane B, #7 data/concurrency, #8 Lane A concurrency kit, #10 Module 9 Strands antigent, #6 reproducibility protocol. Do not claim merely listing GitHub URL confers access.

**Demo URL:** NOT_VERIFIED. Use local self-contained dashboard only if opened and inspected on screen; do not invent a hosted URL.

**Akamai usage:** vLLM completion endpoint and `/metrics` from the workshop environment, preserving observed completion usage and raw metrics digests. A prior exported Akamai Qwen3-4B smoke receipt reports four successful completions (272 total output tokens, mean request-average 39.4913 tokens/s), previously checked offline for arithmetic and source digests. This is **not** a BF16/FP8 experiment or proof of live performance superiority. Strands/Akamai multi-agent GPU deployment is NOT_TESTED as of this submission-prep pass.

## Suggested 3:45 demo rundown
- **0:00–0:25 — Problem:** inference can be fast but claims about an agent's performance, evaluation, provenance and true token accounting often lack inspectable evidence.
- **0:25–1:05 — Akamai owned inference:** show original workshop environment or verified receipt, model and Prometheus-derived measurements, and explain SSE chunks are not tokenizer tokens.
- **1:05–1:55 — Dashboard:** show observed Qwen smoke receipt and FCO/FCG drill-down, distinguish tokens, tokens/s, descriptive tokens/s²; explain TTFC versus TTFT.
- **1:55–2:45 — Genesis/DAISY/Antigent:** show frozen input-only ECA dataset, separate B0 fixed, B1 Genesis three-vote *proxy*, B2 challenge/adjudicate, B3 randomized control, and answer commitment before oracle scoring. Show Strands Module 9 code/preview only if not deployed, label NOT_TESTED.
- **2:45–3:25 — Concurrency experiment:** show code/notebook for 1/2/4/8, GPU saturation and latency guardrails; if no measured real concurrency receipts, explicitly show NOT_TESTED cells rather than suggesting measured gains.
- **3:25–3:45 — Evidence ceiling and next step:** independent held-out evaluation required for improvement; self-training needs actual weight updates; Anticube/ΔG*/MMR uncomputed/uncommitted. Close with next executable GPU comparison.

## Judge-access gate
- Private canonical repo main currently contains just README; all meaningful implementation is on reviewable PR heads. Verify organizer-approved GitHub collaborator access for judges or safely publish a sanitized reviewed release branch after secret/license audit. Do not make private repo public by default.
- On a different account/unauthenticated browser, verify source and any demo URL access. If private, request organizers' access instructions before claiming judge availability.
- Verify links resolve and site or static HTML launches from a clean browser.

## Required HackerSquad steps (event guide)
1. Sign in to https://hackersquad.io and open the Akamai event's project submission section.
2. Enter project name, description, technologies, GitHub link and accurate team membership; **Save**.
3. Choose **Record Video Demo**, choose screen/tab/window, **Enable Camera & Mic**, allow permissions, **Start Recording**.
4. Show evidence-backed demo. **Stop Recording**, then explicitly **Submit**.
5. Verify final submitted status before 16:00 PDT. A saved form, stopped recording, or GitHub PR is **NOT** an eligible submission by itself.

## Scientific and code-state disclosure
- Frozen ECA pilot data: 32 deterministic inputs, split disjoint from earlier calibration seeds. Input-only pilot dataset in PR #7; confirmatory evaluation not frozen.
- Current policy implementation is **proxies**; `B1_GENESIS` is three-vote self-consistency, not recovered trained Genesis. `B2` is inference-time antigentic challenge, not a weight update.
- Prior uploaded reference completions are source-backed, but no verified paired quantization/speculative/concurrency uplift.
- Workshop `common/loadtest.py` counts SSE chunks as tokens; never reuse its labeled `throughput_tok_s` without conversion to genuine usage or scoped server counter.
- FCO/FCG SHA-256 establishes identity, not scientific correctness. MMR NOT_COMMITTED, signing NOT_SIGNED. Anticube and Delta G* NOT_COMPUTED.

## OWNER and NEXT_ACTION
- **Operator:** submit HackerSquad form and demo plus judge access by 16:00 PDT. Only operator can verify the final Submit success in event UI.
- **Executor (Cursor/Codex):** preserve/finish bounded vLLM and Module 9 run receipts; screenshot actual observed model/telemetry and dashboard; avoid concurrent interfering workloads on shared GPU.
- **Claude:** independent ECA scoring, scientific caveats, summary table, exact notebook/PR refs; no claims beyond executed controls.
- **Orchestrator:** GitHub evidence reconciliation, PR conflict review, public claim ceilings.
- **NEXT_ACTION:** Capture a 3:45 self-contained screen demo showing what is OBSERVED, what is IMPLEMENTED/OFFLINE_TESTED and what remains NOT_TESTED; press Submit and verify in HackerSquad.
