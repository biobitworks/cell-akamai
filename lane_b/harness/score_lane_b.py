#!/usr/bin/env python3
"""Independent scorer: verifies the answer commit, recomputes the ECA oracle on its own, writes exchange rows + analysis.

Usage: score_lane_b.py CONFIG.json RUN_DIR [--source-class OBSERVED|SYNTHETIC_FIXTURE]
Oracle is re-implemented here deliberately; it is not imported from the runner.
"""
import hashlib, json, sys
from math import comb
from pathlib import Path

ARMS = ["B0_FIXED", "B1_GENESIS", "B2_GENESIS_DAISY", "B3_RANDOM_CONTROL"]


def oracle(it):  # periodic boundary, Wolfram encoding L*4+C*2+R (matches recovered RUN001 independent_oracle)
    b, r, n = it["initial_state"], it["rule"], len(it["initial_state"])
    return "".join(str((r >> ((b[(i - 1) % n] << 2) | (b[i] << 1) | b[(i + 1) % n])) & 1) for i in range(n))


def mcnemar_exact(b, c):  # b: A right/B wrong, c: A wrong/B right; two-sided exact
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i]); adj = [0.0] * len(ps); run = 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - rank) * ps[i])); adj[i] = run
    return adj


def main(cfg_path, run_dir, source_class="OBSERVED"):
    cfg = json.loads(Path(cfg_path).read_text()); run = Path(run_dir)
    commit = json.loads((run / "COMMIT.json").read_text())
    if hashlib.sha256((run / "answers.jsonl").read_bytes()).hexdigest() != commit["answers_sha256"]:
        sys.exit("ANSWER COMMIT MISMATCH: refusing to score")
    items = {i["item_id"]: i for i in map(json.loads, (run / "items.jsonl").read_text().splitlines())}
    recs = [json.loads(l) for l in (run / "answers.jsonl").read_text().splitlines()]
    pilot = cfg.get("mode") != "CONFIRMATORY_FROZEN"
    split = "PILOT_NONCONFIRMATORY" if pilot else "HELDOUT_FROZEN"
    correct = {a: {} for a in ARMS}; stats = {a: dict(ham=0.0, abst=0, parse=0, tok=0, tok_unknown=0, wall=0.0, n=0, fail=0) for a in ARMS}
    for r in recs:
        it = items[r["item_id"]]; truth = oracle(it); fa = r["final_answer"]; s = stats[r["arm"]]; s["n"] += 1
        s["wall"] += r["wall_s_total"]; s["fail"] += 1 if r.get("failure") else 0
        if r["tokens_total"] is None: s["tok_unknown"] += 1
        else: s["tok"] += r["tokens_total"]
        if fa == "ABSTAIN": s["abst"] += 1
        if fa is None: s["parse"] += 1
        ok = fa == truth and not r["over_budget"]  # parse failure, abstention, over-budget all count as incorrect
        correct[r["arm"]][r["item_id"]] = ok
        s["ham"] += (sum(x != y for x, y in zip(fa, truth)) / len(truth)) if fa and fa != "ABSTAIN" else 1.0
    pairs = [("B2_GENESIS_DAISY", "B3_RANDOM_CONTROL"), ("B1_GENESIS", "B0_FIXED"), ("B2_GENESIS_DAISY", "B1_GENESIS")]
    res = []
    for a, b in pairs:
        ids = sorted(correct[a]); x = sum(correct[a][i] and not correct[b][i] for i in ids); y = sum(correct[b][i] and not correct[a][i] for i in ids)
        res.append({"A": a, "B": b, "A_only_correct": x, "B_only_correct": y, "p_exact_mcnemar": mcnemar_exact(x, y)})
    for r_, p_ in zip(res, holm([r_["p_exact_mcnemar"] for r_ in res])): r_["p_holm"] = p_
    (run / "analysis.json").write_text(json.dumps({"split": split, "n_items": len(items), "contrasts": res,
        "note": "PILOT: non-confirmatory, no decision" if pilot else "confirmatory", "commit": commit}, indent=2))
    prereg = "lane_b/PREREGISTRATION_DRAFT.md#v0.1-DRAFT-UNFROZEN"; rows = []
    def row(arm, metric, unit, value, status="OBSERVED", note=None):
        rows.append({"schema_version": "cell_akamai.lane_b_result.v1", "experiment_id": cfg["experiment_id"], "arm": arm,
            "model": cfg["model"], "dataset_ref": f"ECA_NEXT_ROW_seed{cfg['seed_start']}_perrule{cfg['per_rule']}", "model_revision": None,
            "metric": metric, "unit": unit, "value": value, "status": status, "evidence_ref": str(run / "answers.jsonl") + "@" + commit["answers_sha256"],
            "evaluation_split": split, "source_class": source_class, "preregistration_ref": prereg, "commit_sha": None,
            "fco_occurrence_id": None, "claim_ceiling": "PILOT non-confirmatory; synthetic ECA control only" if pilot else "synthetic ECA control only"})
    for a in ARMS:
        s = stats[a]; n = s["n"]
        row(a, "exact_match_accuracy_primary", "fraction", sum(correct[a].values()) / n)
        row(a, "mean_hamming_error", "fraction_of_cells", s["ham"] / n)
        row(a, "abstention_rate", "fraction", s["abst"] / n)
        row(a, "parse_failure_rate", "fraction", s["parse"] / n)
        if s["tok_unknown"]:
            row(a, "completion_tokens_total", "tokens", None, "UNKNOWN"); row(a, "request_tokens_per_s", "tokens/s", None, "UNKNOWN")
        else:
            row(a, "completion_tokens_total", "tokens", s["tok"]); row(a, "request_tokens_per_s", "tokens/s", s["tok"] / s["wall"] if s["wall"] else None, "OBSERVED" if s["wall"] else "UNKNOWN")
        row(a, "wall_time_total", "s", s["wall"])
        row(a, "anticube_operational_class", "class", None, "NOT_COMPUTED")
        row(a, "delta_g_star", "UNDEFINED_NO_VALIDATED_FORMULA", None, "NOT_COMPUTED")
    (run / "lane_b_results.jsonl").write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in rows))
    print(f"scored {len(recs)} records; split={split}; wrote {len(rows)} rows")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], *(sys.argv[3:5][1:] if len(sys.argv) > 3 else []))
