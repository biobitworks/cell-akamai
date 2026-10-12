"""Refusal and metric rules of the independent scorer. All runs here are SYNTHETIC_FIXTURE plumbing tests."""
import hashlib, json, sys
from pathlib import Path
import pytest
H = Path(__file__).resolve().parents[1] / "harness"
sys.path.insert(0, str(H))
import run_lane_b, score_lane_b  # noqa: E402
from test_harness import CFG, fake_chat  # noqa: E402


def build(tmp_path, cfg=CFG):
    c = tmp_path / "c.json"; c.write_text(json.dumps(cfg))
    run_lane_b.main(c, tmp_path / "run", chat=fake_chat)
    return c, tmp_path / "run"


def recommit(run, rows=None, **extra):
    if rows is not None:
        (run / "answers.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    commit = json.loads((run / "COMMIT.json").read_text())
    commit["answers_sha256"] = hashlib.sha256((run / "answers.jsonl").read_bytes()).hexdigest()
    commit.update(extra)
    (run / "COMMIT.json").write_text(json.dumps(commit))


def rows(run):
    return [json.loads(l) for l in (run / "answers.jsonl").read_text().splitlines()]


def refused(cfg, run, **kw):
    with pytest.raises(SystemExit):
        score_lane_b.main(cfg, run, "SYNTHETIC_FIXTURE", **kw)
    return json.loads((run / "score_refusal.json").read_text())["reason"]


def test_config_digest_mismatch_refused(tmp_path):
    cfg, run = build(tmp_path)
    cfg.write_text(json.dumps({**CFG, "temperature": 1}))
    assert "CONFIG" in refused(cfg, run)


def test_missing_config_digest_refused(tmp_path):
    cfg, run = build(tmp_path)
    c = json.loads((run / "COMMIT.json").read_text()); c.pop("config_sha256"); (run / "COMMIT.json").write_text(json.dumps(c))
    assert "CONFIG" in refused(cfg, run)


def test_missing_arm_row_refused(tmp_path):
    cfg, run = build(tmp_path)
    recommit(run, [r for r in rows(run) if not (r["arm"] == "B3_RANDOM_CONTROL" and r["item_id"] == "ECA-30-60000")])
    assert "COVERAGE" in refused(cfg, run)


def test_unknown_arm_refused(tmp_path):
    cfg, run = build(tmp_path)
    rr = rows(run); rr[0]["arm"] = "B4_UNDECLARED"; recommit(run, rr)
    assert "COVERAGE" in refused(cfg, run)


def test_duplicate_row_refused(tmp_path):
    cfg, run = build(tmp_path)
    rr = rows(run); recommit(run, rr + [rr[0]])
    assert "COVERAGE" in refused(cfg, run)


def frozen(tmp_path, items):
    d = tmp_path / "d.jsonl"; d.write_text("".join(json.dumps(i, sort_keys=True) + "\n" for i in items))
    m = tmp_path / "m.json"; m.write_text(json.dumps({"sha256": "sha256:" + hashlib.sha256(d.read_bytes()).hexdigest()}))
    return d, m


def test_dataset_checks(tmp_path):
    cfg, run = build(tmp_path)
    items = [json.loads(l) for l in (run / "items.jsonl").read_text().splitlines()]
    d, m = frozen(tmp_path, items)
    score_lane_b.main(cfg, run, "SYNTHETIC_FIXTURE", str(d), str(m))  # all frozen: scores
    m.write_text(json.dumps({"sha256": "sha256:" + "0" * 64}))
    assert "DATASET" in refused(cfg, run, dataset=str(d), manifest=str(m))
    d2, m2 = frozen(tmp_path, [{**items[0], "initial_state": [1 - b for b in items[0]["initial_state"]]}] + items[1:])
    assert "FROZEN" in refused(cfg, run, dataset=str(d2), manifest=str(m2))
    d3, m3 = frozen(tmp_path, items); recommit(run, dataset_sha256="sha256:" + "f" * 64)
    assert "dataset_sha256" in refused(cfg, run, dataset=str(d3), manifest=str(m3))


def test_failed_but_wellformed_answer_is_incorrect(tmp_path):
    cfg, run = build(tmp_path)
    rr = rows(run)
    for r in rr:
        if r["arm"] == "B0_FIXED":
            r["failure"] = "Timeout"  # text is the correct answer, but the call failed
    recommit(run, rr)
    per_arm, _, _ = score_lane_b.main(cfg, run, "SYNTHETIC_FIXTURE")
    assert per_arm["B0_FIXED"]["exact_match_accuracy"] == 0.0 and per_arm["B1_GENESIS"]["exact_match_accuracy"] == 1.0


def test_hamming_counts_length_mismatch():
    assert score_lane_b.hamming("0101", "01010000") == 0.5
    assert score_lane_b.hamming("ABSTAIN", "01010000") == 1.0 and score_lane_b.hamming(None, "01010000") == 1.0


def test_fixture_commit_cannot_be_labeled_observed(tmp_path):
    cfg, run = build(tmp_path); recommit(run, source_class="SYNTHETIC_FIXTURE")
    score_lane_b.main(cfg, run, "OBSERVED")
    assert json.loads((run / "analysis.json").read_text())["source_class"] == "SYNTHETIC_FIXTURE"


def test_metrics_calls_tokens_discordance(tmp_path):
    cfg, run = build(tmp_path)
    per_arm, contrasts, checks = score_lane_b.main(cfg, run, "SYNTHETIC_FIXTURE")
    assert per_arm["B0_FIXED"]["model_calls_per_item"] == 1 and per_arm["B2_GENESIS_DAISY"]["model_calls_per_item"] == 3
    assert per_arm["B0_FIXED"]["tokens_per_correct_item"] == 5.0  # fake: 5 tokens/call, all correct
    assert all(c["discordant_pairs"] == 0 for c in contrasts) and checks["complete_paired_coverage"]


def test_cli_parses_flags(tmp_path):
    cfg, run = build(tmp_path)
    score_lane_b.cli([str(cfg), str(run), "--source-class", "SYNTHETIC_FIXTURE"])
    with pytest.raises(SystemExit):
        score_lane_b.cli([str(cfg), str(run), "--dataset", "x"])
