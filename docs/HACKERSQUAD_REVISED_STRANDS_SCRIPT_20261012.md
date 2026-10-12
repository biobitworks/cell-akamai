# Cell-Akamai — Revised HackerSquad evidence narrative and Strands-first recording
**2026-10-12; review-only draft.** Canonical repo: biobitworks/cell-akamai. This is a copy/script and evidence-reconciliation change, not a new GPU run, scientific scorer, deployment or HackerSquad submission.

## Ready-to-paste short project description
**Project:** Cell-Akamai — Auditable Agent and Antigent Inference on Akamai Cloud

Cell-Akamai is a Strands-enabled agent-and-antigent research prototype built around inference that can be measured and audited. It separates an actor producing candidate answers, an antigent challenger reviewing them, and an adjudicator selecting an answer, with a randomized challenge control and independent post-commit scoring.

We connected to the workshop's Akamai-hosted Qwen3-4B vLLM endpoint and ran usage-based inference and concurrency measurements. A short original-workshop-style run at eight concurrent requests reported **269.0 completion tokens/s, 1.262 s p95 request latency, and zero HTTP failures**. This is an endpoint-serving result, **not** a Strands, DAISY or scientific quality speedup. We retained the complete sixteen-cell BF16 policy-pilot summaries: eight distinct ECA tasks were repeatedly attempted under four policy arms and concurrency levels 1, 2, 4 and 8. All 128 policy×task×concurrency attempts failed the defined valid-answer/within-budget admission criteria even though model calls and usage were recorded. We preserve this negative result.

An input-only 32-task deterministic ECA pilot and three ECA-derived role datasets (Genesis, Vita DAISY, evaluator) were preserved in original/FCO/FCG forms. The three original-versus-reconstructed pairs passed local exact-reconstruction checks; these are **synthetic fixtures**, not historical biological or real model-role outputs. The dashboard and Jupyter notebooks expose source receipts, token-usage units, failure states and scientific claim limits. A local Ollama Llama 3.2 3B pilot was scored separately: 0/4 exact matches per arm at each tested concurrency level, with no paired discordant correct items. Different models/backends preclude a controlled local-versus-Akamai performance claim.

The Strands role bridge and bounded runner passed local fixture tests but **a networked Strands request, tool invocation and Kubernetes service were not verified**. The original Module 9 agent notebook has a retained port-forward failure. A Module 8 before/after scheduler change (`max-num-seqs=32→64`) did not establish an improvement. FP8, speculation-on/off, long-duration tests, Anticube, ΔG*, self-training weight updates and project MMR remain unverified/uncomputed as appropriate.

**Technologies:** Akamai Cloud GPU / hosted vLLM / Qwen3-4B; Python; Strands Agents SDK (offline-tested reference); OpenAI-compatible endpoint; Jupyter; Kubernetes (prototype manifests); Prometheus; SHA-256-backed FCO/FCG projections; GitHub; local Ollama (separately labeled).

**Source:** https://github.com/biobitworks/cell-akamai (PRIVATE; judges must receive organizer-approved access). The working implementation currently resides in distinct open PRs: #3 telemetry, #5/#13 Lane B science, #7/#8 concurrency and frozen pilot dataset, #10 Strands Module 9, #11 dashboard, #12 executed result archive.

