"""Shared helpers for Cell-Akamai companion notebooks (modules 01, 02, 03, 07) on a local Ollama server.

Everything here is a CLIENT of Ollama. Server-reported counts/durations come from Ollama's own response fields.
These are NOT vLLM metrics and NOT Akamai GPU measurements; results must never be pooled with Akamai runs.
"""
import hashlib, json, math, platform, subprocess, threading, time
from pathlib import Path
import requests

OLLAMA = "http://127.0.0.1:11434"


def sha256_hex(b: bytes) -> str:
    return "sha256:" + hashlib.sha256(b).hexdigest()


def percentile(values, q):
    """Nearest-rank percentile, q in (0,100]. None if empty. Defined explicitly so replays agree."""
    v = sorted(x for x in values if x is not None)
    if not v:
        return None
    k = max(1, math.ceil(q / 100 * len(v)))
    return v[k - 1]


def _sysctl(key):
    try:
        return subprocess.run(["sysctl", "-n", key], capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        return "UNKNOWN"


def host_info(base=OLLAMA):
    v = requests.get(base + "/api/version", timeout=10).json().get("version", "UNKNOWN")
    return {"host": platform.node(), "platform": platform.platform(), "chip": _sysctl("machdep.cpu.brand_string"),
            "memory_bytes": int(_sysctl("hw.memsize") or 0), "ollama_version": v, "backend": "ollama",
            "gpu_hardware": "Apple silicon unified memory (NOT an Akamai NVIDIA GPU)", "source_class": "OBSERVED_LOCAL_NOT_AKAMAI"}


def model_meta(model, base=OLLAMA):
    tags = {m["name"]: m for m in requests.get(base + "/api/tags", timeout=10).json()["models"]}
    show = requests.post(base + "/api/show", json={"model": model}, timeout=30).json()
    t = tags.get(model, {})
    return {"model": model, "digest": t.get("digest", "UNKNOWN"), "file_bytes": t.get("size"),
            "parameter_size": show.get("details", {}).get("parameter_size"), "quantization": show.get("details", {}).get("quantization_level"),
            "model_info": show.get("model_info", {})}


def kv_bytes_per_token(model_info, dtype_bytes=2):
    """Exact KV bytes/token from GGUF metadata, or None when metadata cannot support it (hybrid/array layouts).

    Standard attention only: 2 (K and V) * layers * kv_heads * head_dim * dtype_bytes. dtype 2 = f16 (ASSUMED Ollama default).
    """
    arch = model_info.get("general.architecture")
    g = lambda k: model_info.get(f"{arch}.{k}")
    layers, kv, heads, emb = g("block_count"), g("attention.head_count_kv"), g("attention.head_count"), g("embedding_length")
    hd = g("attention.key_length") or (emb // heads if emb and heads and not isinstance(heads, list) else None)
    if not all(isinstance(x, int) for x in (layers, kv, hd)):
        return None
    return 2 * layers * kv * hd * dtype_bytes


def generate_stream(model, prompt, num_predict=64, base=OLLAMA, keep_alive="10m", seed=1, options=None):
    """One streamed /api/generate call. Client timings via monotonic clock; counts/durations are Ollama-reported (never chunk-derived)."""
    body = {"model": model, "prompt": prompt, "stream": True, "keep_alive": keep_alive,
            "options": {"temperature": 0, "seed": seed, "num_predict": num_predict, **(options or {})}}
    rec = {"model": model, "prompt_sha256": sha256_hex(prompt.encode()), "status": "NOT_TESTED", "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    t0 = time.monotonic_ns(); first = None; parts = []; chunks = 0; final = {}
    try:
        with requests.post(base + "/api/generate", json=body, stream=True, timeout=600) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if not line:
                    continue
                j = json.loads(line)
                if j.get("response"):
                    chunks += 1; parts.append(j["response"])
                    if first is None:
                        first = time.monotonic_ns()
                if j.get("done"):
                    final = j
        end = time.monotonic_ns()
        rec.update(status="OBSERVED", ttfc_s=None if first is None else (first - t0) / 1e9, wall_s=(end - t0) / 1e9, stream_chunks=chunks,
                   prompt_eval_count=final.get("prompt_eval_count"), prompt_eval_duration_s=(final.get("prompt_eval_duration") or 0) / 1e9 or None,
                   eval_count=final.get("eval_count"), eval_duration_s=(final.get("eval_duration") or 0) / 1e9 or None,
                   load_duration_s=(final.get("load_duration") or 0) / 1e9, response_sha256=sha256_hex("".join(parts).encode()))
    except Exception as e:  # failures are retained, exception text is not (may contain URLs)
        rec.update(status="FAILED", failure_type=type(e).__name__, wall_s=(time.monotonic_ns() - t0) / 1e9)
    return rec


def run_concurrent(fn, n_requests, concurrency):
    """Run fn(i) for i in range(n_requests) with a fixed worker pool; returns (results, batch_wall_s)."""
    results = [None] * n_requests; idx = iter(range(n_requests)); lock = threading.Lock()

    def worker():
        while True:
            with lock:
                i = next(idx, None)
            if i is None:
                return
            results[i] = fn(i)
    ts = [threading.Thread(target=worker) for _ in range(concurrency)]
    t0 = time.monotonic()
    [t.start() for t in ts]; [t.join() for t in ts]
    return results, time.monotonic() - t0


def write_receipt(out_dir, name, rows, meta):
    """Write rows as JSONL plus a receipt binding file hash, host, and honest status. No MMR, unsigned."""
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    data = b"".join(json.dumps(r, sort_keys=True).encode() + b"\n" for r in rows)
    (out / f"{name}.jsonl").write_bytes(data)
    receipt = {"name": name, "rows": len(rows), "jsonl_sha256": sha256_hex(data), **meta,
               "independent_reexecution": "NOT_TESTED", "mmr": "NOT_COMMITTED", "signed": False}
    (out / f"{name}.receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True))
    return receipt
