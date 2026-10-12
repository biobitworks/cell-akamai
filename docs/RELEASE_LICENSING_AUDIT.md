# Public release licensing and secret audit

Audit scope: isolated branch `codex/public-release-audit`, based on
`9f99db6ceb8d` (`Sign deterministic custody checkpoint and explain claim
limits`), on 2026-10-12. No push, merge, publication, or edits to other
worktrees were performed.

## Scoped license files prepared

- Root `LICENSE`: official Apache License 2.0 text, fetched from
  `https://www.apache.org/licenses/LICENSE-2.0.txt`. The scope is limited to
  original software contributors may license.
- `LICENSE-NONCODE-CC-BY-NC-ND-4.0.txt`: Creative Commons BY-NC-ND 4.0
  International legal code, fetched from the Creative Commons official URL.
  Its scope is original prose, notebook narrative, and other non-software
  contributions only.
- `NOTICE` and `docs/THIRD_PARTY_NOTICES.md` state those limits and preserve
  third-party rights.

No third-party source files were intentionally bundled. The Akamai workshop
repo is linked and its module names are referenced. Its visible repository root
does not list a license file or license declaration. The speculative-decoding
notebook links to Module 6; a comparison with the linked upstream notebook
found low source overlap and no long verbatim lines, but this is not a legal
review. The relation between its workflow narrative and the workshop material
still needs contributor confirmation before publication. If it reproduces
protected workshop content, get permission or remove that content; the new
licenses do not cover it.

## Secret scans and content inventory

- `gitleaks git --log-opts=--all --redact` scanned the available repository
  history (66 commits) and found one `generic-api-key` pattern at
  `PACKAGE_MANIFEST.json:24` in commit `26da5ca8fd3e73e958b69e504651a6766e6ceb20`.
  It is a 64-character SHA-256 inventory value for
  `notebooks/10_token_kinetics.ipynb`; the historical blob hash matches that
  value. This is a confirmed false positive, not a credential. No matched value
  is reproduced in this report.
- `gitleaks dir --redact` scanned the checked-out tree and reported the same
  single manifest hash false positive.
- The tracked evidence directory contains 31 files (about 1.6 MB), comprising
  receipts, summaries, dashboards' evidence indexes, and attestation data.
  The reviewed paths do not contain raw inference response logs or raw
  Prometheus snapshots. The tracked result JSONL is a draft of null/NOT_TESTED
  rows, and the frozen ECA dataset contains generated inputs rather than model
  answers.
- Tracked notebooks have no executed model outputs. The sole notebook with
  outputs is the synthetic offline replay fixture; it has three small outputs.
- No credentials were found in the secret scans. Source references environment
  variable names for API keys and endpoints; these are placeholders and no
  credential values are intentionally stored.

## Release state

The scoped licensing files and sanitized notice are prepared on this isolated
branch. Treat publication as blocked until the contributor confirms that the
workshop-referencing notebook prose is independently authored or the relevant
rights are obtained, and a reviewer confirms the target branch and final file
set. The gitleaks match does not require secret rotation or history rewrite.
