#!/usr/bin/env python3
"""Score every cXX_paired_for_scoring panel of a run_concurrency.py run folder, then write a sanitized summary.

Each panel is scored only after its answers.jsonl commitment verifies (score_lane_b.verify):
answers, config and frozen-dataset digests, frozen-record identity and complete 4-arm x item
coverage. A refused panel is retained as a REFUSED row with its reason; it is never dropped.

Writes RUN_FOLDER/lane_b_concurrency_summary.json: aggregates only (no answer text, prompts,
credentials or hostnames), one row per (concurrency, arm) plus paired contrasts per level.

Usage: score_concurrency.py RUN_FOLDER --config CONFIG.json --dataset D.jsonl --manifest M.json
"""
import argparse, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import score_lane_b as S  # noqa: E402

AKAMAI_STAGES = ("bf16_reference", "fp8", "speculative", "tuned")


def family(backend, stage):
    if backend == "AKAMAI_VLLM":
        return "AKAMAI_" + (stage.upper() if stage in AKAMAI_STAGES else "OTHER_STAGE")
    return backend  # MAGICSTUDIO_OLLAMA / MAGICPRO_OLLAMA / SYNTHETIC_FIXTURE stay separate


def summarize(folder, config, dataset, manifest):
    folder = Path(folder)
    meta = json.loads((folder / "run_manifest.json").read_text())
    bench = {}
    if (folder / "bench_cells.json").exists():
        for r in json.loads((folder / "bench_cells.json").read_text()).get("rows", []):
            bench[(r["concurrency"], r["arm"])] = r
    found = {int(p.name[1:3]) for p in folder.glob("c*_paired_for_scoring") if re.fullmatch(r"c\d{2}_paired_for_scoring", p.name)}
    scheduled = {int(c) for c in meta.get("concurrency", [])}
    rows, contrasts, panel_states = [], [], []
    for c in sorted(found | scheduled):
        p = folder / f"c{c:02d}_paired_for_scoring"
        if not p.is_dir():  # scheduled in the run manifest but never reached commitment (interrupted/failed run)
            panel_states.append({"concurrency": c, "state": "REFUSED", "reason": "PANEL NEVER COMMITTED (scheduled, absent)"}); continue
        if not (p / "COMMIT.json").exists():
            panel_states.append({"concurrency": c, "state": "REFUSED", "reason": "NO ANSWER COMMITMENT"}); continue
        try:
            commit, items, recs, checks = S.verify(config, p, dataset, manifest)
        except S.Refusal as e:
            (p / "score_refusal.json").write_text(json.dumps({"state": "REFUSED", "reason": str(e), "scored": False}, indent=2) + "\n")
            panel_states.append({"concurrency": c, "state": "REFUSED", "reason": str(e)}); continue
        per_arm, cons = S.score(items, recs)
        source = "SYNTHETIC_FIXTURE" if commit.get("source_class") == "SYNTHETIC_FIXTURE" else "OBSERVED"
        panel_states.append({"concurrency": c, "state": "SCORED", "answers_sha256": S.bare(commit["answers_sha256"]),
                             "source_class": source, "checks": {k: v for k, v in checks.items() if isinstance(v, bool)}})
        for arm, m in per_arm.items():
            b = bench.get((c, arm), {})
            rows.append({"concurrency": c, "arm": arm, "source_class": source,
                         **{k: m[k] for k in ("n_items", "correct", "exact_match_accuracy", "mean_hamming_error", "abstention_rate",
                                              "parse_failure_rate", "failure_rate", "over_budget_rate", "model_calls", "model_calls_per_item",
                                              "completion_tokens", "tokens_per_correct_item", "tokens_per_correct_item_denominator")},
                         "aggregate_completion_tokens_per_s": b.get("aggregate_completion_tokens_per_s"),
                         "latency_p95_ms": b.get("latency_p95_ms")})
        contrasts += [{"concurrency": c, **x} for x in cons]
    out = {"schema": "cell_akamai.lane_b_concurrency_summary.v1", "run_id": meta.get("run_id"), "module": meta.get("module"),
           "backend": meta.get("backend"), "stage": meta.get("stage"), "backend_family": family(meta.get("backend"), meta.get("stage")),
           "served_model_requested": meta.get("served_model_requested"), "model_revision": meta.get("model_revision", "UNKNOWN"),
           "precision_verified": meta.get("precision_verified", "UNKNOWN"), "run_state": meta.get("state"),
           "dataset_sha256": S.bare(json.loads(Path(manifest).read_text())["sha256"]),
           "split": "PILOT_NONCONFIRMATORY", "panels": panel_states, "rows": rows, "contrasts": contrasts,
           "arm_fairness": S.FAIRNESS, "arm_notes": S.ARM_NOTES,
           "anticube": "NOT_COMPUTED", "delta_g_star": "NOT_COMPUTED", "self_training": "NOT_TESTED (no weight updates)",
           "genesis": "B1 is GENESIS_POLICY_PROXY_V0, not the recovered Genesis policy", "signature": "NOT_SIGNED"}
    (folder / "lane_b_concurrency_summary.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    return out


def cli(argv=None):
    ap = argparse.ArgumentParser(description="Score concurrency panels after answer commitment")
    ap.add_argument("run_folder"); ap.add_argument("--config", required=True)
    ap.add_argument("--dataset", required=True); ap.add_argument("--manifest", required=True)
    a = ap.parse_args(argv)
    out = summarize(a.run_folder, a.config, a.dataset, a.manifest)
    for p in out["panels"]:
        print(f"c={p['concurrency']:>2} {p['state']}" + (f" {p.get('reason')}" if p["state"] != "SCORED" else f" {p['source_class']}"))
    for r in out["rows"]:
        print(f"c={r['concurrency']:>2} {r['arm']:<18} acc={r['exact_match_accuracy']:.3f} ham={r['mean_hamming_error']:.3f} "
              f"abst={r['abstention_rate']:.3f} calls={r['model_calls']} tok/correct={r['tokens_per_correct_item']}")
    for c in out["contrasts"]:
        print(f"c={c['concurrency']:>2} {c['A']} vs {c['B']}: A-only={c['A_only_correct']} B-only={c['B_only_correct']} p_holm={c['p_holm']:.3f}")
    return 0 if all(p["state"] == "SCORED" for p in out["panels"]) and out["panels"] else 1


if __name__ == "__main__":
    sys.exit(cli())
