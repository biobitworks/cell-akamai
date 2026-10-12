import json

from tools.concurrency.serve_dashboard import load_sanitized


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def test_dashboard_preserves_zero_null_and_reports_pending_separately(tmp_path):
    run = tmp_path / "concurrency-07-demo"
    write_json(run / "run_manifest.json", {
        "run_id": "demo", "module": "07", "backend": "MAGICPRO_OLLAMA",
        "stage": "local", "state": "IN_PROGRESS", "served_model_requested": "llama3.2:3b",
    })
    write_json(run / "bench_cells.json", {"rows": [{
        "arm": "B0_FIXED", "concurrency": 1, "items": 4,
        "model_calls_observed": 4, "aggregate_completion_tokens_per_s": 0.0,
        "latency_p95_ms": None, "failed_or_abstained_or_over_budget": 4,
        "token_count_status": "UNKNOWN",
    }]})

    data = load_sanitized(tmp_path)

    assert data["rows"][0]["aggregate_completion_tokens_per_s"] == 0.0
    assert data["rows"][0]["latency_p95_ms"] is None
    pending = data["pending"][0]
    assert pending["run_id"] == "demo"
    assert pending["backend"] == "MAGICPRO_OLLAMA"
    assert pending["served_model_requested"] == "llama3.2:3b"
    assert pending["run_state"] == "IN_PROGRESS"
    assert pending["score_state"] == "PENDING"
    assert pending["reason"] == "Run is still in progress; no independent score receipt is present."
    assert data["science"] == []
    assert "PENDING: '+active" in __import__("tools.concurrency.serve_dashboard", fromlist=["HTML"]).HTML


def test_dashboard_reports_aggregates_without_claiming_scoring(tmp_path):
    run = tmp_path / "concurrency-07-demo"
    write_json(run / "run_manifest.json", {
        "run_id": "demo", "module": "07", "backend": "AKAMAI_VLLM",
        "stage": "short", "state": "COMPLETED_WITH_RESULT_OR_FAILURE_ROWS",
    })
    write_json(run / "bench_cells.json", {"rows": [{
        "arm": "B0_FIXED", "concurrency": 1, "items": 4,
        "model_calls_observed": 4, "aggregate_completion_tokens_per_s": 0.0,
        "latency_p95_ms": 0.0, "failed_or_abstained_or_over_budget": 4,
    }]})

    data = load_sanitized(tmp_path)

    assert data["science"] == []
    assert data["pending"][0]["score_state"] == "UNSCORED"
    assert "No independent score receipt" in data["pending"][0]["reason"]
    assert data["rows"][0]["aggregate_completion_tokens_per_s"] == 0.0


def test_dashboard_distinguishes_empty_source_from_zero_measurements(tmp_path):
    assert load_sanitized(tmp_path / "missing") == {
        "schema": "cell_akamai.concurrent_summary.v1", "rows": [], "science": [], "pending": []
    }
    run = tmp_path / "concurrency-07-demo"
    write_json(run / "run_manifest.json", {"run_id": "demo", "state": "COMPLETED"})
    write_json(run / "bench_cells.json", {"rows": [{
        "arm": "B0_FIXED", "concurrency": 1,
        "aggregate_completion_tokens_per_s": 0.0,
    }]})
    assert load_sanitized(tmp_path)["rows"][0]["aggregate_completion_tokens_per_s"] == 0.0


def test_terminal_marker_overrides_stale_in_progress_manifest(tmp_path):
    run = tmp_path / "concurrency-07-stopped"
    write_json(run / "run_manifest.json", {"run_id": "stopped", "state": "IN_PROGRESS"})
    write_json(run / "STOPPED_CORRECTION.json", {"state": "KILLED_SIGKILL", "reason": "private context is ignored"})

    pending = load_sanitized(tmp_path)["pending"]

    assert len(pending) == 1
    assert pending[0]["score_state"] == "STOPPED_UNSCORED"
    assert pending[0]["run_marker_state"] == "KILLED_SIGKILL"
    assert "private context" not in pending[0]["reason"]
