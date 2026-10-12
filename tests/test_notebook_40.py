"""Execute the replay notebook headless against a SYNTHETIC_FIXTURE run (no model calls, no network)."""
import json, os, sys
from pathlib import Path
import nbformat
from nbclient import NotebookClient
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lane_b/harness")); sys.path.insert(0, str(ROOT / "lane_b/tests")); sys.path.insert(0, str(ROOT / "tools/concurrency"))
import run_concurrency, score_concurrency  # noqa: E402
from test_harness import fake_chat  # noqa: E402

DATA, MAN = ROOT / "dataset/eca_pilot_inputs_v1.jsonl", ROOT / "dataset/eca_pilot_manifest_v1.json"


def run_nb(runs):
    nb = nbformat.read(ROOT / "notebooks/40_concurrency_replay_dashboard.ipynb", as_version=4)
    os.environ["CELL_AKAMAI_RUNS"] = str(runs)
    NotebookClient(nb, timeout=120, kernel_name="python3", resources={"metadata": {"path": str(ROOT / "notebooks")}}).execute()
    return "\n".join(o.get("text", "") for c in nb.cells if c.cell_type == "code" for o in c.outputs)


def test_notebook_without_receipts_reports_not_tested(tmp_path):
    out = run_nb(tmp_path / "empty")
    assert "DATASET_SHA_VERIFIED" in out and "NOT_TESTED — no scored Lane B panels" in out


def test_notebook_renders_scored_synthetic_panels(tmp_path):
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({"experiment_id": "T", "mode": "PILOT_NONCONFIRMATORY", "model": "fake", "temperature": 0, "decode_seed": 1,
                               "max_tokens_per_call": 10, "item_token_cap": 100, "item_call_cap": 3, "seed_start": 50000, "per_rule": 8}))
    runs = tmp_path / "runs"
    folder = run_concurrency.main(["--dataset", str(DATA), "--manifest", str(MAN), "--config", str(cfg), "--harness",
                                   str(ROOT / "lane_b/harness/run_lane_b.py"), "--backend", "SYNTHETIC_FIXTURE", "--concurrency", "1",
                                   "--limit-items", "4", "--output-root", str(runs), "--execute"], injected_chat=fake_chat)
    score_concurrency.summarize(folder, cfg, DATA, MAN)
    out = run_nb(runs)
    assert "SYNTHETIC_FIXTURE" in out and "plumbing only" in out and "B2_GENESIS_DAISY vs B3_RANDOM_CONTROL" in out
    assert "ANTICUBE NOT_COMPUTED" in out
