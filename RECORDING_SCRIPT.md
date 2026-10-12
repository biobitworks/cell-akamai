# Strands-first recording script — about three minutes

[Face camera, then show PR #10: https://github.com/biobitworks/cell-akamai/pull/10]

Hi, I’m Byron. Cell-Akamai is a Strands-based agent and antigent prototype designed to make scientific inference auditable on infrastructure we control. Our central idea is to separate the actor that proposes an answer, the challenger that questions it, and the adjudicator that decides what to retain. A randomized challenger gives us a control for whether useful challenge adds value beyond extra inference.

[Show module9_antigents/bridge.py and run_capstone.py in PR #10]

During the workshop, we implemented a Strands OpenAIModel bridge for OpenAI-compatible inference endpoints, with fresh context for each role call, token-usage accounting when the SDK provides it, and hash-only role traces. We added a preview-first capstone runner, separate plain-client and Strands runtime paths, and answer commitments before independent scoring. An optional HTTP service defines a bounded six-request concurrency limit. That service is implementation work, not a verified deployment.

Seven local fixture tests passed for the Strands integration, and its review notebook executed offline. These tests check the scaffolding; they do not prove a real networked Strands request or tool call against Akamai. Those integration steps remain untested in our verified evidence.

[Show the sanitized dashboard at http://127.0.0.1:8771]

Separately, we did execute real inference workloads on the existing Akamai Qwen3-4B vLLM service. We ran sixteen BF16 concurrency cells across four policy arms and concurrency levels one, two, four and eight. These endpoint results validate execution and accounting, but they are not Strands runtime measurements.

We preserved negative results: all sixteen cells reported zero valid answers within budget: 128 arm-by-task attempts using eight unique ECA tasks repeatedly. A separate original-workshop concurrency-eight run measured 269 completion tokens per second, 1.262 seconds p95 latency, and no HTTP failures. We corrected the distinction between streamed chunks and actual tokens. These are short pilots and do not establish a speedup or quality improvement.

Module 8 also ran: changing max-num-seqs from 32 to 64 produced no demonstrated throughput or quality benefit. The tested concurrency never reached the original limit, so this pilot cannot establish a benefit from that knob.

[Show PR #12 evidence and test index]

We also verified exact reconstruction of three synthetic datasets across original, FCO and FCG representations, ran named offline verification suites, and published sanitized evidence and a dashboard. The synthetic fixtures are not biological observations. Claude’s scored local llama3.2:3b pilot on the MAGICPRO_OLLAMA backend is shown alongside separate Akamai Qwen3-4B panels. Each scored arm has zero exact matches on four items, but local Hamming errors differ between arms. McNemar comparisons show no discordant correct pairs, with adjusted p-values of one. This small pilot does not establish equivalence or a benefit. Tokens per correct answer is undefined because zero answers were correct. These are different models and serving configurations, not a controlled hardware comparison.

Our next milestone is a real Strands request, followed by equal-budget plain-versus-Strands experiments and independent scoring of committed answers. Long-duration runs are incomplete. FP8, speculative decoding, Anticube and delta G star remain unverified or uncomputed. We have not trained weights.

Cell-Akamai’s contribution today is the Strands role-separated implementation plus real Akamai endpoint experiments and reproducible evidence. We make the boundary between implemented, tested, failed and not yet tested visible. Thank you.

## Test-count provenance — reference, not narration

- PR #12 publication checkout: 44 tests passed on the current execution/recovery/successor suite: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests/hour_scale tools/recovery/test_package_evidence.py evidence/20261012/successor/tests`. Historical counts 36 and 42 refer to earlier snapshots.
- PR #10: seven Strands fixture tests; these do not prove network integration.
- Claude dashboard/scorer counts belong to their particular branch and source SHA. Do not add these counts as independent validations; inspect the latest integration receipt before quoting a number.
- Strands live-canary status is changing during repair. Keep this script’s conservative status until a successful sanitized receipt is published.

## Submission access

Judges need access to the source. Public repository visibility is not a claimed event requirement. No raw replies, credentials, kubeconfig, or private logs should appear in the recording.

