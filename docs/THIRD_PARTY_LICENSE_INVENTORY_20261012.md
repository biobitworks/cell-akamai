# Third-party software and model licensing inventory

**Checked:** 2026-10-12 · **Scope:** tracked dependency declarations and named inference dependencies for public `biobitworks/cell-akamai`. This is a **source- and metadata-backed inventory**, not a resolved transitive software bill of materials or a substitute for rights-holder permission.

## Software and tooling

| Component | Pinned or declared use | Upstream license evidence | Repo distribution treatment |
| --- | --- | --- | --- |
| [Akamai inference workshop](https://github.com/akamai-developers/akamai-workshop-ai-inference/tree/454b43269216c1f92dd8d7e2711649e38cb888cb) | Pinned reference commit `454b43269216c1f92dd8d7e2711649e38cb888cb` | Upstream [README](https://github.com/akamai-developers/akamai-workshop-ai-inference/blob/454b43269216c1f92dd8d7e2711649e38cb888cb/README.md) states Apache-2.0. No root LICENSE file observed at pinned ref. | Reference/companion-only as examined; upstream names, workflows and any permitted reused material require preservation of appropriate notices |
| [Strands Agents](https://pypi.org/project/strands-agents/1.60.0/) | `strands-agents[openai]==1.60.0` | **Apache-2.0** per this exact PyPI release; publisher attestation also available for the wheel/source package. | External SDK, not vendored |
| [OpenAI Python SDK](https://pypi.org/project/openai/2.54.0/) | `openai==2.54.0` in module9; `openai>=1.40` in root packaging | **Apache-2.0** at pinned 2.54.0; the range is not a resolved package version | External SDK, not vendored |
| [Requests](https://pypi.org/project/requests/) | `requests>=2.31` | **Apache-2.0** per PyPI packaging metadata | External library, not vendored |
| [Matplotlib](https://matplotlib.org/stable/project/license.html) | `matplotlib>=3.8` | **Matplotlib/PSF-derived BSD-compatible license**, with separate contribution terms noted by upstream | External library, not vendored; preserve actual resolved distribution notices |
| [Pytest](https://pypi.org/project/pytest/) | `pytest>=8` test extra | **MIT** per PyPI metadata | External test tool, not vendored |
| [Setuptools](https://pypi.org/project/setuptools/) | `setuptools>=68` build requirement | **MIT** per PyPI metadata | External build tool, not vendored |
| [vLLM](https://github.com/vllm-project/vllm/blob/main/pyproject.toml) | Remote Akamai inference serving runtime; not a vendored Python dependency in repository | **Apache-2.0** declared in upstream `pyproject.toml` and source SPDX notices | Deployed third-party runtime; vLLM container and any bundled dependencies need their own deployed-version inventory |

## Model and data rights

| Model/data | Source | Status |
| --- | --- | --- |
| [Qwen/Qwen3-4B](https://huggingface.co/Qwen/Qwen3-4B) | Original model card shows **Apache-2.0** | Served via Akamai vLLM. Model card/license may govern model use or redistribution; no model-weight files found in present tracked Cell-Akamai tree |
| [Meta Llama 3.2 3B](https://huggingface.co/meta-llama/Llama-3.2-3B) | **Llama 3.2 Community License**, not Apache-2.0 and not automatically an OSI open-source software license | Local Ollama model. Terms can include attribution/redistribution and acceptable-use requirements. We observed no repository-shipped model weights; do **not** apply Cell-Akamai Apache-2.0 to Llama weights |
| Generated 32-task ECA workload and original/FCO/FCG projections | Frozen synthetic Cell-Akamai task lineage | Synthetic evidence/fixtures, not independent biological datasets; scientific validity is not established by licensing |
| Inference outputs, external datasets and private prompts | Depends on provider/experiment | Rights, confidentiality, consent and permitted redistribution **NOT_CERTIFIED**; no blanket assertion that numeric results license input content or model outputs |

## Evidence-backed comparison against the Akamai workshop

A read-only inspection of the pinned upstream and current project Git trees found **zero identical Git blob SHA-1 values** between 282 current project blobs at the inspection snapshot and 75 upstream blobs. A source-cell comparison of **21 project** notebooks against the **10 upstream** workshop notebooks used six-token consecutive-word shingles; maximum short-cell overlap approximately `0.076923` (three shared shingles in speculative-decoding Markdown). These are **copying triage heuristics**; they do not prove authorship, fair use or legal clearance. A third-party image or substantial adapted work could violate rights even when hashes and token similarity are low.

## Release decisions and open compliance bounds

- **PRESENT:** [Apache-2.0 root software license](../LICENSE), [CC BY-NC-ND original nonsoftware license](../LICENSE-NONCODE-CC-BY-NC-ND-4.0.txt), [LICENSES.md](../LICENSES.md), [NOTICE](../NOTICE) and [third-party notices](THIRD_PARTY_NOTICES.md).
- **PRESENT:** Public, independently inspectable [judge snapshot](../judges/index.html). It contains summaries, not a license to redistribute weights, any protected input datasets or raw private logs.
- **NOT_VENDORED:** Current tracked tree contains no binary media/weight artifacts with the evaluated media/weight extensions. This says nothing about local runtime installations or private files.
- **NOT_RESOLVED:** Root dependencies use `>=` ranges; without a frozen environment/package lock, actual installed versions, transitive dependencies, optional extras, Docker layers, and their individual license notices cannot be exhaustively assigned.
- **NOT_CERTIFIED:** Third-party redistribution under external contracts, contributor ownership attestation, trade-secret/privacy clearance and model-output rights require independent authorization. **Do not treat this source inventory as legal signoff.**
- **SCIENCE:** Identity hashes and valid license notices establish neither scientific correctness nor completed self-training, MMR or signed custody.

**NEXT_ACTION:** freeze deployed Python packages and image digests, generate an SPDX/CycloneDX dependency SBOM and review transitive/resolved package notices. For repackaged workshop assets, data, media or model weights, retain provenance and seek rights-holder approval as necessary. Preserve negative results and all audit predecessors. See [full-history audit](PUBLIC_RELEASE_FULL_HISTORY_AUDIT_20261012.md) and [Issue #18](https://github.com/biobitworks/cell-akamai/issues/18).
