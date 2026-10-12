# Third-party material and attribution

The repository-level licenses cover only rights-valid original Cell-Akamai
contributions: software under Apache-2.0, original non-software creative
material under CC BY-NC-ND 4.0. See [LICENSES.md](../LICENSES.md) for
file-type scope. Neither license changes third-party rights or licenses
content its contributors do not own.

## Akamai inference workshop reference

This repository references the public
[Akamai AI inference workshop](https://github.com/akamai-developers/akamai-workshop-ai-inference)
and its Modules 00–09. At pinned upstream commit
`454b43269216c1f92dd8d7e2711649e38cb888cb`, the upstream **README
explicitly declares "License: Apache-2.0"**, while a dedicated root
`LICENSE` file was not found by the read-only repository lookup. Do not
state that upstream lacks a license declaration. Confirm any applicable
file-specific notices and attribution before republishing upstream material.

Cell-Akamai describes its notebooks as independent companion and measurement
notebooks, not copies of upstream workshop notebooks. Prior read-only
comparison of a speculative-decoding companion with the upstream Module 6
notebook reported no identical source lines longer than 40 characters and
low whole-cell similarity (roughly 8% Markdown, 11% code). **This is triage,
not a license, an authorization, or a legal clearance.** The public
repository still requires a complete redistributed-content review to exclude
unauthorized copied course text, figures or other protected items. Preserve
any third-party notices for material properly reused under its own terms.

No Akamai workshop software or prose becomes an original Cell-Akamai
contribution merely by appearing in this repository. These Cell-Akamai
license texts cannot supersede third-party conditions or trademarks.

## Dependencies and model services

The [dated third-party licensing inventory](THIRD_PARTY_LICENSE_INVENTORY_20261012.md)
records pinned SDK metadata and separately licensed inference models. It is not a
resolved transitive dependency SBOM or model-redistribution grant.

Python dependencies are declared separately in `pyproject.toml` and module
requirements; dependencies are not licensed by Cell-Akamai's root Apache-2.0
notice. Review and retain upstream licenses and notices in distributed
dependency bundles. Model weights, tokenizer assets, output rights and
Akamai-hosted service access remain governed by their own terms.

## Evidence and model outputs

Committed evidence includes structured receipts, measurements, hashes,
indexes and notebook/snapshot projections. Earlier sanitized snapshot
checks excluded private responses and credentials, but **did not constitute
a comprehensive audit of all current Git history**. Public disclosure of
numeric measurements does not establish scientific validity or ownership
of source data. Raw model outputs, third-party data and confidential
materials may require rights/privacy reviews independent of SHA-256 hashes.

## Release clearance status

- **PUBLIC:** repository visibility observed as public on 2026-10-12.
- **LICENSE TEXTS:** original software Apache-2.0; original non-software
  CC BY-NC-ND 4.0; separate rights and notices retained.
- **NOT COMPLETED:** whole-history secrets/privacy review, independent
  third-party redistribution review, and an upstream-material-by-file
  publication signoff.
- **NEXT_ACTION:** inspect public Git history, notebooks, tracked artifacts,
  licensed third-party material and excluded private sources; if exposure
  is detected, revoke any credentials and document mitigation independently
  rather than relying only on later commits.