## Revised Strands-first video script (about 3 minutes at moderate pace)
**[On camera, then PR #10 `module9_antigents/bridge.py`]**
Hi, I'm Byron. This is Cell-Akamai, an auditable agent and antigent prototype built around inference served on Akamai Cloud. An actor proposes an answer. An antigent independently challenges it. An adjudicator produces a final decision, and a randomized challenger gives us a control. The goal is to test **whether that extra reasoning actually improves scientific answers enough to justify its cost**.

**[Show `run_capstone.py`, preview mode, frozen-data and commitment code]**
We implemented a Strands `OpenAIModel` bridge for OpenAI-compatible inference with separate role contexts, bounded requests, optional read-only tools, and hashed role traces. Our runner defaults to preview; it commits answers before an independent evaluator can score them. Seven offline fixture tests passed. **The live Strands SDK request, tool call and Kubernetes antigent deployment have not yet been verified**, so this is implementation evidence, not a successful Akamai Strands demo.

**[Show `http://127.0.0.1:8771/evidence`, only if running and its data sources are visible]**
What we did run on Akamai was real Qwen3-4B inference. In the workshop's concurrency test, eight-way load produced **269 completion tokens per second** with **1.262 seconds p95 latency** and no HTTP failures. We counted server-reported completion tokens, not streamed chunks.

**[Show PR #12, failed BF16 science panel]**
We also completed sixteen BF16 pilot cells across four answering strategies and concurrency one, two, four and eight. That is **128 experimental attempts over eight repeatedly used, unique synthetic tasks**. Every cell reported zero answers meeting its parsing and budget criteria. Execution succeeded; scientific validation did not. We retained the failures rather than report a speedup.

**[Show frozen ECA data and FCO/FCG reconstruction graph]**
Our frozen ECA dataset contains 32 synthetic inputs. We created original and linked FCO/FCG representations for Genesis, Vita DAISY and evaluator **fixture roles**, and checked that reconstruction reproduces the records exactly. These are not biological observations or separately trained Genesis and DAISY models.

**[Show separate local backend tab and M08 status]**
Claude's independently scored local Llama 3.2 3B pilot also found zero exact matches on four tasks per arm at each tested concurrency level, although error patterns differed. That local model isn't directly comparable to the Akamai model. A separate Module 8 tuning run also showed no demonstrated gain; the original Module 9 agent deployment encountered a port-forward failure.

**[Return to dashboard, source and status fields]**
Our contribution is a working evidence framework with a Strands agent-and-antigent implementation, real Akamai inference measurements, reproducible notebooks and visible negative results. FP8, speculative decoding, Anticube, ΔG*, long-duration validation and antigentic weight training remain future experiments. We distinguish **implemented, observed, failed and untested** so claims can be checked rather than assumed. Thank you.

## Extended methodological description for judges
The 32-item frozen ECA pilot is the dataset inventory, not a claim that every run used 32 unique questions. The recovered BF16 full matrix used eight distinct task identities repeated for four named policies and four concurrency levels. B0 used one direct model call per item; B1 used three self-consistency votes (**GENESIS_POLICY_PROXY_V0**, not actual recovered Genesis); B2 used answer/challenge/adjudication as an *inference-time* DAISY-style antigentic policy; B3 used randomized single-cell recheck and adjudication (not a no-op placebo). Different call and challenge budgets prevent causal superiority claims.

The six named dataset representations are three underlying ECA-derived role datasets paired across original versus FCO/FCG reconstructions; they are **not six independent biological datasets**. Independent evaluator keys must not be shown to actors. File hashes, local Merkle construction, reconstruction correctness and custody provenance are distinct from scientific truth, and **project MMR = NOT_COMMITTED**, signatures = NOT_SIGNED.

Local run `MAGICPRO_OLLAMA` `llama3.2:3b`, `concurrency-07-ollama_q4_default-20261012T201153Z-4427e1d6`: Claude scorer verified answer/config/dataset digests and complete paired coverage at c=1 and c=2; each arm 0/4 exact. Matched correctness contrasts show 0 discordant correct pairs, Holm-adjusted p=1; this is uninformative in a tiny all-wrong sample, not evidence for equivalence or harm/benefit. Hamming error/parse failures vary; tokens per correct item is undefined, not zero. This is *MAGICPRO_OLLAMA*, not MagicStudio.

The separate Cell-Akamai LFM 1.2B directory reviewed by Codex has 0-byte `answers.jsonl`, and no scored outcome or verifiable host/model information. Separate prior exploratory MagicStudio LFM manifests may exist but are not joined to the Cell-Akamai pilot, and do not establish controlled local/cloud comparison.

Akamai M08 operator-reported benchmark tested `max-num-seqs=32→64` at max workload concurrency 16 and quality 0/8 exact before and after: one nonbinding limit change, no supported improvement. M09 original agent deployed notebook status = FAILED (agent port-forward exited); do not say it passed Strands/Akamai deployment.

**Offline tests:** PR #10 reports 7 Strands fixture tests; PR #11 reports 43 dashboard+Lane A/B tests; PR #12 reports 36 deterministic execution tests. The user's separate figure "42" has no matching single suite receipt in these reviewed PR descriptions, so omit it pending pinned test-command/log evidence. These suites overlap and must not be summed. Do not mistake unit tests for a remote GPU validation.

**Original workshop Module07 c8:** completion usage throughput 269.008183 tokens/s, p95 request duration 1261.605 ms, zero HTTP failures in 32 requests, short pilot only. c1 38.254 tokens/s; higher **aggregate** throughput under larger concurrency is not agent or scientific improvement. The original workshop `common/loadtest.py` estimated tokens from SSE chunks; operator changed calculation to use usage tokens. Distinguish original `legacy_stream_chunks_per_s` from true `usage_completion_tokens_per_s`.

**Future datasets:** LongevityBench and URSA are source-pinned candidates; **not evaluated or biologically validated in this event's reported run**. LongeBench and VCC remain separate scientific evaluation protocols.

**Judge and licensing:** The supplied HackerSquad FAQ says participants retain intellectual-property rights, promo license covers submitted media but not underlying source, and judges require source access for prize eligibility. Repo is PRIVATE. Arrange organizer-approved access without unnecessarily making source public. Demo <=5 minutes; Save details and explicit video Submit required.

## Source ledger / review boundaries
- Original workshop: https://github.com/akamai-developers/akamai-workshop-ai-inference (pinned source 454b43269216c1f92dd8d7e2711649e38cb888cb)
- Strands prototype: https://github.com/biobitworks/cell-akamai/pull/10
- Dashboard and local scored pilot: https://github.com/biobitworks/cell-akamai/pull/11 — scored `evidence/lane_b_pilot/concurrency-07-ollama_q4_default-20261012T201153Z-4427e1d6/lane_b_concurrency_summary.json`
- Independent scorer: https://github.com/biobitworks/cell-akamai/pull/13
- Executor/operator results: https://github.com/biobitworks/cell-akamai/pull/12 — `evidence/20261012/recovered/runs_workshop07/*/summary.json`, `.../runs_fullmatrix/*/bench_cells.json`, `.../successor/80_m08_*STATUS.json`, `.../successor/81_m09_*STATUS.json`
- Privacy: raw prompts, kubeconfig, credentials and protected responses must not be committed.
- Linked Google spreadsheet: https://docs.google.com/spreadsheets/d/1odI_3t8YM9a44dD0As6kqy5SmbMqJtAO/edit ; **NOT_REVIEWED** in this handoff (no connected Google Drive reader; public fetch failed); no claim to have updated this spreadsheet.

**NEXT_ACTION:** Operator use this reviewed three-minute script for video and explicitly Submit on HackerSquad, verify judge private GitHub access, then Claude/Executor reconcile failed scientific-task outputs and M09 deployment on separate branches. Do not merge PRs without independent tests and evidence review.
