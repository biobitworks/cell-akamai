"""Runner -> commitment -> independent scorer, end to end. SYNTHETIC_FIXTURE only: never model performance."""
import json, sys
from pathlib import Path
import pytest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lane_b/harness")); sys.path.insert(0, str(ROOT / "lane_b/tests")); sys.path.insert(0, str(ROOT / "tools/concurrency"))
import run_concurrency, score_concurrency  # noqa: E402
from test_harness import fake_chat  # noqa: E402

DATA, MAN = ROOT / "dataset/eca_pilot_inputs_v1.jsonl", ROOT / "dataset/eca_pilot_manifest_v1.json"


@pytest.fixture
def run(tmp_path):
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({"experiment_id": "T", "mode": "PILOT_NONCONFIRMATORY", "model": "fake", "temperature": 0, "decode_seed": 1,
                               "max_tokens_per_call": 10, "item_token_cap": 100, "item_call_cap": 3, "seed_start": 50000, "per_rule": 8}))
    folder = run_concurrency.main(["--dataset", str(DATA), "--manifest", str(MAN), "--config", str(cfg),
                                   "--harness", str(ROOT / "lane_b/harness/run_lane_b.py"), "--backend", "SYNTHETIC_FIXTURE",
                                   "--concurrency", "1", "2", "--limit-items", "4", "--output-root", str(tmp_path / "runs"), "--execute"],
                                  injected_chat=fake_chat)
    return Path(folder), cfg


def test_all_panels_scored_after_commitment(run):
    folder, cfg = run
    out = score_concurrency.summarize(folder, cfg, DATA, MAN)
    assert [p["state"] for p in out["panels"]] == ["SCORED", "SCORED"]
    assert len(out["rows"]) == 8 and all(r["source_class"] == "SYNTHETIC_FIXTURE" for r in out["rows"])
    assert {r["model_calls_per_item"] for r in out["rows"] if r["arm"] == "B0_FIXED"} == {1.0}
    assert out["anticube"] == out["delta_g_star"] == "NOT_COMPUTED" and out["backend_family"] == "SYNTHETIC_FIXTURE"
    text = (folder / "lane_b_concurrency_summary.json").read_text()
    assert "ANSWER:" not in text and "text" not in json.loads(text)["rows"][0]  # sanitized: no model text


def test_tampered_panel_refused_and_retained(run):
    folder, cfg = run
    a = folder / "c02_paired_for_scoring" / "answers.jsonl"; a.write_text(a.read_text() + "\n")
    out = score_concurrency.summarize(folder, cfg, DATA, MAN)
    states = {p["concurrency"]: p for p in out["panels"]}
    assert states[1]["state"] == "SCORED" and states[2]["state"] == "REFUSED" and "COMMIT" in states[2]["reason"]
    assert (folder / "c02_paired_for_scoring" / "score_refusal.json").exists()
    assert {r["concurrency"] for r in out["rows"]} == {1}


def test_wrong_config_refused(run, tmp_path):
    folder, _ = run
    other = tmp_path / "other.json"; other.write_text("{}")
    out = score_concurrency.summarize(folder, other, DATA, MAN)
    assert all(p["state"] == "REFUSED" and "CONFIG" in p["reason"] for p in out["panels"])


def test_backend_families_kept_separate():
    assert score_concurrency.family("AKAMAI_VLLM", "fp8") == "AKAMAI_FP8"
    assert score_concurrency.family("AKAMAI_VLLM", "speculative") == "AKAMAI_SPECULATIVE"
    assert score_concurrency.family("MAGICSTUDIO_OLLAMA", "x") == "MAGICSTUDIO_OLLAMA"
