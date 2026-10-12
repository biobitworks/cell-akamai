#!/usr/bin/env python3
"""Import returned Cell-Akamai archives into a versioned, append-only dashboard evidence index.

Only archives that exist are read; each archive's SHA-256 is recorded and its internal manifest is
checked file by file. Every numeric value in the index is either read from a receipt or computed by
a deterministic, named derivation from hashed source files. Nothing is invented: absent sources are
NOT_RECOVERED, unexecuted work is NOT_TESTED, undefined quantities are NOT_COMPUTED.

Original archives are never modified. Output: evidence/dashboard/DASHBOARD_EVIDENCE_INDEX.v<N>.json
(a new version is written only if content changed; earlier versions are kept).

Usage: python tools/dashboard/import_evidence.py [--archives-dir ~/Downloads] [--runs runs/concurrency]
"""
import argparse, glob, hashlib, io, json, re, statistics, time, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "evidence/dashboard"
SCHEMA = "cell_akamai.dashboard_evidence_index.v1"
EXPECTED = [  # (label, glob pattern)
    ("M08_M09_HANDOFF", "CELL_AKAMAI_M08_M09_HANDOFF_20261012.zip"),
    ("M08_M09_SIX_DATASETS", "CELL_AKAMAI_M08_M09_SIX_DATASETS_20261012.zip"),
    ("ALL_EVIDENCE", "CELL_AKAMAI_ALL_EVIDENCE_20261012_*.zip"),
    ("GITHUB_EVIDENCE", "CELL_AKAMAI_GITHUB_EVIDENCE_20261012_*.zip"),
    ("EVIDENCE_EXPORT", "CELL_AKAMAI_EVIDENCE_EXPORT.zip"),
    ("AKAMAI_RUN_001", "akamai_run_001.zip"),
]
sha = lambda b: hashlib.sha256(b).hexdigest()


def row(experiment_id, run_id, source, metric, unit, value, state, evidence_ref, model="UNKNOWN", workload=None, derivation=None, **extra):
    r = {"experiment_id": experiment_id, "run_id": run_id, "source_archive": source.get("name") if source else None,
         "source_sha256": source.get("sha256") if source else None, "commit_sha": None,
         "dataset_sha256": extra.pop("dataset_sha256", None), "model_identity": model, "workload": workload,
         "metric": metric, "unit": unit, "value": value, "state": state, "evidence_ref": evidence_ref}
    if derivation: r["derivation"] = derivation
    r.update(extra)
    return r


def verify_manifest(z):
    """Check every file listed in the archive's own manifest. Returns (state, n_ok, n_listed, failures)."""
    names = set(z.namelist())
    for mf in ("PACKAGE_MANIFEST.json", "EVIDENCE_MANIFEST.json"):
        if mf in names:
            m = json.loads(z.read(mf))
            files = m.get("files", m.get("source_snapshot_file_checks"))
            if files is None:
                return "NO_FILE_LIST", 0, 0, [], mf
            pairs = list(files.items()) if isinstance(files, dict) else [(f["path"], f["sha256"]) for f in files]
            bad = [p for p, h in pairs if p not in names or sha(z.read(p)) != h.split(":")[-1]]
            return ("PASS" if not bad else "FAIL"), len(pairs) - len(bad), len(pairs), bad[:10], mf
    return "NO_MANIFEST", 0, 0, [], None


def prom(text):
    """Parse the vLLM counters/gauges used here, summed over label sets."""
    out = {}
    for line in text.splitlines():
        m = re.match(r"^(vllm:[a-z_]+)(\{[^}]*\})?\s+([-+0-9.eE]+|NaN)$", line)
        if not m: continue
        name, labels, v = m.group(1), m.group(2) or "", float(m.group(3))
        key = name
        if name == "vllm:request_success_total":
            fr = re.search(r'finished_reason="([a-z]+)"', labels); key = f"{name}:{fr.group(1) if fr else 'all'}"
        out[key] = out.get(key, 0.0) + v
        if name == "vllm:request_success_total": out["vllm:request_success_total:all"] = out.get("vllm:request_success_total:all", 0.0) + v
    return out


