## Workshop extensions and demo

[What we added, with evidence limits](docs/WORKSHOP_ADDITIONS.md) · [Three-minute walkthrough](docs/FINAL_DEMO_SCRIPT.md)

# cell-akamai · Lane A — Verified inference telemetry

This is a **standalone integration package** for the existing MagicPro directory `/Users/byron/projects/active/cell-akamai` and the **CPU-only hosted Akamai JupyterLab**. It does not modify Kubernetes manifests or provision GPUs. The vLLM service already runs on the workshop GPU node.

## What works

- Runs bounded, sequential streaming OpenAI-compatible requests against `VLLM_HOST` / `MODEL_NAME` (starting with Qwen3-4B).
- Preserves exact Prometheus `/metrics` sample bytes, SHA-256 digests, timestamps, labels, and parsed metrics.
- Preserves SHA-256 identities of prompt/request and response bytes, model IDs, stream-chunk hashes, observed completion-token counts, monotonic timing, and source IDs.
- Derives request tokens/s and **inter-request** tokens/s² using a versioned, deterministic algorithm. Missing usage returns null, never invented token counts.
- Builds addressable local FCO/FCG **projections**, distinct content/occurrence identities, typed edges, and independent file reread/arithmetic checks.
- Produces `lane_a_dashboard.html` as a single self-contained HTML file: model comparison, token curves, KV gauge, run selection and FCO drill-down. The dashboard includes Lane B rows when supplied.
- Includes `notebooks/10_token_kinetics.ipynb` (live) and `notebooks/11_replay_offline.ipynb` (offline), plus `pytest` tests.

## Start in Akamai hosted JupyterLab

1. Execute the workshop's **`00_prerequisites/00_connect_and_verify.ipynb`** once. Confirm model call passes; it checks `VLLM_HOST`, namespace, vLLM health and chat completions.
2. Upload the companion **`cell_akamai_lane_a.zip`** into JupyterLab, then in its terminal run:

   ```bash
   python - <<'PY'
   import zipfile
   with zipfile.ZipFile('cell_akamai_lane_a.zip') as z:
       for name in z.namelist():
           if name.startswith('/') or '..' in name.split('/'):
               raise ValueError('unsafe archive path')
       z.extractall('.')
   PY
   cd cell_akamai_lane_a
   ```
3. Open `notebooks/10_token_kinetics.ipynb`, select the installed Python 3.11+ kernel, and run its cells. Notebook 0/1 setup does not install anything; live experiment makes **4 requests** and lightly polls `/metrics`.
4. Open generated `lane_a_dashboard.html` from JupyterLab file browser (or transfer it for a read-only local browser preview).
5. For offline replay on a copied run, execute `notebooks/11_replay_offline.ipynb` or `python -m pytest tests -q`.

The archive's folder is deliberately separate from the workshop's source checkout; don't copy new files into `00_prerequisites/` or edit the shared vLLM deployment to run this experiment.

## Scientific/evidence constraints

- Stream chunks are **not equivalent to tokenizer tokens**. `ttfc_s` measures arrival of first nonempty content/reasoning chunk, **not server-side TTFT**.
- Request tokens/s = `usage.completion_tokens` / request wall duration (prefill + decode + network). This differs from vLLM's aggregate `/metrics` rate and decode-only TPOT.
- tokens/s² uses difference between **request-average rates** divided by difference of request **midpoint times**. It is inter-request kinetic variation, **not a per-token derivative** and **not epistemic gain**.
- Prometheus KV-cache ratio is occupancy of GPU-serving cache blocks, not scientific model quality; it is usually a fraction 0–1.
- SHA-256 deduplicates contents but is not signing or truth. All FCOs here are explicitly **`UNADMITTED_LOCAL_PROJECTION`**. No project MMR commitment is computed.
- Output files may expose research model names / source references; do not push raw `runs/`, `.env`, credentials, or restricted data to public GitHub.
- **No real Akamai run was executed in this package authoring environment**. Tests are synthetic or purely mathematical and are separately labeled.

## GitHub integration (after Gum Doctor isolates Git root)

The target repository is `biobitworks/cell-akamai`. This package was prepared before the GitHub repository existed. Consult current GitHub branches, issues and PRs for publication state. Never `git add .` while `cell-akamai` resolves to the unrelated parent MobiDB-lite repository.

From a verified independent repo root, import this package preserving its relative paths, create lane `lane/a-akamai-telemetry`, run `pytest`, commit/push, open a PR, and comment the exact branch/contract path on Claude's Lane B GitHub Issue. See `docs/LANE_B_HANDOFF.md`.

## Outputs

Each run creates `runs/akamai-<timestamp>-<random>/` with:

- `inference_observations.jsonl`: streamed chunk hashes, timing, usage, derived rates
- `telemetry_samples.jsonl`: timestamps, parsed gauges/counters, raw-file pointer and digest
- `metrics/raw/*.prom`: exact Prometheus samples
- `fco.jsonl`: content and occurrence identity, local context
- `fcg.jsonl`: typed links (relationships only, no causality)
- `verification.json`: local arithmetic/source integrity result and explicit verification limits
- `run_summary.json`: source fingerprints and model provenance gaps

**Lane B exchange:** `schemas/lane_b_results.schema.json`, documented in `docs/LANE_B_HANDOFF.md`.

**Model comparison:** run notebook separately for each actually served model, freezing prompt, sampler interval, max completion tokens, and recording weight/tokenizer IDs if available. Do not assume switching the notebook's `MODEL_NAME` switches the GPU server model.

## Recovered execution evidence

[Module 7–9 receipts and original publication context](docs/RECOVERED_PUBLICATION_README.md) · [Coverage and custody audit](docs/EVIDENCE_COVERAGE_AUDIT.md)

Recovered answer commitment discrepancies remain unresolved; bundled scores are not admitted by this audit. Private raw outputs and recovery archives are excluded.
