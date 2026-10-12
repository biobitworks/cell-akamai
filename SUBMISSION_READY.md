# HackerSquad submission packet

## Project details (copy and paste)

**Project name**

Cell-Akamai: Auditable Inference Evaluation

**Project description**

Cell-Akamai is an evidence-first prototype for evaluating LLM inference on an Akamai-hosted vLLM service. It records request usage, latency, failures, source/configuration identity, and answer commitments so short workload results can be reconstructed and checked. The current package also demonstrates lossless provenance projections for a frozen synthetic ECA pilot. These are short, non-confirmatory runs and local fixture checks; no model training or improvement is established, and no hour-scale study has completed.

**Technology**

Python, Jupyter notebooks, vLLM, Akamai AI Inference workshop, JSONL evidence fixtures, SHA-256 manifests, local dashboard.

**Working source**

https://github.com/biobitworks/cell-akamai/tree/lane/akamai-m08-m09-results-20261012

**Reviewable evidence PR**

https://github.com/biobitworks/cell-akamai/pull/12

**Related source and evidence**

- Workshop companion, PR #5: https://github.com/biobitworks/cell-akamai/pull/5
- Concurrency workload, PR #7: https://github.com/biobitworks/cell-akamai/pull/7
- Akamai workshop source: https://github.com/akamai-developers/akamai-workshop-ai-inference

## Demo talking points (about 4 minutes)

1. **Problem and scope (0:00–0:35).** “This prototype makes inference runs auditable: it preserves workload, request accounting, failures, configuration identity, and committed answers. We measured inference; we did not train model weights.”
2. **A short measured run (0:35–1:25).** Show the verified results/dashboard if available. The separate original-workshop Module 07 c=8 run recorded 269.01 completion tokens/s, 1.262 s p95 request latency, and zero failed HTTP requests. Explain that the original workshop counted streamed chunks, while this figure uses server-reported completion tokens over measured batch time. It describes that workload only. Do not imply a before/after gain.
3. **A result that did not pass (1:25–2:20).** Show the B0–B3 table and failures. The recovered BF16 pilot has 16/16 cells run; 128/128 items failed parsing or within-budget answer criteria. Its synthetic ECA inputs are fixtures, not biological observations or a biological benchmark. B1 is a Genesis proxy; the arms have unequal call budgets and challenge information. No improvement claim follows.
4. **Reconstruction and custody (2:20–3:15).** Show the offline verification receipt: three roles with 32 rows each, exact payload reconstruction across original/FCO/FCG representations, and SHA-256 file digests. Explain that FCO/FCG are data representation/provenance projections. Historical Genesis/Vita outputs were not recovered; the local Merkle tree is not a project MMR.
5. **Limits and next work (3:15–4:00).** Module 08's one-flag pilot ran without an improvement claim. Module 09's agent port-forward failed, while ECA execution continued with the retained notebook failure. The current sustained queue targets 48 five-minute windows across four leakage-safe representations (four measured GPU-hours); no completed hour-scale result is verified. The two evaluator representations remain blocked pending an oracle-safe workload contract. FP8/speculation were not tested. Vita/DAISY longevity work is source-pinned design only, and the Virtual Cell Challenge is a separate future track with no verified submission. Close by showing the source link and evidence files.

Keep the recording under five minutes. Avoid private raw responses, credentials, environment variables, kubeconfig, and private logs. Click **Submit** after recording and verify the submitted state.