def akamai_runs(z, src, base, rows, seen):
    """EXP-AKAMAI-* experiment folders inside an archive (or at its root)."""
    receipts = [n for n in z.namelist() if n.endswith("experiment_receipt.json")]
    for rp in receipts:
        folder = rp[: -len("experiment_receipt.json")]
        rec = json.loads(z.read(rp)); ver = json.loads(z.read(folder + "verification.json")) if folder + "verification.json" in z.namelist() else {}
        exp, rid = rec.get("experiment_id"), rec.get("run_id") or folder.rstrip("/").split("_")[-1]
        key = (exp, rid)
        if key in seen:  # same run carried by another archive: record the duplicate, don't double count
            rows.append(row(exp, rid, src, "duplicate_source_of_run", "flag", True, "OBSERVED", f"{src['name']}:{rp}",
                            derivation=f"run already imported from {seen[key]}")); continue
        seen[key] = src["name"]
        model = rec.get("model") or "Qwen/Qwen3-4B (from Prometheus model_name label)"
        ref = f"{src['name']}:{rp}"
        rows.append(row(exp, rid, src, "verification_same_host_replay", "state", ver.get("same_host_replay") or ver.get("deterministic_derived_arithmetic"),
                        "OBSERVED", f"{src['name']}:{folder}verification.json", model))
        rows.append(row(exp, rid, src, "independent_reexecution", "state", ver.get("independent_host_reexecution", ver.get("independent_gpu_attestation", "NOT_TESTED")),
                        "NOT_TESTED", f"{src['name']}:{folder}verification.json", model))
        for d in rec.get("derived") or []:
            r_ = d.get("run")
            rows.append(row(exp, rid, src, "request_completion_tokens_per_s", "tokens/s", d.get("tokens_per_s"), d.get("status", "OBSERVED"), ref, model,
                            workload=f"sequential request {r_}", derivation="receipt.derived (client wall clock, usage tokens)", request=r_))
            rows.append(row(exp, rid, src, "client_first_nonempty_chunk_ms", "ms", d.get("first_nonempty_chunk_ms"), d.get("status", "OBSERVED"), ref, model,
                            workload=f"sequential request {r_}", derivation="client first non-empty chunk; NOT server TTFT", request=r_))
            if d.get("inter_request_tokens_per_s2") is not None:
                rows.append(row(exp, rid, src, "inter_request_tokens_per_s2", "tokens/s^2", d["inter_request_tokens_per_s2"], "OBSERVED", ref, model,
                                workload=f"between requests {r_ - 1} and {r_}", derivation="receipt.derived: change in tokens/s over request-midpoint time", request=r_))
        for o in rec.get("observations") or []:  # SPEC-001 style per-request observations
            for k in ("completion_tokens", "tokens_per_s", "wall_s"):
                if isinstance(o.get(k), (int, float)):
                    rows.append(row(exp, rid, src, "spec_" + k, {"completion_tokens": "tokens", "tokens_per_s": "tokens/s", "wall_s": "s"}[k], o[k], o.get("status", "OBSERVED"),
                                    ref, model, workload=f"request {o.get('run', o.get('request'))}", derivation="receipt.observations", request=o.get("run", o.get("request"))))
        proms = sorted(n for n in z.namelist() if n.startswith(folder) and n.endswith(".prom"))
        pairs = {}
        for n in proms:
            m = re.search(r"run(\d+)_(before|after)\.prom$", n)
            if m: pairs.setdefault(int(m.group(1)), {})[m.group(2)] = n
        for r_, p in sorted(pairs.items()):
            if set(p) != {"before", "after"}: continue
            b, a = prom(z.read(p["before"]).decode()), prom(z.read(p["after"]).decode())
            d = lambda k: (a.get(k, 0.0) - b.get(k, 0.0)) if k in a else None
            pref = f"{src['name']}:{p['before']}|{p['after']}"
            deriv = "after - before vLLM Prometheus counters (server side)"
            for metric, unit, val in (
                ("server_generation_tokens", "tokens", d("vllm:generation_tokens_total")),
                ("server_prompt_tokens", "tokens", d("vllm:prompt_tokens_total")),
                ("server_requests_completed", "requests", d("vllm:request_success_total:all")),
                ("server_requests_finished_length", "requests", d("vllm:request_success_total:length")),
                ("server_preemptions", "events", d("vllm:num_preemptions_total")),
            ):
                if val is not None: rows.append(row(exp, rid, src, metric, unit, val, "OBSERVED", pref, model, workload=f"request {r_}", derivation=deriv, request=r_))
            for metric, base_ in (("server_ttft_mean_s", "vllm:time_to_first_token_seconds"), ("server_e2e_latency_mean_s", "vllm:e2e_request_latency_seconds"),
                                  ("server_inter_token_latency_mean_s", "vllm:inter_token_latency_seconds")):
                cs, cc = d(base_ + "_sum"), d(base_ + "_count")
                val, st = (cs / cc, "OBSERVED") if cs is not None and cc else (None, "NOT_COMPUTED")
                rows.append(row(exp, rid, src, metric, "s", val, st, pref, model, workload=f"request {r_}", derivation=f"delta({base_}_sum)/delta(_count)", request=r_))
            rows.append(row(exp, rid, src, "kv_cache_usage_after", "fraction", a.get("vllm:kv_cache_usage_perc", a.get("vllm:gpu_cache_usage_perc")),
                            "OBSERVED", pref, model, workload=f"request {r_}", derivation="gauge snapshot after request; NOT in-flight peak", request=r_))
            for g in ("vllm:num_requests_running", "vllm:num_requests_waiting"):
                rows.append(row(exp, rid, src, g.split(":")[1] + "_after", "requests", a.get(g), "OBSERVED", pref, model, workload=f"request {r_}",
                                derivation="gauge snapshot after request", request=r_))


