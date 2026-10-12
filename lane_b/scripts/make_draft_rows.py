#!/usr/bin/env python3
"""Generate DRAFT Lane B exchange rows (all NOT_TESTED / NOT_COMPUTED, value=null).

No measurement is produced here. Run from the package root: python3 lane_b/scripts/make_draft_rows.py
"""
import json
from pathlib import Path
try:
    from cell_akamai.contract import validate_lane_b_result  # Lane A validator (PR #3), when installed
except ModuleNotFoundError:  # standalone: check the fields this script writes against the shared schema file
    def validate_lane_b_result(row):
        schema = json.loads((Path(__file__).resolve().parents[2] / "schemas/lane_b_results.schema.json").read_text()) \
            if (Path(__file__).resolve().parents[2] / "schemas/lane_b_results.schema.json").exists() else {"required": []}
        return [f"missing {k}" for k in schema.get("required", []) if k not in row]

PREREG = "lane_b/PREREGISTRATION_DRAFT.md#v0.1-DRAFT-UNFROZEN"
ARMS = ["B0_FIXED", "B1_GENESIS", "B2_GENESIS_DAISY", "B3_RANDOM_CONTROL"]
# (metric, unit, status)
METRICS = [
    ("exact_match_accuracy_primary", "fraction", "NOT_TESTED"),
    ("mean_hamming_error", "fraction_of_cells", "NOT_TESTED"),
    ("abstention_rate", "fraction", "NOT_TESTED"),
    ("parse_failure_rate", "fraction", "NOT_TESTED"),
    ("completion_tokens_total", "tokens", "NOT_TESTED"),
    ("wall_time_total", "s", "NOT_TESTED"),
    ("request_tokens_per_s", "tokens/s", "NOT_TESTED"),
    ("anticube_operational_class", "class", "NOT_COMPUTED"),
    ("delta_g_star", "UNDEFINED_NO_VALIDATED_FORMULA", "NOT_COMPUTED"),
]
CEILING = "DRAFT_PREREGISTERED_NOT_EXECUTED; synthetic ECA control only; no generalization, biological, or physical-energy claim"

rows = []
for arm in ARMS:
    for metric, unit, status in METRICS:
        rows.append({
            "schema_version": "cell_akamai.lane_b_result.v1",
            "experiment_id": "EXP-LANEB-GDAISY-001-DRAFT",
            "arm": arm, "model": None, "dataset_ref": "ECA_NEXT_ROW_w8_rules30-90-110-184_UNFROZEN",
            "model_revision": None, "metric": metric, "unit": unit, "value": None, "status": status,
            "evidence_ref": PREREG, "evaluation_split": "HELDOUT_UNFROZEN",
            "source_class": "UNKNOWN", "preregistration_ref": PREREG,
            "commit_sha": None, "fco_occurrence_id": None, "claim_ceiling": CEILING,
        })
bad = [(i, e) for i, r in enumerate(rows) if (e := validate_lane_b_result(r))]
assert not bad, bad
out = Path("data/lane_b_results.jsonl")
out.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
print(f"wrote {len(rows)} rows, all valid, none observed")
