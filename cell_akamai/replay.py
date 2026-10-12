"""Independent *process-capable* local reread and verification of exported files."""
from __future__ import annotations
import json
from pathlib import Path
from .kinetics import bytes_digest, content_digest, verify_kinetics


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def verify_run(directory: str | Path) -> dict:
    directory = Path(directory)
    summary = json.loads((directory / "run_summary.json").read_text())
    errors = []
    for filename, expected in summary.get("source_sha256", {}).items():
        p = directory / filename
        if not p.is_file() or bytes_digest(p.read_bytes()) != expected:
            errors.append(f"SOURCE_DIGEST_MISMATCH:{filename}")
    rows = load_jsonl(directory / "inference_observations.jsonl")
    arithmetic = verify_kinetics(rows)
    if arithmetic["status"] != "PASS":
        errors.append("KINETICS_RECOMPUTATION_FAILED")
    fcos = load_jsonl(directory / "fco.jsonl")
    edges = load_jsonl(directory / "fcg.jsonl")
    ids = set()
    for f in fcos:
        if f.get("content_id") != content_digest({"kind": f.get("kind"), "content": f.get("content")}):
            errors.append("FCO_CONTENT_ID_MISMATCH")
        if f.get("occurrence_id") != content_digest({"content_id": f.get("content_id"), "context": f.get("context")}):
            errors.append("FCO_OCCURRENCE_ID_MISMATCH")
        ids.add(f.get("occurrence_id"))
    for edge in edges:
        if edge.get("src") not in ids or edge.get("dst") not in ids:
            errors.append("FCG_DANGLING_EDGE")
    for s in load_jsonl(directory / "telemetry_samples.jsonl"):
        if s.get("status") != "OBSERVED":
            continue
        # Ref may only refer to the run root or below; refuse traversal.
        rel = Path(s.get("raw_ref") or "")
        if rel.is_absolute() or ".." in rel.parts:
            errors.append("UNSAFE_RAW_REF")
            continue
        p = directory / rel
        if not p.is_file() or bytes_digest(p.read_bytes()) != s.get("raw_sha256"):
            errors.append("PROMETHEUS_RAW_DIGEST_MISMATCH")
    return {"status": "PASS" if not errors else "FAILED", "errors": sorted(set(errors)),
            "run_id": summary.get("run_id"), "arithmetic": arithmetic["status"],
            "fco_count": len(fcos), "fcg_edge_count": len(edges),
            "verification_type": "disk_readback_local", "independent_host_verification": "NOT_TESTED",
            "signed": False, "mmr_root": "NOT_COMPUTED", "mmr_committed": False}
