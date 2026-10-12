"""Deterministic, unit-explicit derivatives of measured token throughput.

No interpolation of missing completion counts. Stream chunks are not tokenizer tokens.
Raw monotonic timestamps are recorded in nanoseconds and time is converted
into seconds only for these derived measurements.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any


def canonical_bytes(value: Any) -> bytes:
    """Project-local canonical JSON v1; NOT RFC8785/JCS."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def content_digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def bytes_digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def enrich_observations(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compute request throughput and midpoint-based *inter-request* acceleration.

    Throughput = reported completion_tokens / wall duration. This is **not**
    decode-only throughput; TTFC is first content chunk, not vLLM's true TTFT.
    Acceleration = difference in two request-average rates divided by distance
    between request midpoints. It is NOT a per-token acceleration measurement.
    """
    out = []
    prev = None
    for row in rows:
        d = dict(row)
        start = d.get("started_mono_ns")
        end = d.get("ended_mono_ns")
        tokens = d.get("completion_tokens")
        duration_s = None
        mid_ns = None
        if isinstance(start, int) and isinstance(end, int) and end > start:
            duration_s = (end - start) / 1e9
            mid_ns = (start + end) / 2
        d["duration_s"] = duration_s
        d["midpoint_mono_ns"] = mid_ns
        if (type(tokens) is int and tokens >= 0 and duration_s is not None):
            d["tokens_per_s"] = tokens / duration_s
        else:
            d["tokens_per_s"] = None
        d["tokens_per_s2_inter_request"] = None
        if prev is not None and d["tokens_per_s"] is not None and prev.get("tokens_per_s") is not None:
            if mid_ns is not None and prev["midpoint_mono_ns"] is not None:
                midpoint_dt_s = (mid_ns - prev["midpoint_mono_ns"]) / 1e9
                if midpoint_dt_s > 0:
                    d["tokens_per_s2_inter_request"] = (d["tokens_per_s"] - prev["tokens_per_s"]) / midpoint_dt_s
        d["ttfc_s"] = (d["first_content_mono_ns"] - start) / 1e9 if (
            isinstance(start, int) and isinstance(d.get("first_content_mono_ns"), int)
            and d["first_content_mono_ns"] >= start
        ) else None
        d["source_class"] = row.get("source_class", "OBSERVED")
        d["measurement_semantics"] = {
            "tokens_per_s": "completion_tokens / request_wall_duration_s",
            "tokens_per_s2_inter_request": "delta(request_average_tokens_per_s)/delta(request_midpoint_s)",
            "ttfc_s": "first_nonempty_stream_content_arrival - request_start; NOT server TTFT",
        }
        out.append(d)
        prev = d
    return out


def verify_kinetics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Replay derived values from immutable source fields, without trusting saved results."""
    immutable = [{k: v for k, v in r.items() if k not in (
        "duration_s", "midpoint_mono_ns", "tokens_per_s", "tokens_per_s2_inter_request",
        "ttfc_s", "measurement_semantics", "source_class")}
                 for r in rows]
    rebuilt = enrich_observations(immutable)
    mismatches = []
    for i, (a, b) in enumerate(zip(rows, rebuilt)):
        for key in ("duration_s", "midpoint_mono_ns", "tokens_per_s",
                    "tokens_per_s2_inter_request", "ttfc_s"):
            saved = a.get(key)
            actual = b.get(key)
            equal = saved == actual if saved is None or actual is None else (
                isinstance(saved, (float, int)) and isinstance(actual, (float, int))
                and math.isclose(saved, actual, abs_tol=1e-10, rel_tol=1e-12))
            if not equal:
                mismatches.append({"row": i, "field": key, "saved": saved, "recomputed": actual})
    return {"status": "PASS" if not mismatches else "FAILED", "row_count": len(rows),
            "mismatches": mismatches, "verification_type": "local_arithmetic_recomputation_v1"}
