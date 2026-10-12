#!/usr/bin/env python3
"""Independent scorer: verifies every commitment, recomputes the ECA oracle on its own, writes rows + analysis.

Usage:
  score_lane_b.py CONFIG.json RUN_DIR [--source-class OBSERVED|SYNTHETIC_FIXTURE]
                  [--dataset dataset/eca_pilot_inputs_v1.jsonl --manifest dataset/eca_pilot_manifest_v1.json]

Refuses to score (exit code 1, writes RUN_DIR/score_refusal.json) unless:
  * answers.jsonl matches COMMIT.json answers_sha256;
  * CONFIG matches COMMIT.json config_sha256;
  * with --manifest: the dataset file matches the manifest SHA, COMMIT.json dataset_sha256 (if recorded)
    matches it, and every item in items.jsonl is exactly a record of the frozen dataset;
  * coverage is complete: exactly the four arms, each with exactly one row per item, no unknown items/arms.
Oracle is re-implemented here deliberately; it is not imported from the runner.
"""
import argparse, hashlib, json, sys
from math import comb
from pathlib import Path

ARMS = ["B0_FIXED", "B1_GENESIS", "B2_GENESIS_DAISY", "B3_RANDOM_CONTROL"]
CONTRASTS = [("B2_GENESIS_DAISY", "B3_RANDOM_CONTROL"), ("B1_GENESIS", "B0_FIXED"), ("B2_GENESIS_DAISY", "B1_GENESIS")]
ARM_NOTES = {
    "B0_FIXED": "1 model call per item",
    "B1_GENESIS": "GENESIS_POLICY_PROXY_V0: 3 prompt variants + majority vote; NOT the recovered Genesis policy",
    "B2_GENESIS_DAISY": "3 calls: answer, blanket critique ('find any wrong cell'), adjudicate; inference-time challenge, NOT weight training",
    "B3_RANDOM_CONTROL": "3 calls: answer, re-check of one random cell, adjudicate; randomized adversarial control, NOT an inert placebo",
}
FAIRNESS = ("Arms are not compute-matched: B0 uses 1 call, B1-B3 use 3. B2 vs B3 differ in challenge content "
            "(blanket critique vs single random-cell re-check), and a random-cell re-check is itself verification. "
            "No causal attribution to DAISY challenge content is supported by these contrasts alone.")