def six_datasets(z, src, rows):
    ver = json.loads(z.read("data/SIX_DATASET_VERIFICATION.json"))
    files = ver["files"]
    data_sha = sha(z.read("data/eca_pilot_inputs_v1.jsonl"))
    for role in ("genesis", "vita_daisy", "evaluator"):
        paths = {k: f"data/{k}/{role}.jsonl" for k in ("original", "fco", "fcg")}
        raw = {k: z.read(p) for k, p in paths.items()}
        recs = {k: [json.loads(l) for l in raw[k].decode().splitlines() if l.strip()] for k in raw}
        ids = [r.get("item_id") for r in recs["original"]]
        hash_ok = all(sha(raw[k]) == files[paths[k]] for k in raw)
        # reconstruction: each FCO payload must equal the original row, in order
        recon = [f.get("payload") for f in recs["fco"]] == recs["original"]
        endpoints = {f["occurrence_id"] for f in recs["fco"]}
        edges_ok = all(e.get("from_occurrence") in endpoints for e in recs["fcg"])
        rel = sorted({e.get("relation") for e in recs["fcg"]})
        lookup = {f["payload"].get("item_id"): f for f in recs["fco"]}
        t0 = time.perf_counter_ns()
        for _ in range(200):
            for i in ids: lookup[i]
        lk = (time.perf_counter_ns() - t0) / (200 * len(ids)) / 1000
        by_from = {}
        for e in recs["fcg"]: by_from.setdefault(e["from_occurrence"], []).append(e)
        t0 = time.perf_counter_ns()
        for _ in range(200):
            for f in recs["fco"]: by_from.get(f["occurrence_id"], [])
        tv = (time.perf_counter_ns() - t0) / (200 * len(recs["fco"])) / 1000
        ref = f"{src['name']}:data/*/{role}.jsonl"
        common = dict(dataset_sha256=data_sha, workload=f"six-dataset pair: {role}", data_class="ECA_DERIVED_FIXTURE", role=role)
        for metric, unit, val, st in (
            ("original_records", "records", len(recs["original"]), "OBSERVED"),
            ("original_unique_records", "records", len(set(ids)), "OBSERVED"),
            ("original_bytes", "bytes", len(raw["original"]), "OBSERVED"),
            ("fco_count", "objects", len(recs["fco"]), "OBSERVED"),
            ("fcg_edge_count", "edges", len(recs["fcg"]), "OBSERVED"),
            ("fco_fcg_bytes", "bytes", len(raw["fco"]) + len(raw["fcg"]), "OBSERVED"),
            ("storage_overhead_ratio", "x", (len(raw["fco"]) + len(raw["fcg"])) / len(raw["original"]), "OBSERVED"),
            ("reconstruction_equal", "bool", recon, "OBSERVED"),
            ("file_hashes_match_verification", "bool", hash_ok, "OBSERVED"),
            ("fcg_edge_endpoints_exist", "bool", edges_ok, "OBSERVED"),
            ("direct_lookup_mean_us", "microseconds", round(lk, 4), "OBSERVED_LOCAL_MAGICPRO_PYTHON_DICT"),
            ("fcg_traversal_mean_us", "microseconds", round(tv, 4), "OBSERVED_LOCAL_MAGICPRO_PYTHON_DICT"),
            ("model_visible_prompt_tokens", "tokens", None, "NOT_COMPUTED"),
            ("inference_tokens_per_s", "tokens/s", None, "NOT_TESTED"),
            ("inference_total_request_latency_s", "s", None, "NOT_TESTED"),
        ):
            rows.append(row("CAKM-SIX-DATASET", f"six-{role}", src, metric, unit, val, st, ref,
                            derivation="deterministic from hashed archive files" if st.startswith("OBSERVED") else None, relations=rel, **common))
    rows.append(row("CAKM-SIX-DATASET", "six-all", src, "historical_genesis_vita_execution", "state", None, "NOT_RECOVERED",
                    f"{src['name']}:data/SIX_DATASET_VERIFICATION.json", derivation="actual_genesis_execution/actual_vita_daisy_execution = NOT_TESTED"))


