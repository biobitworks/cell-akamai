# Cell-Akamai HackerSquad video (about 3 minutes)

Use the dashboard and GitHub PR #12 as screen cues. Keep the browser on sanitized aggregate views and public repository pages. This script is written to speak as-is; bracketed text is a screen cue, not narration.

**[Face camera; title card or project page]**

Hi, I’m presenting Cell-Akamai, an evidence-first prototype for evaluating language-model inference on an Akamai-hosted vLLM service. The project records workload details, token usage, latency, failures, configuration identity, and committed answers so that a run can be checked after it finishes. We used Python and Jupyter for the harness, Kubernetes to reach the existing Akamai service, pytest for accounting checks, and SHA-256 receipts for reproducibility. This is inference evaluation. We did not train model weights.

**[Show the dashboard’s sanitized aggregate results]**

Here is a short, completed workload measurement. In a separate run of the original workshop Module 07 workload at concurrency eight, the service recorded 269.01 completion tokens per second, 1.262 seconds p95 request latency, and no failed HTTP requests. The workshop’s original counter counted streamed chunks; this result uses server-reported completion-token usage divided by measured batch time. These numbers describe that workload and run only. They do not show an improvement over a control.

**[Show the B0–B3 table and retained failures]**

We also tested a small synthetic ECA pilot. The results include failures: across the recovered BF16 pilot, all 128 items failed the parse or within-budget answer criteria. The fixture is synthetic and does not represent biological data. B1 is a Genesis proxy, and the arms had different call budgets and challenge information, so this pilot cannot establish that one approach is better. We preserve the negative result instead of treating it as a success.

**[Show the offline verification receipt]**

For reproducibility, the local verification checked three role datasets with 32 records each and confirmed that the FCO and FCG projections reconstruct the original fixture payloads exactly. These are data representation and provenance checks. They do not verify biological correctness or recover historical Genesis and Vita/DAISY model outputs.

**[Show GitHub PR #12, then the current run status]**

[Show tools/hour_scale/sustained.py and its unit tests briefly.] PR twelve tracks the longer evaluation implementation. Its current design allocates 48 five-minute windows across four eligible representations and configurations. The attempted start failed preflight before inference, so zero windows completed and the longer study remains pending. FP8 and speculative decoding are untested. The dashboard and receipts keep that boundary visible.

**[Show project page; face camera for close]**

Longevity evaluation is a future, source-pinned design track. The Virtual Cell Challenge is separate future work; no submission is verified. Cell-Akamai’s contribution today is a reproducible inference workflow that records both measurements and failures. Thank you.