def h(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def bare(d):
    return d.split(":", 1)[1] if isinstance(d, str) and d.startswith("sha256:") else d


def oracle(it):  # periodic boundary, Wolfram encoding L*4+C*2+R (matches recovered RUN001 independent_oracle)
    b, r, n = it["initial_state"], it["rule"], len(it["initial_state"])
    return "".join(str((r >> ((b[(i - 1) % n] << 2) | (b[i] << 1) | b[(i + 1) % n])) & 1) for i in range(n))


def hamming(fa, truth):
    """Fraction of cells wrong. Missing/extra cells count as wrong; non-answers count as all wrong."""
    if not isinstance(fa, str) or fa == "ABSTAIN" or not fa or any(ch not in "01" for ch in fa):
        return 1.0
    n = len(truth)
    wrong = sum(x != y for x, y in zip(fa, truth)) + abs(len(fa) - n)
    return min(1.0, wrong / n)


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


class Refusal(Exception):
    pass


def verify(cfg_path, run, dataset=None, manifest=None):
    """All pre-scoring checks. Returns (commit, items, recs, checks) or raises Refusal."""
    checks = {}
    commit = json.loads((run / "COMMIT.json").read_text())
    checks["answers_sha256_matches"] = h((run / "answers.jsonl").read_bytes()) == bare(commit.get("answers_sha256"))
    if not checks["answers_sha256_matches"]:
        raise Refusal("ANSWER COMMIT MISMATCH")
    checks["config_sha256_matches"] = bool(commit.get("config_sha256")) and h(Path(cfg_path).read_bytes()) == bare(commit["config_sha256"])
    if not checks["config_sha256_matches"]:
        raise Refusal("CONFIG DIGEST MISSING OR MISMATCHED")
    items_list = [json.loads(l) for l in (run / "items.jsonl").read_text().splitlines() if l.strip()]
    items = {i["item_id"]: i for i in items_list}
    if len(items) != len(items_list) or not items:
        raise Refusal("EMPTY OR DUPLICATE ITEM IDS")
    if manifest is not None:
        man = json.loads(Path(manifest).read_text())
        data_bytes = Path(dataset).read_bytes()
        checks["dataset_sha256_matches_manifest"] = h(data_bytes) == bare(man["sha256"])
        if not checks["dataset_sha256_matches_manifest"]:
            raise Refusal("DATASET DIGEST MISMATCH vs manifest")
        if commit.get("dataset_sha256") is not None:
            checks["commit_dataset_sha256_matches"] = bare(commit["dataset_sha256"]) == bare(man["sha256"])
            if not checks["commit_dataset_sha256_matches"]:
                raise Refusal("COMMIT dataset_sha256 does not match the frozen dataset")
        frozen = {r["item_id"]: r for r in (json.loads(l) for l in data_bytes.decode().splitlines() if l.strip())}
        checks["items_are_frozen_records"] = all(i in frozen and frozen[i] == items[i] for i in items)
        if not checks["items_are_frozen_records"]:
            raise Refusal("ITEMS NOT IDENTICAL TO FROZEN DATASET RECORDS")
    recs = [json.loads(l) for l in (run / "answers.jsonl").read_text().splitlines() if l.strip()]
    cells = {}
    for r in recs:
        cells[(r.get("arm"), r.get("item_id"))] = cells.get((r.get("arm"), r.get("item_id")), 0) + 1
    unknown_arms = sorted({str(a) for a, _ in cells if a not in ARMS})
    unknown_items = sorted({str(i) for _, i in cells if i not in items})
    missing = [f"{a}/{i}" for a in ARMS for i in sorted(items) if cells.get((a, i), 0) == 0]
    dupes = [f"{a}/{i}" for (a, i), n in cells.items() if n > 1]
    checks.update({"unknown_arms": unknown_arms, "unknown_items": unknown_items, "missing_cells": missing[:20],
                   "duplicate_cells": dupes[:20], "expected_rows": len(ARMS) * len(items), "rows": len(recs)})
    checks["complete_paired_coverage"] = not (unknown_arms or unknown_items or missing or dupes) and len(recs) == len(ARMS) * len(items)
    if not checks["complete_paired_coverage"]:
        raise Refusal("INCOMPLETE OR INVALID ARM x ITEM COVERAGE")
    return commit, items, recs, checks


def score(items, recs):
    correct = {a: {} for a in ARMS}
    stats = {a: dict(ham=0.0, abst=0, parse=0, fail=0, over=0, tok=0, tok_unknown=0, calls=0, wall=0.0, n=0) for a in ARMS}
    for r in recs:
        truth = oracle(items[r["item_id"]]); fa = r.get("final_answer"); s = stats[r["arm"]]; s["n"] += 1
        s["wall"] += r.get("wall_s_total") or 0.0; s["calls"] += r.get("n_calls") or 0
        s["fail"] += 1 if r.get("failure") else 0; s["over"] += 1 if r.get("over_budget") else 0
        if r.get("tokens_total") is None: s["tok_unknown"] += 1
        else: s["tok"] += r["tokens_total"]
        if fa == "ABSTAIN": s["abst"] += 1
        if fa is None: s["parse"] += 1
        # failure, over-budget, parse failure and abstention all count as incorrect, even if the text is well-formed
        correct[r["arm"]][r["item_id"]] = fa == truth and not r.get("over_budget") and not r.get("failure")
        s["ham"] += hamming(fa, truth)
    per_arm = {}
    for a in ARMS:
        s = stats[a]; n = s["n"]; k = sum(correct[a].values()); known = s["tok_unknown"] == 0
        per_arm[a] = {"n_items": n, "correct": k, "exact_match_accuracy": k / n, "mean_hamming_error": s["ham"] / n,
                      "abstention_rate": s["abst"] / n, "parse_failure_rate": s["parse"] / n, "failure_rate": s["fail"] / n,
                      "over_budget_rate": s["over"] / n, "model_calls": s["calls"], "model_calls_per_item": s["calls"] / n,
                      "completion_tokens": s["tok"] if known else None,
                      "tokens_per_correct_item": (s["tok"] / k) if known and k else None,
                      "tokens_per_correct_item_denominator": (f"{k} correct of {n}" if known else "UNKNOWN (missing usage)"),
                      "wall_s_total": s["wall"], "note": ARM_NOTES[a]}
    contrasts = []
    ids = sorted(items)
    for a, b in CONTRASTS:
        x = sum(correct[a][i] and not correct[b][i] for i in ids); y = sum(correct[b][i] and not correct[a][i] for i in ids)
        both = sum(correct[a][i] and correct[b][i] for i in ids)
        contrasts.append({"A": a, "B": b, "A_only_correct": x, "B_only_correct": y, "both_correct": both,
                          "both_wrong": len(ids) - x - y - both, "discordant_pairs": x + y, "p_exact_mcnemar": mcnemar_exact(x, y)})
    for c, p in zip(contrasts, holm([c["p_exact_mcnemar"] for c in contrasts])): c["p_holm"] = p
    return per_arm, contrasts


def main(cfg_path, run_dir, source_class="OBSERVED", dataset=None, manifest=None):
    cfg = json.loads(Path(cfg_path).read_text()); run = Path(run_dir)
    try:
        commit, items, recs, checks = verify(cfg_path, run, dataset, manifest)
    except Refusal as e:  # retained as a failure record; nothing is scored
        (run / "score_refusal.json").write_text(json.dumps({"state": "REFUSED", "reason": str(e), "scored": False}, indent=2) + "\n")
        sys.exit(f"REFUSED: {e}")
    if commit.get("source_class") == "SYNTHETIC_FIXTURE":
        source_class = "SYNTHETIC_FIXTURE"  # a fixture commit can never be relabeled as observed model performance
    pilot = cfg.get("mode") != "CONFIRMATORY_FROZEN"
    split = "PILOT_NONCONFIRMATORY" if pilot else "HELDOUT_FROZEN"
    per_arm, contrasts = score(items, recs)
    (run / "analysis.json").write_text(json.dumps({
        "split": split, "source_class": source_class, "n_items": len(items), "checks": checks, "per_arm": per_arm,
        "contrasts": contrasts, "arm_fairness": FAIRNESS, "genesis_policy": commit.get("genesis_policy"),
        "anticube": "NOT_COMPUTED", "delta_g_star": "NOT_COMPUTED", "self_training": "NOT_TESTED (no weight updates)",
        "note": "PILOT: non-confirmatory, no decision" if pilot else "confirmatory", "commit": commit}, indent=2, sort_keys=True) + "\n")
    prereg = "lane_b/PREREGISTRATION_DRAFT.md#v0.1-DRAFT-UNFROZEN"; rows = []
    def row(arm, metric, unit, value, status="OBSERVED"):
        rows.append({"schema_version": "cell_akamai.lane_b_result.v1", "experiment_id": cfg["experiment_id"], "arm": arm,
            "model": cfg["model"], "dataset_ref": f"ECA_NEXT_ROW_seed{cfg['seed_start']}_perrule{cfg['per_rule']}", "model_revision": None,
            "metric": metric, "unit": unit, "value": value, "status": status,
            "evidence_ref": str(run / "answers.jsonl") + "@" + bare(commit["answers_sha256"]),
            "evaluation_split": split, "source_class": source_class, "preregistration_ref": prereg, "commit_sha": None,
            "fco_occurrence_id": None, "claim_ceiling": "PILOT non-confirmatory; synthetic ECA control only" if pilot else "synthetic ECA control only"})
    for a in ARMS:
        p = per_arm[a]; tok = p["completion_tokens"]
        row(a, "exact_match_accuracy_primary", "fraction", p["exact_match_accuracy"])
        row(a, "mean_hamming_error", "fraction_of_cells", p["mean_hamming_error"])
        row(a, "abstention_rate", "fraction", p["abstention_rate"])
        row(a, "parse_failure_rate", "fraction", p["parse_failure_rate"])
        row(a, "model_calls", "calls", p["model_calls"])
        if tok is None:
            row(a, "completion_tokens_total", "tokens", None, "UNKNOWN"); row(a, "request_tokens_per_s", "tokens/s", None, "UNKNOWN")
            row(a, "tokens_per_correct_item", "tokens/correct_item", None, "UNKNOWN")
        else:
            row(a, "completion_tokens_total", "tokens", tok)
            row(a, "request_tokens_per_s", "tokens/s", tok / p["wall_s_total"] if p["wall_s_total"] else None, "OBSERVED" if p["wall_s_total"] else "UNKNOWN")
            row(a, "tokens_per_correct_item", "tokens/correct_item", p["tokens_per_correct_item"], "OBSERVED" if p["correct"] else "UNDEFINED_ZERO_CORRECT")
        row(a, "wall_time_total", "s", p["wall_s_total"])
        row(a, "anticube_operational_class", "class", None, "NOT_COMPUTED")
        row(a, "delta_g_star", "UNDEFINED_NO_VALIDATED_FORMULA", None, "NOT_COMPUTED")
    (run / "lane_b_results.jsonl").write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in rows))
    print(f"scored {len(recs)} records; split={split}; source={source_class}; wrote {len(rows)} rows")
    return per_arm, contrasts, checks


def cli(argv=None):
    ap = argparse.ArgumentParser(description="Independent Lane B scorer")
    ap.add_argument("config"); ap.add_argument("run_dir")
    ap.add_argument("--source-class", choices=["OBSERVED", "SYNTHETIC_FIXTURE"], default="OBSERVED")
    ap.add_argument("--dataset"); ap.add_argument("--manifest")
    a = ap.parse_args(argv)
    if bool(a.dataset) != bool(a.manifest):
        ap.error("--dataset and --manifest must be given together")
    main(a.config, a.run_dir, a.source_class, a.dataset, a.manifest)


if __name__ == "__main__":
    cli()