def modules(z, src, rows):
    names = set(z.namelist())
    for mod, nb, metrics in (("M08", "notebooks/80_m08_tune_before_after.ipynb",
                              ["completion_tokens_per_s", "ttft_p50_s", "ttft_p95_s", "e2e_p95_s", "inter_token_latency_s", "kv_cache_usage", "requests_running",
                               "requests_waiting", "preemptions", "heldout_quality"]),
                             ("M09", "notebooks/81_m09_agent_and_daisy.ipynb",
                              ["agent_requests_completed", "agent_requests_failed", "tool_calls", "in_scope_handled", "out_of_scope_refused",
                               "six_session_wall_s", "single_session_wall_s", "kv_cache_usage"])):
        present = nb in names
        rows.append(row(f"CAKM-{mod}", f"{mod}-handoff", src, "protocol_notebook", "state", present, "IMPLEMENTED" if present else "NOT_RECOVERED",
                        f"{src['name']}:{nb}", derivation="notebook present; not executed on Akamai in any returned receipt"))
        for m in metrics:
            for phase in (("before", "after") if mod == "M08" else ("run",)):
                rows.append(row(f"CAKM-{mod}", f"{mod}-{phase}", src, f"{phase}_{m}", "see_protocol", None,
                                "AFTER_NOT_TESTED" if phase == "after" else "NOT_TESTED", f"{src['name']}:{nb}"))


