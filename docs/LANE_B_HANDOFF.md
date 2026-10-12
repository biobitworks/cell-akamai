# Claude Lane B → Lane A handoff (v1)

**Exchange file:** `data/lane_b_results.jsonl` (one JSON object per line; no markdown).

**Schema:** `schemas/lane_b_results.schema.json`.

Use exact arms `B0_FIXED`, `B1_GENESIS`, `B2_GENESIS_DAISY`, `B3_RANDOM_CONTROL`. Bind every result to `experiment_id`, metric name, unit, dataset/split, preregistration, model/checkpoint revision, source reference, execution state, and evidence ref. Preserve non-results with `value:null` and appropriate status. Never fabricate Anticube, ΔG*, or MMR values. Provide the exact formula IDs and validated preregistration before a future expansion of those panels.

**Pull/PR workflow:** Claude works in `lane/claude-msm`, commits its own files, pushes, and opens a PR. Lane A imports only reviewed JSONL and known schema. Claude may comment the evidence file path and commit SHA on the Lane A GitHub Issue; do not edit Lane A code or notebooks.

**Incorporation into Lane A dashboard:** `write_dashboard("runs", "data/lane_b_results.jsonl", "lane_a_dashboard.html")`.

**Published Lane A contract:** pending PR review and Lane B integration.
