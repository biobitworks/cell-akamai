#!/usr/bin/env python3
"""Bounded, append-only concurrency adapter for Claude Lane B run_item.

No independent oracle in this process. Never claims self-training or inference
improvement; evaluation must be run *after* answers are content-committed.
Requires source branch PR #5 for lane_b/harness/run_lane_b.py.
"""
from __future__ import annotations
import argparse
import concurrent.futures as cf
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import re
import statistics
import sys
import time
import uuid
from datetime import datetime, timezone
from urllib.parse import urlsplit

ARMS = ("B0_FIXED", "B1_GENESIS", "B2_GENESIS_DAISY", "B3_RANDOM_CONTROL")
DECLARED_CALLS = {"B0_FIXED": 1, "B1_GENESIS": 3, "B2_GENESIS_DAISY": 3, "B3_RANDOM_CONTROL": 3}


def sha(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def parse_items(raw: bytes, limit: int):
    values = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if not values or limit < 1 or limit > len(values):
        raise ValueError("Invalid number of dataset items")
    seen = set()
    for item in values:
        if set(("item_id", "rule", "seed", "width", "initial_state")) - set(item):
            raise ValueError("Missing dataset fields")
        if item["item_id"] in seen or item["rule"] not in (30, 90, 110, 184) or item["width"] != 8:
            raise ValueError("Invalid/duplicate ECA item")
        if item["seed"] in (41031, 41032, 41033, 41034):
            raise ValueError("Calibration seed in scored input")
        if len(item["initial_state"]) != 8 or any(type(b) is not int or b not in (0, 1) for b in item["initial_state"]):
            raise ValueError("Invalid ECA state")
        seen.add(item["item_id"])
    # Round-robin one item per rule before increasing replication depth.
    selected = []
    buckets = {rule: [r for r in values if r["rule"] == rule] for rule in (30, 90, 110, 184)}
    while len(selected) < limit:
        for rule in buckets:
            if len(selected) < limit and buckets[rule]:
                selected.append(buckets[rule].pop(0))
        if all(not bucket for bucket in buckets.values()) and len(selected) < limit:
            raise ValueError("Insufficient balanced items")
    return selected


def pct(seq, q):
    if not seq:
        return None
    s = sorted(seq)
    return s[min(len(s) - 1, max(0, int(q * (len(s) - 1))))]


def summarize(rows, arm, concurrency, elapsed_s):
    token_counts = [r.get("tokens_total") for r in rows]
    call_counts = [r.get("n_calls", 0) for r in rows]
    all_known = all(type(n) is int and n >= 0 for n in token_counts)
    durations = [r.get("item_elapsed_s") for r in rows if isinstance(r.get("item_elapsed_s"), (int, float))]
    failed = sum(bool(r.get("failure") or r.get("over_budget") or not r.get("final_answer") or r.get("final_answer") == "ABSTAIN") for r in rows)
    return {"arm": arm, "concurrency": concurrency, "items": len(rows), "successful_parsed_within_budget": len(rows) - failed,
            "failed_or_abstained_or_over_budget": failed, "model_calls_observed": sum(call_counts),
            "model_calls_declared_upper_bound": len(rows) * DECLARED_CALLS[arm],
            "aggregate_completion_tokens": sum(token_counts) if all_known else None,
            "aggregate_completion_tokens_per_s": (sum(token_counts) / elapsed_s) if all_known and elapsed_s > 0 else None,
            "token_count_status": "OBSERVED_USAGE" if all_known else "UNKNOWN",
            "items_per_s": len(rows) / elapsed_s if elapsed_s > 0 else None,
            "latency_p50_ms": pct(durations, 0.50) * 1000 if durations else None,
            "latency_p95_ms": pct(durations, 0.95) * 1000 if durations else None,
            "batch_wall_s": elapsed_s,
            "inter_request_tokens_per_s2": None,
            "inter_request_tokens_per_s2_reason": "concurrent per-item calls cannot define sequential request-midpoint derivatives; use Lane A per-request collector"}


def load_claude(harness_path: Path):
    harness_path = harness_path.resolve()
    if not harness_path.is_file():
        raise FileNotFoundError(f"Claude harness required: {harness_path}")
    sys.path.insert(0, str(harness_path.parent))
    spec = importlib.util.spec_from_file_location("cell_akamai_claude_run_lane_b", harness_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "run_item") or not hasattr(module, "make_chat"):
        raise ValueError("Claude harness missing run_item/make_chat")
    return module


def run_batch(items, concurrency, arm, claude, chat, config, seed):
    shuffled = list(items)
    random.Random(f"{seed}:{arm}:{concurrency}").shuffle(shuffled)
    def task(it):
        started = time.perf_counter_ns()
        try:
            result = claude.run_item(arm, it, chat, config)
        except Exception as exc:
            result = {"item_id": it["item_id"], "arm": arm, "calls": [], "final_answer": None,
                      "failure": type(exc).__name__, "tokens_total": None, "wall_s_total": 0.0, "n_calls": 0, "over_budget": False}
        result["item_elapsed_s"] = (time.perf_counter_ns() - started) / 1e9
        return result
    begin = time.perf_counter_ns()
    with cf.ThreadPoolExecutor(max_workers=concurrency) as pool:
        results = list(pool.map(task, shuffled))
    elapsed = (time.perf_counter_ns() - begin) / 1e9
    results.sort(key=lambda row: row["item_id"])
    return results, summarize(results, arm, concurrency, elapsed)


def main(argv=None, injected_chat=None):
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", required=True)
    p.add_argument("--manifest", required=True)
    p.add_argument("--config", required=True)
    p.add_argument("--harness", default="lane_b/harness/run_lane_b.py")
    p.add_argument("--module-id", choices=["01", "03", "05", "06", "07", "08", "09"], default="07")
    p.add_argument("--stage", default="bf16_reference")
    p.add_argument("--backend", choices=["AKAMAI_VLLM", "MAGICSTUDIO_OLLAMA", "MAGICPRO_OLLAMA", "SYNTHETIC_FIXTURE"], default="AKAMAI_VLLM")
    p.add_argument("--concurrency", type=int, nargs="+", default=[1, 2, 4, 8])
    p.add_argument("--limit-items", type=int, default=8)
    p.add_argument("--output-root", default="runs/concurrency")
    p.add_argument("--execute", action="store_true")
    p.add_argument("--max-total-calls", type=int, default=500)
    args = p.parse_args(argv)
    if len(args.concurrency) != len(set(args.concurrency)) or any(n < 1 or n > 32 for n in args.concurrency):
        raise ValueError("Concurrency must be unique and within 1–32")
    if not re.fullmatch(r"[a-zA-Z0-9_\-]{1,64}", args.stage):
        raise ValueError("Unsafe stage name")
    config_bytes = Path(args.config).read_bytes()
    config = json.loads(config_bytes)
    dataset_bytes = Path(args.dataset).read_bytes()
    manifest = json.loads(Path(args.manifest).read_text())
    if sha(dataset_bytes) != manifest["sha256"]:
        raise ValueError("Dataset SHA-256 mismatch")
    items = parse_items(dataset_bytes, args.limit_items)
    expected_calls = len(items) * sum(DECLARED_CALLS.values()) * len(args.concurrency)
    if expected_calls > args.max_total_calls:
        raise ValueError(f"Projected {expected_calls} calls exceeds --max-total-calls={args.max_total_calls}")
    plan = {"state": "PROPOSED" if not args.execute else "EXECUTED_LOCALLY_FROM_CONFIG", "module": args.module_id,
            "backend": args.backend, "stage": args.stage, "concurrency": args.concurrency, "items_per_arm": len(items),
            "declared_max_model_calls": expected_calls, "dataset_sha256": sha(dataset_bytes),
            "config_sha256": sha(config_bytes), "oracle_access": "NONE", "source_class": "SYNTHETIC_FIXTURE" if args.backend == "SYNTHETIC_FIXTURE" else "OBSERVED_IF_ENDPOINT_SUCCESS"}
    if not args.execute:
        print(json.dumps(plan, indent=2))
        return plan
    if args.backend == "SYNTHETIC_FIXTURE" and injected_chat is None:
        raise ValueError("Fixtures require explicit injected fake chat")
    if args.backend != "SYNTHETIC_FIXTURE":
        url = urlsplit(config.get("base_url", ""))
        if url.scheme not in ("http", "https") or not url.hostname or not config.get("model") or "SET_ME" in config["model"]:
            raise ValueError("Missing usable endpoint/model identity")
    claude = load_claude(Path(args.harness))
    runtime_cfg = dict(config)
    runtime_cfg["api_key_env_value"] = os.environ.get(config.get("api_key_env", "VLLM_API_KEY"), "none")
    chat = injected_chat or claude.make_chat(runtime_cfg)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rid = "concurrency-" + args.module_id + "-" + args.stage + "-" + stamp + "-" + uuid.uuid4().hex[:8]
    folder = Path(args.output_root) / rid
    folder.mkdir(parents=True, exist_ok=False)
    folder.chmod(0o700)
    # Source config saved by digest and sanitized subset only. Inference replies remain in ignored runs/.
    meta = {**plan, "state": "IN_PROGRESS", "run_id": rid, "host": os.uname().nodename,
            "served_model_requested": config.get("model", "UNKNOWN"), "model_revision": "UNKNOWN",
            "precision_verified": "UNKNOWN", "deployment_args_sha": "UNKNOWN",
            "source_claude_harness_sha256": sha(Path(args.harness).read_bytes()),
            "workshop_baseline_sha": "454b43269216c1f92dd8d7e2711649e38cb888cb",
            "preregistration": "PILOT_NONCONFIRMATORY", "self_training": "NOT_TESTED",
            "anticube": "NOT_COMPUTED", "delta_g_star": "NOT_COMPUTED", "mmr": "NOT_COMMITTED",
            "signature": "NOT_SIGNED", "independent_host_verification": "NOT_TESTED"}
    write_json(folder / "run_manifest.json", meta)
    observed = []
    try:
        for c in args.concurrency:
            # Each concurrency level is one complete paired panel for Claude scorer.
            c_recs = []
            # Different warmup/load could affect order, which is recorded.
            for arm in ARMS:
                cell = folder / f"c{c:02d}_{arm}"
                cell.mkdir()
                recs, stats = run_batch(items, c, arm, claude, chat, runtime_cfg, config.get("decode_seed", 0))
                (cell / "answers.jsonl").write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in recs))
                (cell / "items.jsonl").write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in items))
                ans_hash = hashlib.sha256((cell / "answers.jsonl").read_bytes()).hexdigest()
                write_json(cell / "COMMIT.json", {"answers_sha256": ans_hash, "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
                    "genesis_policy": getattr(claude, "GENESIS_POLICY", "UNKNOWN"), "oracle_accessed": False,
                    "dataset_sha256": sha(dataset_bytes), "run_id": rid, "source_class": "SYNTHETIC_FIXTURE" if injected_chat else "OBSERVED"})
                write_json(cell / "bench_summary.json", stats)
                observed.append({"cell": cell.name, "answers_sha256": "sha256:" + ans_hash, **stats})
                write_json(folder / "bench_cells.json", {"run_id": rid, "rows": observed, "status": "IN_PROGRESS" if not injected_chat else "SYNTHETIC_FIXTURE"})
                c_recs.extend(recs)
                print(f"{cell.name} items={len(recs)} calls={stats['model_calls_observed']} tokens={stats['aggregate_completion_tokens']} throughput={stats['aggregate_completion_tokens_per_s']}", flush=True)
            paired = folder / f"c{c:02d}_paired_for_scoring"
            paired.mkdir()
            (paired / "answers.jsonl").write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in c_recs))
            (paired / "items.jsonl").write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in items))
            answers_digest = hashlib.sha256((paired / "answers.jsonl").read_bytes()).hexdigest()
            write_json(paired / "COMMIT.json", {"answers_sha256": answers_digest, "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
                "genesis_policy": getattr(claude, "GENESIS_POLICY", "UNKNOWN"), "oracle_accessed": False, "dataset_sha256": sha(dataset_bytes),
                "run_id": rid, "source_class": "SYNTHETIC_FIXTURE" if injected_chat else "OBSERVED"})
        write_json(folder / "bench_cells.json", {"run_id": rid, "rows": observed, "status": "OBSERVED" if not injected_chat else "SYNTHETIC_FIXTURE"})
        meta["state"] = "COMPLETED_WITH_RESULT_OR_FAILURE_ROWS"
    except BaseException as exc:
        meta["state"] = "FAILED"
        meta["failure_type"] = type(exc).__name__
        raise
    finally:
        write_json(folder / "run_manifest.json", meta)
    print("RUN_FOLDER", folder)
    return folder


if __name__ == "__main__":
    main()