"""Minimal fail-closed Lane B exchange validator, no additional notebook dependency."""
from __future__ import annotations
import math

ARMS = {"B0_FIXED", "B1_GENESIS", "B2_GENESIS_DAISY", "B3_RANDOM_CONTROL"}
STATES = {"OBSERVED", "FAILED", "NOT_TESTED", "UNKNOWN", "NOT_COMPUTED"}
SOURCES = {"OBSERVED", "SYNTHETIC_FIXTURE", "DERIVED_EVIDENCE", "UNKNOWN"}
REQUIRED = ("schema_version", "experiment_id", "arm", "metric", "unit",
            "status", "evidence_ref", "evaluation_split", "source_class")


def validate_lane_b_result(row) -> list[str]:
    if not isinstance(row, dict): return ["ROW_NOT_OBJECT"]
    errors = ["REQUIRED_MISSING:" + k for k in REQUIRED if k not in row]
    if row.get("schema_version") != "cell_akamai.lane_b_result.v1":
        errors.append("SCHEMA_MISMATCH")
    if row.get("arm") not in ARMS: errors.append("ARM_UNKNOWN")
    if row.get("status") not in STATES: errors.append("STATUS_UNKNOWN")
    if row.get("source_class") not in SOURCES: errors.append("SOURCE_CLASS_UNKNOWN")
    for key in ("experiment_id", "metric", "unit", "evidence_ref", "evaluation_split"):
        if not isinstance(row.get(key), str) or not row[key].strip():
            errors.append("EMPTY:" + key)
    v=row.get("value")
    if row.get("status") == "OBSERVED":
        if type(v) not in (float, int) or not math.isfinite(v):
            errors.append("OBSERVED_REQUIRES_FINITE_VALUE")
    elif v is not None:
        errors.append("NON_OBSERVED_VALUE_MUST_BE_NULL")
    return errors
