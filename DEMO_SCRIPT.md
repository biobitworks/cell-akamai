# Cell-Akamai demo — target 3 minutes

Use the verified results report and live local dashboard. Do not show terminal
environment variables, raw model replies, kubeconfig, credentials, or private logs.

**0:00–0:30 — Problem and prototype**

“Cell-Akamai measures agent inference on our Akamai vLLM service. We preserve
the source version, request accounting, answer commitments and failures so that
performance claims can be checked. This is inference evaluation; we have not trained
model weights.”

**0:30–1:20 — Actual measurements**

Show the dashboard and the final report. Name the observed served model and precision.
Explain that original workshop Module 07 counted streamed chunks, so this run uses
server-reported completion tokens divided by measured batch time. At c=8 the separate
original-workshop run measured 269.01 completion tokens/s, 1.262 s p95 request latency,
and zero failed HTTP requests. These measurements describe that workload only.

**1:20–2:00 — Scientific failures are evidence**

Show the B0–B3 table, including failed cells. Explain that the frozen ECA pilot is
synthetic and non-confirmatory, B1 is a Genesis proxy, and the arms have unequal
call budgets and different challenge information. State the final observed parse
failure and correctness results from the report. Do not claim improvement.

**2:00–2:35 — Custody and reconstruction**

Show the three-role dataset validation receipt: 32 records per role, exact payload
reconstruction, and independently checked file hashes. FCO/FCG are representation
and provenance projections. Historical Genesis/Vita outputs have not been recovered;
the local Merkle construction is not a committed project MMR.

**2:35–3:00 — Reproducibility and limits**

Show the GitHub PR, sanitized evidence index and archive digests. State Module 8 and
agent deployment outcomes exactly as recorded, including any exceptions. Finish
with the next experiment or unresolved blocker. Raw responses stay private.

## Submission

Save the project details and working source link in HackerSquad. Record a browser
tab or application window with this demonstration, keeping the video under five
minutes. Finish recording, then press **Submit**. Verify the submitted state; stopping
the recording alone does not submit it. Complete this before **16:00 PDT, October 12,
2026**, even if optional FP8 or speculative experiments remain untested.
