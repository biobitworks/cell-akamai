# Third-party material and attribution

The repository-level licenses cover only original Cell-Akamai contributions:
software under Apache-2.0 and non-software material under CC BY-NC-ND 4.0.
They do not change third-party rights or apply to content that contributors do
not own or have permission to license.

## Akamai inference workshop reference

The notebooks reference the public
[Akamai inference workshop](https://github.com/akamai-developers/akamai-workshop-ai-inference)
and name its modules. The checked repository root did not show a license file
or license declaration. Files in this project are described as companion or
measurement notebooks; they do not intentionally include the upstream workshop
notebooks. The speculative-decoding notebook links to the upstream Module 6
notebook and describes a workflow involving workshop modules. A read-only
comparison against the linked Module 6 notebook found no identical source lines
longer than 40 characters and low whole-cell-source similarity (about 8% in
markdown and 11% in code). That check is a triage aid, not a legal conclusion.

No Akamai workshop source, prose, or figures are covered by the licenses in
this repository. Before publication, confirm that the Module 6 workflow
description and companion module references are independently authored and do
not reproduce protected course material. If any upstream content is retained,
obtain permission or remove that content; do not rely on the root license.

## Dependencies

Python dependencies are declared by name and version range in `pyproject.toml`;
their code is installed separately and is not vendored here. Each dependency
remains under its own license. Review dependency licenses when producing a
binary or source bundle that includes dependency code.

## Evidence and model outputs

Committed evidence consists of structured receipts, summaries, hashes,
metrics indexes, and signatures. It does not include raw inference response
logs, raw Prometheus dumps, API credentials, or executed outputs in the
notebooks inspected for this audit. A model name or a reference to a model
does not grant rights to that model or its outputs.
