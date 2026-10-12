# Public release: Git-history security and licensing audit

**Date:** 2026-10-12 · **Repository:** `biobitworks/cell-akamai` (PUBLIC) ·
**Canonical evidence:** [GitHub Actions run #38323784985](https://github.com/biobitworks/cell-akamai/actions/runs/38323784985) on [PR #20](https://github.com/biobitworks/cell-akamai/pull/20).

## Verdict

| Independent gate | State | Evidence |
| --- | --- | --- |
| Public judge access to repository files | **PASS** | GitHub repository visibility `public`; judge guide and saved snapshot exist |
| Scanner coverage across reachable published Git refs | **PASS, bounded** | 94 reachable commits under fetched branch/tag refs; pinned Gitleaks 8.30.1 `--log-opts='--all' --redact` |
| High-confidence secret candidates | **0 unresolved** | One `generic-api-key` candidate; independently recomputed as SHA-256 inventory digest |
| Dual original-content license files | **PASS** | Apache-2.0 software; CC BY-NC-ND 4.0 original non-software, LICENSES/NOTICE |
| Current tracked key/model-weight-like file names | **0 present** | GitHub Actions checkout inventory, 284 tracked files, 21 notebooks |
| Notebook copying vs pinned Akamai workshop | **No substantial overlap detected by automated triage** | 21 Cell-Akamai vs 10 Akamai notebooks, longest normalized 6-token-shingle cell overlap score 0.076923 |
| Upstream exact blob equality | **0 identical Git blobs** | Current Cell-Akamai Git tree against pinned Akamai workshop tree |
| Rights to third-party models, outputs, datasets, and any undisclosed contributions | **NOT_CERTIFIED** | No ownership attestations or complete external rights agreements provided |
| Unreachable/dangling local Git objects and already-forked copies | **OUT_OF_SCOPE / UNKNOWN** | Reachable Git refs only |
| Complete legal release signoff | **NOT_CERTIFIED** | Human third-party and author-rights review remains distinct from automated technical audit |

## 1. Reproducible Git-history security receipt

Workflow: [`.github/workflows/public-release-audit.yml`](../.github/workflows/public-release-audit.yml).

1. Checkout history with `fetch-depth: 0`, fetch every published `refs/heads/*` and `refs/tags/*` into a temporary GitHub-hosted runner. The audit evaluated **94 reachable commits** across fetched refs, including the PR test state. This is not a claim that inaccessible/dangling objects were searched.
2. Download [Gitleaks v8.30.1](https://github.com/gitleaks/gitleaks/releases/tag/v8.30.1) from its published Linux x64 release and **verify archive SHA-256** `551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb` before execution.
3. Execute `gitleaks git --log-opts='--all' --redact --report-format=json`. Preserve the candidate report **only ephemerally on the CI runner**, with public logs containing rule counts and no matched values.
4. One `generic-api-key` candidate was detected at `PACKAGE_MANIFEST.json` at commit `26da5ca8fd3e73e958b69e504651a6766e6ceb20`. This predecessor was already documented in [RELEASE_LICENSING_AUDIT.md](RELEASE_LICENSING_AUDIT.md). The new workflow **recomputed SHA-256** from historical `notebooks/10_token_kinetics.ipynb`, checked it appears in the corresponding historical manifest, and admitted **only** the sole expected finding with the expected rule, path and commit. This is a noncredential inventory hash, not a silently suppressed scanner finding.
5. Result: `finding_count=1`, `verified_noncredential_inventory_digest_count=1`, `unresolved_candidate_count=0`; **workflow success**. Scanner's raw exit code `1` reflects the detected candidate before its separate deterministic triage.
6. Current checkout inventory: `tracked_files=284`, `tracked_notebooks=21`; root Apache/CC dual license files, LICENSES, NOTICE and third-party notice present. No tracked filename with the screened private-key/model-weight extensions. Filename inspection does not assert content safety.

**Limits:** Gitleaks is a secret-pattern detector, not a complete privacy, malware, trade-secret, credentials-validity, data-protection or intellectual-property review. Existing public disclosure cannot be reversed by a later deletion, and the audit does not prove all secrets absent. On suspected actual credential exposure, revoke/rotate affected credentials and open a private incident response, without copying raw values into issues.

## 2. Dependency and external-material custody

| Component or class | Observed declaration / origin | Distribution and licensing disposition |
| --- | --- | --- |
| Original Cell-Akamai executable Python, tooling, tests and code cells | [LICENSE](../LICENSE), [LICENSES.md](../LICENSES.md), [NOTICE](../NOTICE) | **Apache-2.0** where original/rights-valid; not a blanket grant to third parties |
| Original notebook narrative, documents and media authored for this repo | [Non-code license](../LICENSE-NONCODE-CC-BY-NC-ND-4.0.txt) | **CC BY-NC-ND 4.0**, noncommercial; downstream sharing of adaptations is restricted |
| Akamai inference workshop Modules 00–09 | `akamai-developers/akamai-workshop-ai-inference` pinned `454b43269216c1f92dd8d7e2711649e38cb888cb` | Upstream README declares **Apache-2.0**; standalone root LICENSE not found in that pinned tree; retain attribution and check any file-specific notices |
| Python build and regular requirements | `setuptools>=68`, `openai>=1.40`, `requests>=2.31`, `matplotlib>=3.8` | External installations, **not vendored**; each resolves to its own upstream version/license. `>=` constraints do not form a pinned release SBOM |
| Test dependency | `pytest>=8` | External installation; own distribution license |
| Strands module requirements | `strands-agents[openai]==1.60.0`, `openai==2.54.0` | Version-pinned external Python installations; no source vendoring asserted |
| Served and local models | Qwen3-4B vLLM on Akamai; local Ollama Llama 3.2 3B | Model weights are **not included** in current tracked file inventory; provider/model terms are independent of Apache-2.0 repo code and must be honored when redistributing models or outputs |
| Frozen ECA fixtures, FCO/FCG projections, aggregate dashboard | Generated/synthetic task data and serialized evidence, linked in [judge quick review](JUDGES_QUICK_REVIEW.md) | No independent biological dataset ownership asserted; scientific status/commitments remain separate from copyright and file hashes |
| Executed model outputs, private logs, credentials, historical backups | Excluded by contributor publication policy | Root license notices **do not authorize** release of confidential or separately licensed material |

### Source overlap triage

- Current Git trees compared: **282** Cell-Akamai blobs at comparison snapshot and **75** upstream-workshop blobs; **zero matching Git blob hashes**. Later commits may alter totals; this is a time-scoped observation.
- Notebook source compared using normalized 6-token consecutive-word shingles across **21** Cell-Akamai and **10** pinned upstream notebooks. Highest short-cell overlap fraction was approximately **7.69%** (3 common 6-token shingles in speculative-decoding Markdown). Other notebook cells scored lower/zero. This detects literal and near-literal copying only and **cannot establish legal originality, license compatibility or ownership**.
- No tracked current binary media or model weight artifacts were listed by the tree/file extension inventory at inspection time. Dependencies installed at run time are not automatically redistributed in the repository.
- Referenced upstream module names and links do not themselves transfer rights in upstream screenshots, diagrams, source code, model weights or dataset assets.

## 3. Custody and remaining release limitations

- Root license notices are **present and internally scoped**. Notebook cells are split by executable code versus creative Markdown/media; third-party content keeps separate rights.
- A public reviewer can browse the [judge guide](JUDGES_QUICK_REVIEW.md) and saved `judges/` HTML/JSON snapshot without private run files. The public snapshot is **not live GPU access**.
- No trained-model accuracy/quality gain, canonical project MMR completion, independent scientific correctness or model-output redistribution right is implied by the security/rights audit.
- **Manual author-rights and third-party legal signoff remains required** for any redistributed content with disputed ownership, copied media, model assets or data contracts. The automated notebook comparison and README license are evidence supporting assessment, not a substitute for rights-holder approval.
- A dedicated dependency SBOM for a resolved frozen environment has **not** been computed because the root package uses unconstrained upper versions and no deployed lockfile was recovered.

## NEXT_ACTION

1. Treat the Gitleaks history gate as **PASS with one specifically recomputed false positive**, scoped to the ref set and CI run above; preserve run link, commit SHA and artifact count.
2. Keep publication warnings for **third-party author/redistribution permissions, full external-data privacy/trade-secret review, and unpinned dependency SBOM**. These remain `NOT_CERTIFIED`; do not rewrite them as PASS merely because the repository is public.
3. Re-run the workflow on future `main` updates, preserving scanner findings and failed predecessors. For any new unmatched candidate, **fail closed** and triage privately.
4. Keep GitHub Issue [#18](https://github.com/biobitworks/cell-akamai/issues/18) as the canonical tracker for residual external rights and release-hardening work.

**Auditor method:** GitHub API source/tree inspection, checksum-pinned redacted Gitleaks GitHub Actions execution, independently recomputed manifest SHA-256 false-positive check, static notebook upstream overlap comparison, package/NOTICE/third-party source review. **No new inference, GPU experiments or scientific benchmark were executed.**
