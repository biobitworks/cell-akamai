# Cell-Akamai — Uploadable Module 8 + 9 companion (2026-10-12)

**Status: IMPLEMENTED / OFFLINE_TESTED; AKAMAI_INFERENCE=NOT_EXECUTED_FROM_THIS_PACKAGE.**

Source predecessors: [Akamai official workshop](https://github.com/akamai-developers/akamai-workshop-ai-inference) `454b43269216c1f92dd8d7e2711649e38cb888cb`; [cell-akamai Claude Lane B PR #5](https://github.com/biobitworks/cell-akamai/pull/5) `73001e73eeada4aee4f3b32fa4a0671cca255601`; [cell-akamai concurrency PR #7](https://github.com/biobitworks/cell-akamai/pull/7) dataset SHA-256 `69ced0ca1cf77a00446e2b3db03564eb487b2f2b15e68c34590ee8e96b07c274`.

## Upload, unzip and run on your Akamai JupyterLab

1. In your workshop JupyterLab, upload the **ZIP** provided with this README. Open a **Terminal** inside JupyterLab.
2. Unzip it **outside the Akamai workshop git checkout** to avoid modifying the upstream repo:

   ```bash
   mkdir -p ~/cell-akamai-m08-m09
   unzip -o CELL_AKAMAI_M08_M09_HANDOFF_20261012.zip -d ~/cell-akamai-m08-m09
   cd ~/cell-akamai-m08-m09
   python -m pytest -q tests    # optional; needs pytest in the notebook environment
   ```

   If the ZIP has already been uploaded to a different location, use its exact full path in `unzip`.
3. Find the workshop checkout via JupyterLab's file browser. Run official Module 0 (`00_prerequisites/00_connect_and_verify.ipynb`) first. Set the env variable if the ZIP's notebook cannot find the workshop clone:

   ```python
   import os
   os.environ['WORKSHOP_REPO'] = '/home/jovyan/akamai-workshop-ai-inference'  # replace with actual path
   ```

4. Open `notebooks/80_m08_tune_before_after.ipynb` and run sequentially. It benchmarks the current vLLM, writes a one-flag plan, and **does not** change deployment unless you explicitly set `AUTHORIZE_ONE_FLAG_ROLLOUT=True`. For a real before/after Module 8 comparison, review the plan, authorize within your namespace, wait for readiness, and run the after cell. Only `--max-num-seqs` is changed.
5. Open `notebooks/81_m09_agent_and_daisy.ipynb`. You may run official Module 9 first to deploy its Solutions Architect agent, **or** set `AUTHORIZE_UPSTREAM_AGENT_DEPLOY=True` in companion 81 to use its upstream source and manifest. Test the agent and six concurrent questions. Run the four-arm synthetic ECA pilot (8 items default; 32 optional) and then the independent scorer.
6. Open `notebooks/82_verify_and_export.ipynb`. Download its generated `CELL_AKAMAI_M08_M09_RESULTS_*.zip` and **upload that results ZIP here** for independently checked dashboard aggregation and receipt comparison.

**Do not run GPU load benchmarks simultaneously with Claude's local pilot or any other workload sharing this vLLM server.** Wait for one bench epoch to finish before starting another. The upstream workshop 08 notebook's `kubectl apply` may redeploy; do not run it blindly on top of the companion's single-flag patch.

## What goes into the result ZIP

- `runs/M08_before_*/...`: requests with actual server `usage` token counts, p50/p95 wall latency, aggregate tokens/s, sampled running/waiting/KV gauges, raw before/after `/metrics` snapshots and hashes.
- `runs/M08_after_*/...`: same frozen workload after one authorized serving-policy change, plus configuration-matched comparison.
- `runs/M09_UPSTREAM_K8S_AGENT_*/...`: original agent's HTTP scope/pricing results and 6-way batching metrics. Internal invocation of the pricing tool is **NOT_DIRECTLY_ATTESTED**; the upstream code supports tool calling.
- `runs/M09_ECA_B0_B3_*/...`: oracle-free answer generation, content hashes, completed pilot's independently computed exact-match accuracy, McNemar discordance and tokens/correct.
- `ARCHIVE_MANIFEST.json`: per-file SHA-256. File identity is not a validated MMR root.

**Measurement boundaries:** upstream `common/loadtest.py` counts *SSE chunks*, not true completion tokens. Our usage-verified completions are not pooled with upstream 'tokens/s'. For simultaneous requests, `tokens/s²=NOT_COMPUTED`. FP8 precision=UNKNOWN unless the live deployment image/config and model identity establish it. Zero or missing metrics are distinguished. B0 has fewer calls than B1/B2/B3; B1 is a Genesis proxy, and B2/B3 do not yet represent an information-matched causal control. No weight updates => no self-training claim. `ΔG*`, Anticube, signatures, MMR remain NOT_COMPUTED/NOT_SIGNED.

## Submission reminder

Event deadline: **October 12, 2026, 4:00 PM PDT**. Prioritize **saving the HackerSquad project**, recording a video of **at most five minutes**, then clicking **Submit** and verifying judge access to source. Don't wait for the full 32-item pilot or a risky redeploy if submission is endangered. If a private GitHub repository is used, arrange organizer-access explicitly.

## Restore baseline manually if needed

The original deployment `args` are stored in `runs/M08_before_*/identity.json` and the applied single-flag JSON patch in `tune_actual.json`. Restoring is **not automatic**, because it would be another cluster mutation. Use the upstream Module 8 workflow and the saved baseline values only with explicit authorization.

## Successor v2: three original-role datasets and three FCO/FCG projections

**Important provenance boundary:** these 3 originals are **new structured fixtures derived from** the verified 32-item ECA pilot `data/eca_pilot_inputs_v1.jsonl` (PR #7). They are not recovered historical before/after Genesis, Vita DAISY, or evaluator datasets. Actual Genesis model output, Vita DAISY trace, and historic evaluator output remain **NOT_RECOVERED / NOT_TESTED**.

- `data/original/genesis.jsonl`: 32 ECA Genesis-**proxy input** tasks, null model outputs.
- `data/original/vita_daisy.jsonl`: 32 challenge-**input** fixtures with deterministic placeholder candidate, no actual challenger output.
- `data/original/evaluator.jsonl`: 32 independently computed deterministic ECA truth rows, restricted to post-commit local scoring.
- `data/fco/{genesis,vita_daisy,evaluator}.jsonl`: 3 deterministic content+occurrence projections, lossless payload.
- `data/fcg/{genesis,vita_daisy,evaluator}.jsonl`: 3 typed link/relationship files, from these same original rows; not evidence of causal relations.
- `data/SIX_DATASET_VERIFICATION.json`: all file digests, exact reversible checks, byte costs, local **nine-file** data Merkle tree including the 3 graph files; this is explicitly **NOT a project MMR**.

**Run notebooks:** `83_six_dataset_offline_verify.ipynb` (offline verification) → `80_m08_tune_before_after.ipynb` (Module 8) → `81_m09_agent_and_daisy.ipynb` (Module 9) → `84_six_dataset_akamai_paired.ipynb` (optional paired original/FCO GPU pilot) → `82_verify_and_export.ipynb` (results ZIP). Independent evaluator reference never sent to models. Source-bundled tests: `python -m pytest -q tests`.

Jupyter code-cell ZIP extraction (NOT a shell command, no `unzip` SyntaxError):

```python
from pathlib import Path
from zipfile import ZipFile
archive=Path('CELL_AKAMAI_M08_M09_SIX_DATASETS_20261012.zip')
target=Path.home()/'cell-akamai-six'
with ZipFile(archive) as z:
    z.extractall(target)
print(target)
```

This bundle does **not** claim historical recovered six datasets. Supply the actual three original source exports to replace these fixtures in a future append-only successor; do not overwrite this v2 root.
