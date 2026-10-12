"""Read-only Akamai vLLM observation. No Kubernetes mutation, no model installation."""
from __future__ import annotations
import json
import os
import platform
import sys
import socket
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from .custody import make_edge, make_fco
from .kinetics import canonical_bytes, bytes_digest, content_digest, enrich_observations, verify_kinetics
from .prometheus import parse_metrics


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, data) -> None:
    path.write_bytes(canonical_bytes(data) + b"\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_bytes(b"".join(canonical_bytes(x) + b"\n" for x in rows))


def metric_url(base_url: str) -> str:
    p = urlsplit(base_url)
    path = p.path.rstrip("/")
    path = path[:-3] if path.endswith("/v1") else path
    return f"{p.scheme}://{p.netloc}{path}/metrics"


class MetricsSampler:
    def __init__(self, url: str, out_dir: Path, interval_s: float = 1.0, api_key: str | None = None, source_class: str = "OBSERVED"):
        self.url = url
        self.out_dir = out_dir
        self.interval_s = interval_s
        self.api_key = api_key
        self.source_class = source_class
        self.samples = []
        self._stop = threading.Event()
        self._thread = None
        self._lock = threading.Lock()

    def poll_once(self):
        import requests
        idx = len(self.samples)
        observed_ns = time.perf_counter_ns()
        # No password or auth header is persisted to files.
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key and self.api_key != "not-needed" else {}
        row = {"sample_index": idx, "wall_time_utc": utc_now(),
               "mono_ns": observed_ns, "metric_source": self.url, "source_class": self.source_class,
               "status": "NOT_TESTED", "raw_sha256": None, "raw_ref": None, "samples": []}
        try:
            r = requests.get(self.url, timeout=3, headers=headers)
            r.raise_for_status()
            raw = r.content
            path = self.out_dir / f"{idx:04d}.prom"
            # Each source sample is retained unchanged.
            path.write_bytes(raw)
            row.update({"status": "OBSERVED", "raw_sha256": bytes_digest(raw),
                        "raw_ref": str(path.relative_to(self.out_dir.parent.parent)),
                        "samples": parse_metrics(raw.decode("utf-8", errors="replace"))})
        except Exception as exc:
            # Do not persist exception text: URLs and response bodies may contain secrets.
            row.update({"status": "FAILED", "failure_type": type(exc).__name__})
        with self._lock:
            self.samples.append(row)
        return row

    def start(self):
        self.poll_once()
        def worker():
            while not self._stop.wait(self.interval_s):
                self.poll_once()
        self._thread = threading.Thread(target=worker, daemon=True)
        self._thread.start()

    def close(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
        self.poll_once()


def collect_request(client, *, model: str, prompt: str, prompt_ref: str,
                    max_tokens: int, run_id: str, seq: int,
                    model_revision: str = "UNKNOWN", source_class: str = "OBSERVED") -> dict:
    """Record stream CHUNKS and final usage; never treat chunks as atomic tokens."""
    request_params = {"model": model, "messages": [{"role": "user", "content": prompt}],
                      "temperature": 0, "max_tokens": max_tokens, "stream": True,
                      "stream_options": {"include_usage": True}}
    started = time.perf_counter_ns()
    row = {"schema": "cell_akamai.inference_observation.v1", "source_class": source_class,
           "run_id": run_id, "sequence": seq, "model": model, "model_revision": model_revision,
           "tokenizer_revision": "UNKNOWN", "prompt_ref": prompt_ref,
           "request_content_id": content_digest(request_params),
           "wall_time_utc": utc_now(), "started_mono_ns": started,
           "completion_tokens": None, "prompt_tokens": None,
           "first_content_mono_ns": None, "response_id": None, "stream_events": [],
           "finish_reason": None, "status": "NOT_TESTED", "response_sha256": None}
    output_parts = []
    try:
        stream = client.chat.completions.create(**request_params)
        for event in stream:
            event_time = time.perf_counter_ns()
            if row["response_id"] is None:
                row["response_id"] = getattr(event, "id", None)
            usage = getattr(event, "usage", None)
            if usage is not None:
                row["completion_tokens"] = getattr(usage, "completion_tokens", None)
                row["prompt_tokens"] = getattr(usage, "prompt_tokens", None)
            choices = getattr(event, "choices", None) or []
            if not choices:
                continue
            first = choices[0]
            delta = getattr(first, "delta", None)
            reason = getattr(first, "finish_reason", None)
            if reason:
                row["finish_reason"] = reason
            if delta is None:
                continue
            pieces = [getattr(delta, "reasoning_content", None), getattr(delta, "content", None)]
            for channel, piece in zip(("reasoning_content", "content"), pieces):
                if not isinstance(piece, str) or not piece:
                    continue
                if row["first_content_mono_ns"] is None:
                    row["first_content_mono_ns"] = event_time
                output_parts.append(piece)
                row["stream_events"].append({
                    "sequence": len(row["stream_events"]), "mono_ns": event_time,
                    "elapsed_ns": event_time - started, "channel": channel,
                    "chunk_utf8_bytes": len(piece.encode("utf-8")),
                    "chunk_sha256": bytes_digest(piece.encode("utf-8")),
                    "note": "stream_chunk_not_token"})
        row["status"] = "OBSERVED" if row["completion_tokens"] is not None else "OBSERVED_USAGE_UNKNOWN"
    except Exception as exc:
        row["status"] = "FAILED"
        row["failure_type"] = type(exc).__name__
    finally:
        row["ended_mono_ns"] = time.perf_counter_ns()
        # Content hash detects identical observed bytes, but cannot prove original tokenization.
        row["response_sha256"] = bytes_digest("".join(output_parts).encode("utf-8"))
    return row


def collect_experiment(*, base_url: str | None = None, model: str | None = None,
                       prompt: str | None = None, run_count: int = 4,
                       output_root: str | Path = "runs", max_tokens: int = 128,
                       metric_interval_s: float = 1.0, model_revision: str = "UNKNOWN",
                       prompt_ref: str = "workshop-fixture-aging-v1",
                       source_class: str = "OBSERVED") -> Path:
    from openai import OpenAI
    if not isinstance(run_count, int) or not 1 <= run_count <= 32:
        raise ValueError("run_count must be 1..32")
    if max_tokens < 1 or max_tokens > 1024:
        raise ValueError("max_tokens must be 1..1024")
    base_url = base_url or os.environ.get("VLLM_HOST", "http://vllm:8000/v1")
    model = model or os.environ.get("MODEL_NAME", "Qwen/Qwen3-4B")
    prompt = prompt or "Explain three mechanisms involved in cellular aging, using one sentence per mechanism."
    api_key = os.environ.get("VLLM_API_KEY", "not-needed")
    run_id = "akamai-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    directory = Path(output_root) / run_id
    directory.mkdir(parents=True, exist_ok=False)
    raw_metrics_dir = directory / "metrics" / "raw"
    raw_metrics_dir.mkdir(parents=True)
    # Bind deterministic calculation source identity and execution parameters before requests.
    module_dir = Path(__file__).resolve().parent
    module_digests = {}
    for source_file in ("collect.py", "kinetics.py", "prometheus.py", "custody.py", "replay.py"):
        module_digests[source_file] = bytes_digest((module_dir / source_file).read_bytes())
    manifest = {
        "schema": "cell_akamai.run_manifest.v1",
        "run_id": run_id, "project": "cell-akamai",
        "execution_host": socket.gethostname(), "python_version": sys.version,
        "platform": platform.platform(), "wall_time_utc": utc_now(),
        "endpoint_origin": f"{urlsplit(base_url).scheme}://{urlsplit(base_url).netloc}",
        "model_id": model, "model_revision": model_revision,
        "model_revision_verification": "UNKNOWN",
        "tokenizer_revision": "UNKNOWN", "source_class": source_class,
        "prompt_ref": prompt_ref, "prompt_sha256": bytes_digest(prompt.encode("utf-8")),
        "parameters": {"temperature": 0, "max_tokens": max_tokens, "run_count": run_count,
                       "metric_interval_s": metric_interval_s, "stream": True},
        "calculation_sources": module_digests,
        "auth_details": "NOT_RECORDED",
        "canonicalization": "cell_akamai.python_json_sort_keys_utf8_no_nan_v1",
    }
    write_json(directory / "run_manifest.json", manifest)
    client = OpenAI(base_url=base_url, api_key=api_key, timeout=180)
    sampler = MetricsSampler(metric_url(base_url), raw_metrics_dir, metric_interval_s, api_key, source_class)
    rows = []
    sampler.start()
    try:
        for i in range(run_count):
            row = collect_request(client, model=model, prompt=prompt, prompt_ref=prompt_ref,
                                  max_tokens=max_tokens, run_id=run_id, seq=i,
                                  model_revision=model_revision, source_class=source_class)
            rows.append(row)
            print(f"request {i+1}/{run_count}: {row['status']} ")
    finally:
        sampler.close()
    enriched = enrich_observations(rows)
    write_jsonl(directory / "inference_observations.jsonl", enriched)
    write_jsonl(directory / "telemetry_samples.jsonl", sampler.samples)
    fcos, edges = [], []
    run_fco = make_fco("ExperimentRun", {"run_id": run_id, "model": model},
                       {"project": "cell-akamai", "host": socket.gethostname(), "run_id": run_id})
    fcos.append(run_fco)
    for row in enriched:
        # The content is a safe summary. Full observation bytes are independently stored.
        obs = {k: v for k, v in row.items() if k != "stream_events"}
        context = {"project": "cell-akamai", "run_id": run_id, "sequence": row["sequence"],
                   "source_ref": "inference_observations.jsonl", "source_sha256": content_digest(row)}
        node = make_fco("InferenceObservation", obs, context)
        fcos.append(node)
        edges.append(make_edge(node, run_fco, "observed_in"))
        if row.get("tokens_per_s") is not None:
            derived = make_fco("TokenKineticsDerivation", {
                "tokens_per_s": row["tokens_per_s"],
                "tokens_per_s2_inter_request": row["tokens_per_s2_inter_request"],
                "method": row["measurement_semantics"],
            }, {"run_id": run_id, "sequence": row["sequence"]})
            fcos.append(derived)
            edges.append(make_edge(derived, node, "derived_from"))
    for sample in sampler.samples:
        node = make_fco("MetricsObservation", {"status": sample["status"],
                        "raw_sha256": sample["raw_sha256"], "metric_samples": sample["samples"]},
                        {"run_id": run_id, "sample_index": sample["sample_index"],
                         "source_ref": sample["raw_ref"]})
        fcos.append(node)
        edges.append(make_edge(node, run_fco, "observed_in"))
    write_jsonl(directory / "fco.jsonl", fcos)
    write_jsonl(directory / "fcg.jsonl", edges)
    arithmetic = verify_kinetics(enriched)
    raw_integrity_errors = []
    for s in sampler.samples:
        if s["status"] == "OBSERVED":
            file_path = directory / s["raw_ref"]
            if not file_path.is_file() or bytes_digest(file_path.read_bytes()) != s["raw_sha256"]:
                raw_integrity_errors.append(s["sample_index"])
    fco_errors = []
    for n in fcos:
        if n["content_id"] != content_digest({"kind": n["kind"], "content": n["content"]}):
            fco_errors.append(n["occurrence_id"])
    verification = {"status": "PASS" if arithmetic["status"] == "PASS" and not raw_integrity_errors and not fco_errors else "FAILED",
                    "arithmetic": arithmetic, "metric_source_integrity_errors": raw_integrity_errors,
                    "fco_content_identity_errors": fco_errors, "independent_host_replay": "NOT_TESTED",
                    "signing_state": "NOT_SIGNED", "mmr_state": "NOT_COMMITTED", "mmr_root": "NOT_COMPUTED",
                    "claim_ceiling": "LOCAL_RECOMPUTATION_NOT_EXTERNAL_VERIFICATION"}
    write_json(directory / "verification.json", verification)
    summary = {"schema": "cell_akamai.run_summary.v1", "run_id": run_id, "model": model,
               "model_revision": model_revision, "source_class": source_class,
               "project": "cell-akamai", "wall_time_utc": utc_now(),
               "endpoint_origin": f"{urlsplit(base_url).scheme}://{urlsplit(base_url).netloc}",
               "namespace": os.environ.get("NAMESPACE", "UNKNOWN"),
               "run_count": len(rows), "request_success_count": sum(r["status"].startswith("OBSERVED") for r in rows),
               "metric_sample_count": len(sampler.samples),
               "metric_success_count": sum(s["status"] == "OBSERVED" for s in sampler.samples),
               "verification": verification["status"],
               "source_files": {"manifest": "run_manifest.json", "inference": "inference_observations.jsonl", "telemetry": "telemetry_samples.jsonl",
                                "fco": "fco.jsonl", "fcg": "fcg.jsonl"},
               "source_sha256": {name: bytes_digest((directory / name).read_bytes()) for name in (
                   "run_manifest.json", "inference_observations.jsonl", "telemetry_samples.jsonl", "fco.jsonl", "fcg.jsonl")},
               "semantics": {"ttfc": "first nonempty streamed content, not vLLM TTFT",
                             "throughput": "completion tokens / total request wall time",
                             "acceleration": "inter-request rate derivative by request midpoints",
                             "chunk_is_token": False}}
    write_json(directory / "run_summary.json", summary)
    print(f"Completed {run_id} | local verification={verification['status']} | metrics={summary['metric_success_count']}/{len(sampler.samples)}")
    return directory
