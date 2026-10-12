# Bounded Claude follow-up during submission recording

## Goal

While the operator records the HackerSquad video, do a short CPU-only review that improves the submission evidence index and confirms the dashboard can show current sanitized status. This work is independent of live inference and must not delay recording or submission.

## Allowed work

- Read the current results branch and PR #12 at https://github.com/biobitworks/cell-akamai/pull/12.
- Inspect existing local JSON receipts and dashboard code, without editing frozen datasets, prior evidence, private ledgers, or serving/deployment configuration.
- Produce a concise sanitized evidence index with links/paths to the source PR, offline verification receipt, independent scoring receipt, recovered pilot aggregate, and the current sustained-run state/failure.
- Check that the local aggregate dashboard reads the latest valid snapshot and exposes only its intended whitelisted fields. If the dashboard can be started from an existing snapshot without touching serving, it may be viewed on loopback only. Do not expose raw answers or private paths in the index.
- Return findings and any proposed correction as a reviewable patch or report for Codex. Do not publish the index externally.

## Hard limits

- CPU and filesystem reads only. No Akamai calls, inference requests, GPU work, benchmark launch, or competing load.
- No Kubernetes, vLLM, model, precision, scheduler, or serving changes; no port-forward operation.
- Do not alter frozen datasets or existing receipts. Do not make commits, push branches, open/update PRs, or publish dashboards.
- Keep all output aggregate-only and sanitized. Do not copy raw model responses, credentials, environment variables, kubeconfig, or private logs.
- Do not describe the longer study as complete. The current design has 48 five-minute windows across four eligible representations/configurations; the latest attempted run recorded 0/48 and failed preflight before inference.

## Stop condition

Stop after the evidence index and dashboard redaction/status check are complete. Report exact files inspected, snapshot/run IDs and states, any issue found, and a concise proposed fix. If any step requires live serving access or changes, leave it for Codex and continue no further.
