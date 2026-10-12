"""Fixture tests. The fake model below is a SYNTHETIC_FIXTURE; results here are never evidence of any real run."""
import json, sys
from pathlib import Path
import pytest
H = Path(__file__).resolve().parents[1] / "harness"
sys.path.insert(0, str(H))
import run_lane_b, score_lane_b  # noqa: E402

CFG = {"experiment_id": "T", "mode": "PILOT_NONCONFIRMATORY", "model": "fake", "temperature": 0, "decode_seed": 1,
       "max_tokens_per_call": 10, "item_token_cap": 100, "item_call_cap": 3, "seed_start": 60000, "per_rule": 2, "base_url": "x"}


def fake_chat(messages):  # answers via the scorer's oracle: only for plumbing tests
    import re
    u = messages[-1]["content"]
    rule = int(re.search(r"rule (\d+)", u).group(1)); st = re.search(r"index 0..7\): ([01]{8})", u).group(1)
    it = {"rule": rule, "initial_state": [int(c) for c in st]}
    return "ANSWER: " + score_lane_b.oracle(it), 5, 0.01


def build(tmp_path):
    cfg = tmp_path / "c.json"; cfg.write_text(json.dumps(CFG))
    run_lane_b.main(cfg, tmp_path / "run", chat=fake_chat)
    return cfg


def test_end_to_end_and_rows_valid(tmp_path):
    cfg = build(tmp_path); score_lane_b.main(cfg, tmp_path / "run", "SYNTHETIC_FIXTURE")
    rows = [json.loads(l) for l in (tmp_path / "run" / "lane_b_results.jsonl").read_text().splitlines()]
    assert len(rows) == 44 and all(r["source_class"] == "SYNTHETIC_FIXTURE" for r in rows)
    acc = [r["value"] for r in rows if r["metric"] == "exact_match_accuracy_primary"]
    assert acc == [1.0] * 4
    assert all(r["value"] is None for r in rows if r["status"] == "NOT_COMPUTED")


def test_tampered_answers_refused(tmp_path):
    cfg = build(tmp_path); a = tmp_path / "run" / "answers.jsonl"; a.write_text(a.read_text() + "\n")
    with pytest.raises(SystemExit):
        score_lane_b.main(cfg, tmp_path / "run")


def test_oracle_matches_closed_forms():
    import itertools
    for bits in itertools.product([0, 1], repeat=8):
        L = [bits[(i - 1) % 8] for i in range(8)]; R = [bits[(i + 1) % 8] for i in range(8)]
        r30 = "".join(str(L[i] ^ (bits[i] | R[i])) for i in range(8))
        r90 = "".join(str(L[i] ^ R[i]) for i in range(8))
        assert score_lane_b.oracle({"rule": 30, "initial_state": list(bits)}) == r30
        assert score_lane_b.oracle({"rule": 90, "initial_state": list(bits)}) == r90