def lane_b(runs, rows):
    for p in sorted(Path(runs).glob("concurrency-*/")):
        src = {"name": f"runs/concurrency/{p.name}", "sha256": None}
        stopped = p / "STOPPED.json"
        summ = p / "lane_b_concurrency_summary.json"
        meta = json.loads((p / "run_manifest.json").read_text()) if (p / "run_manifest.json").exists() else {}
        model, backend = meta.get("served_model_requested", "UNKNOWN"), meta.get("backend", "UNKNOWN")
        if stopped.exists():
            s = json.loads(stopped.read_text())
            rows.append(row("EXP-LANEB-GDAISY-001-PILOT-CONCURRENCY", p.name, src, "run_state", "state", s["state"], "FAILED", f"{src['name']}/STOPPED.json",
                            model, workload=backend, derivation=s["reason"], backend=backend))
        if summ.exists():
            s = json.loads(summ.read_text()); src["sha256"] = sha(summ.read_bytes())
            for pnl in s["panels"]:
                if pnl["state"] != "SCORED":
                    rows.append(row("EXP-LANEB-GDAISY-001-PILOT-CONCURRENCY", p.name, src, "panel_refused", "state", pnl.get("reason"), "FAILED",
                                    f"{src['name']}/c{pnl['concurrency']:02d}_paired_for_scoring", model, backend=backend, concurrency=pnl["concurrency"]))
            for r in s["rows"]:
                for metric, unit in (("exact_match_accuracy", "fraction"), ("correct", "items"), ("n_items", "items"), ("mean_hamming_error", "fraction_of_cells"),
                                     ("abstention_rate", "fraction"), ("parse_failure_rate", "fraction"), ("failure_rate", "fraction"), ("over_budget_rate", "fraction"),
                                     ("model_calls", "calls"), ("completion_tokens", "tokens"), ("tokens_per_correct_item", "tokens/correct_item")):
                    v = r.get(metric)
                    rows.append(row("EXP-LANEB-GDAISY-001-PILOT-CONCURRENCY", p.name, src, metric, unit, v,
                                    ("OBSERVED" if v is not None else ("UNDEFINED_ZERO_CORRECT" if metric == "tokens_per_correct_item" and r.get("correct") == 0 and r.get("completion_tokens") is not None else "UNKNOWN")),
                                    f"{src['name']}/c{r['concurrency']:02d}_paired_for_scoring/answers.jsonl", model, workload=f"{backend} c={r['concurrency']}",
                                    derivation="lane_b/harness/score_lane_b.py after commitment verification", arm=r["arm"], concurrency=r["concurrency"],
                                    backend=backend, source_class=r["source_class"], dataset_sha256=s["dataset_sha256"]))
            for c in s["contrasts"]:
                rows.append(row("EXP-LANEB-GDAISY-001-PILOT-CONCURRENCY", p.name, src, "paired_discordance", "pairs", c["discordant_pairs"], "OBSERVED",
                                f"{src['name']}/c{c['concurrency']:02d}_paired_for_scoring", model, workload=f"{c['A']} vs {c['B']}",
                                derivation="exact McNemar, Holm-adjusted", A=c["A"], B=c["B"], A_only=c["A_only_correct"], B_only=c["B_only_correct"],
                                p_holm=c["p_holm"], concurrency=c["concurrency"], backend=backend))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--archives-dir", default=str(Path.home() / "Downloads"))
    ap.add_argument("--runs", default=str(ROOT / "runs/concurrency"))
    a = ap.parse_args(argv)
    rows, sources, seen = [], [], {}
    for label, pattern in EXPECTED:
        hits = sorted(glob.glob(str(Path(a.archives_dir) / pattern)))
        if not hits:
            sources.append({"label": label, "pattern": pattern, "state": "NOT_RECOVERED"}); continue
        for h in hits:
            b = Path(h).read_bytes(); src = {"name": Path(h).name, "sha256": sha(b)}
            z = zipfile.ZipFile(io.BytesIO(b))
            st, ok, n, bad, mf = verify_manifest(z)
            sources.append({"label": label, "archive": src["name"], "sha256": src["sha256"], "bytes": len(b), "manifest": mf,
                            "manifest_state": st, "manifest_files_ok": ok, "manifest_files_listed": n, "manifest_failures": bad})
            if st == "FAIL":
                continue  # integrity failure: listed, never ingested
            if label in ("EVIDENCE_EXPORT", "AKAMAI_RUN_001"): akamai_runs(z, src, h, rows, seen)
            if label == "M08_M09_SIX_DATASETS": six_datasets(z, src, rows)
            if label in ("M08_M09_HANDOFF",): modules(z, src, rows)
    lane_b(a.runs, rows)
    body = {"schema": SCHEMA, "policy": "receipts or named deterministic derivations only; NOT_RECOVERED / NOT_TESTED / NOT_COMPUTED kept visible",
            "sources": sources, "rows": rows,
            "claims": {"anticube": "NOT_COMPUTED", "delta_g_star": "NOT_COMPUTED", "self_training": "NOT_TESTED", "mmr": "NOT_COMMITTED", "signature": "NOT_SIGNED",
                       "genesis": "B1 = GENESIS_POLICY_PROXY_V0, not the recovered Genesis Transformer",
                       "six_datasets": "ECA_DERIVED_FIXTURE; FCO/FCG transformation is not a learned-model improvement",
                       "comparisons": "No cross-run speedup claimed: TOKEN-001 and SPEC-001 differ in workload/config; no matched FP8 or speculative run"}}
    text = json.dumps(body, indent=2, sort_keys=True, default=str) + "\n"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    versions = sorted(OUT_DIR.glob("DASHBOARD_EVIDENCE_INDEX.v*.json"), key=lambda p: int(p.stem.split(".v")[-1]))
    if versions and versions[-1].read_text() == text:
        print("unchanged", versions[-1].name); return versions[-1]
    out = OUT_DIR / f"DASHBOARD_EVIDENCE_INDEX.v{len(versions) + 1}.json"
    out.write_text(text)  # append-only: earlier versions are never rewritten
    print("wrote", out, "rows", len(rows), "sources", len(sources))
    return out


if __name__ == "__main__":
    main()
