"""Regression tests for PR #13 review findings. SYNTHETIC_FIXTURE plumbing only."""
import json, sys
from pathlib import Path
import pytest
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "lane_b/harness")); sys.path.insert(0, str(ROOT / "tools/concurrency"))
import run_lane_b, run_concurrency, score_concurrency  # noqa: E402

CFG = {"decode_seed": 1, "item_token_cap": 100, "item_call_cap": 3}
IT = {"item_id": "ECA-30-1", "rule": 30, "width": 8, "initial_state": [0, 1, 0, 1, 0, 1, 0, 1]}


def test_parse_rejects_nine_bits_and_trailing_junk():
    assert run_lane_b.parse("ANSWER: 010101010") is None
    assert run_lane_b.parse("ANSWER: 01010101x") is None
    assert run_lane_b.parse("ANSWER: 01010101.") == "01010101" and run_lane_b.parse("ANSWER: ABSTAIN") == "ABSTAIN"


def test_partial_calls_survive_a_later_failure():
    n = {"i": 0}
    def chat(messages):
        n["i"] += 1
        if n["i"] == 2: raise TimeoutError("second call")
        return "ANSWER: 00000000", 7, 0.5
    rec = run_lane_b.run_item("B2_GENESIS_DAISY", IT, chat, CFG)
    assert rec["failure"] == "TimeoutError" and rec["final_answer"] is None
    assert rec["n_calls"] == 1 and rec["tokens_total"] == 7 and rec["wall_s_total"] == 0.5


def test_abstention_counts_as_unsuccessful():
    rows = [{"final_answer": "ABSTAIN", "n_calls": 1, "tokens_total": 3}, {"final_answer": "01010101", "n_calls": 1, "tokens_total": 3}]
    s = run_concurrency.summarize(rows, "B0_FIXED", 1, 1.0)
    assert s["failed_or_abstained_or_over_budget"] == 1 and s["successful_parsed_within_budget"] == 1


def test_scheduled_but_uncommitted_panel_is_refused(tmp_path):
    (tmp_path / "run_manifest.json").write_text(json.dumps({"run_id": "r", "concurrency": [1, 4], "backend": "SYNTHETIC_FIXTURE", "stage": "x"}))
    m = tmp_path / "m.json"; m.write_text(json.dumps({"sha256": "sha256:" + "0" * 64}))
    out = score_concurrency.summarize(tmp_path, None, tmp_path / "d.jsonl", m)
    assert [(p["concurrency"], p["state"]) for p in out["panels"]] == [(1, "REFUSED"), (4, "REFUSED")]
    assert all("NEVER COMMITTED" in p["reason"] for p in out["panels"])
