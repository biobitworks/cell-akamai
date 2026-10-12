#!/usr/bin/env python3
"""Convert an EXECUTED Akamai smoke-run receipt (akamai_run_001.zip layout) into a Lane A run folder.

No value is invented: observations, durations, token counts and raw Prometheus bytes are copied from the
receipt; derived rates are recomputed by Lane A's own enrich/verify code. Chunk counts are never used as tokens.
Usage: ingest_smoke_run.py EXTRACTED_DIR LANE_A_PACKAGE_DIR RUNS_ROOT [SOURCE_ZIP]
"""
import hashlib, json, sys
from pathlib import Path


def main(src, pkg, runs_root, src_zip=None):
    src, runs_root = Path(src), Path(runs_root)
    sys.path.insert(0, str(pkg))
    from cell_akamai.kinetics import enrich_observations, verify_kinetics, bytes_digest, content_digest, canonical_bytes
    from cell_akamai.custody import make_fco, make_edge
    from cell_akamai.prometheus import parse_metrics

    rcpt = json.loads((src / "experiment_receipt.json").read_text())
    run_id = "akamai-smoke-" + rcpt["run_id"]
    d = runs_root / run_id
    (d / "metrics" / "raw").mkdir(parents=True, exist_ok=False)
    wj = lambda p, o: p.write_bytes(canonical_bytes(o) + b"\n")
    wl = lambda p, rows: p.write_bytes(b"".join(canonical_bytes(x) + b"\n" for x in rows))
    src_zip_sha = bytes_digest(Path(src_zip).read_bytes()) if src_zip else "UNKNOWN"
    receipt_sha = bytes_digest((src / "experiment_receipt.json").read_bytes())
    model = rcpt["source"]["model"]

    # observations (immutable source fields only; derived fields come from Lane A code)
    rows = []
    for i, r in enumerate(rcpt["records"]):
        start = r["start_ns"]
        rows.append({"schema": "cell_akamai.inference_observation.v1", "source_class": "OBSERVED", "run_id": run_id, "sequence": i,
            "model": model, "model_revision": "UNKNOWN", "tokenizer_revision": "UNKNOWN",
            "prompt_ref": "AKAMAI_WORKSHOP_FCO_TOKEN_SMOKE_V1", "prompt_sha256": r["prompt_sha256"],
            "request_content_id": r["prompt_sha256"], "wall_time_utc": r["started_utc"], "started_mono_ns": start,
            "ended_mono_ns": start + r["duration_ns"], "completion_tokens": r["completion_tokens"], "prompt_tokens": None,
            "first_content_mono_ns": start + r["first_nonempty_chunk_elapsed_ns"], "response_id": r["response_id"],
            "stream_events": [{"sequence": k, "elapsed_ns": c["elapsed_ns"], "chunk_sha256": c["chunk_content_sha256"], "note": "stream_chunk_not_token"}
                              for k, c in enumerate(r["chunks"])],
            "finish_reason": None, "status": r["status"], "response_sha256": r["response_sha256"]})
    enriched = enrich_observations(rows)
    arithmetic = verify_kinetics(enriched)

    # telemetry: copy raw prom bytes unchanged, verify against receipt digest, parse with Lane A parser
    samples = []
    for idx, m in enumerate(rcpt["metrics_files"]):
        name = f"metrics_run{m['run']}_{m['phase']}.prom"
        raw = (src / name).read_bytes()
        if bytes_digest(raw) != m["sha256"]:
            sys.exit("RAW METRIC DIGEST MISMATCH vs receipt: " + name)
        (d / "metrics" / "raw" / name).write_bytes(raw)
        samples.append({"sample_index": idx, "wall_time_utc": None, "mono_ns": None, "metric_source": rcpt["source"]["metrics_source"],
            "source_class": "OBSERVED", "status": "OBSERVED", "raw_sha256": m["sha256"], "raw_ref": f"metrics/raw/{name}",
            "phase": m["phase"], "run": m["run"], "samples": parse_metrics(raw.decode("utf-8", errors="replace"))})
    wl(d / "telemetry_samples.jsonl", samples)
    wl(d / "inference_observations.jsonl", enriched)

    # FCO/FCG projections (local, unadmitted); predecessor = the executed receipt
    ctx = {"project": "cell-akamai", "run_id": run_id}
    run_fco = make_fco("ExperimentRun", {"run_id": run_id, "model": model, "namespace": rcpt["source"]["namespace"]}, ctx)
    pred = make_fco("SourceReceipt", {"receipt_run_id": rcpt["run_id"], "experiment_id": rcpt["experiment_id"], "receipt_sha256": receipt_sha,
                                       "source_zip_sha256": src_zip_sha}, ctx)
    fcos, edges = [run_fco, pred], [make_edge(run_fco, pred, "derived_from")]
    for row in enriched:
        obs = {k: v for k, v in row.items() if k != "stream_events"}
        node = make_fco("InferenceObservation", obs, {**ctx, "sequence": row["sequence"], "source_sha256": content_digest(row)})
        fcos.append(node); edges.append(make_edge(node, run_fco, "observed_in"))
        if row["tokens_per_s"] is not None:
            dv = make_fco("TokenKineticsDerivation", {"tokens_per_s": row["tokens_per_s"], "tokens_per_s2_inter_request": row["tokens_per_s2_inter_request"],
                          "method": row["measurement_semantics"]}, {**ctx, "sequence": row["sequence"]})
            fcos.append(dv); edges.append(make_edge(dv, node, "derived_from"))
    for s in samples:
        node = make_fco("MetricsObservation", {"status": s["status"], "raw_sha256": s["raw_sha256"], "metric_samples": s["samples"]},
                        {**ctx, "sample_index": s["sample_index"], "source_ref": s["raw_ref"]})
        fcos.append(node); edges.append(make_edge(node, run_fco, "observed_in"))
    wl(d / "fco.jsonl", fcos); wl(d / "fcg.jsonl", edges)
    wj(d / "run_manifest.json", {"schema": "cell_akamai.run_manifest.v1", "run_id": run_id, "converted_from": {"receipt_sha256": receipt_sha, "source_zip_sha256": src_zip_sha,
        "receipt_run_id": rcpt["run_id"], "producer": "AKAMAI_WORKSHOP_FCO_TOKEN_SMOKE_V1.ipynb"}, "model_id": model, "model_revision": "UNKNOWN",
        "execution_location": "Akamai workshop namespace " + rcpt["source"]["namespace"], "source_class": "OBSERVED",
        "note": "adapter conversion; independent_reexecution NOT_TESTED; receipt MMR NOT_COMMITTED, unsigned"})
    ver = {"status": "PASS" if arithmetic["status"] == "PASS" else "FAILED", "arithmetic": arithmetic, "independent_host_replay": "NOT_TESTED",
           "signing_state": "NOT_SIGNED", "mmr_state": "NOT_COMMITTED", "mmr_root": "NOT_COMPUTED", "claim_ceiling": "LOCAL_RECOMPUTATION_NOT_EXTERNAL_VERIFICATION"}
    wj(d / "verification.json", ver)
    wj(d / "run_summary.json", {"schema": "cell_akamai.run_summary.v1", "run_id": run_id, "model": model, "model_revision": "UNKNOWN", "source_class": "OBSERVED",
        "project": "cell-akamai", "wall_time_utc": rcpt["records"][0]["started_utc"], "endpoint_origin": "http://vllm:8000", "namespace": rcpt["source"]["namespace"],
        "run_count": len(rows), "request_success_count": sum(r["status"] == "OBSERVED" for r in rows), "metric_sample_count": len(samples),
        "metric_success_count": len(samples), "verification": ver["status"],
        "source_files": {"manifest": "run_manifest.json", "inference": "inference_observations.jsonl", "telemetry": "telemetry_samples.jsonl", "fco": "fco.jsonl", "fcg": "fcg.jsonl"},
        "source_sha256": {n: bytes_digest((d / n).read_bytes()) for n in ("run_manifest.json", "inference_observations.jsonl", "telemetry_samples.jsonl", "fco.jsonl", "fcg.jsonl")},
        "semantics": {"ttfc": "first nonempty streamed content, not vLLM TTFT", "throughput": "completion tokens / total request wall time",
                      "acceleration": "inter-request rate derivative by request midpoints", "chunk_is_token": False}})
    print(run_id, "verification:", ver["status"])


if __name__ == "__main__":
    main(*sys.argv[1:5])
