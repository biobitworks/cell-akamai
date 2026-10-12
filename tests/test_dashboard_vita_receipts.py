"""Synthetic fixture tests for allowlisted, redacted Vita dashboard receipts."""
import json
from pathlib import Path

from tools.concurrency.serve_dashboard import HTML, load_vita_experiments

NAMES = (
    "AKAMAI_VITA_R4_CPU_REPLAY.json",
    "AKAMAI_VITA_CPU_TRAINING_SUCCESSOR.json",
    "AKAMAI_GENESIS_VCC2025_HOLDOUT.json",
)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def test_synthetic_fixture_allowlist_and_redaction(tmp_path):
    root = tmp_path / "evidence" / "20261012"
    write(root / NAMES[0], {
        "run_id": "fixture-replay", "status": "COMPLETED", "device": "cpu",
        "source_sha": "a" * 64, "test_set_evaluated": False,
        "training_performed": False,
        "cells": [{"rows": 10, "duration_s": 2, "rows_per_s": 5,
                   "anticube_accuracy": 0.5, "anticube_ce": 1.2,
                   "delta_g_star_mse": 0.4, "loss": 1.3, "failures_count": 0,
                   "predictions": ["PRIVATE_RESPONSE"], "path": "/private/path"}],
        "raw_response": "PRIVATE_RESPONSE", "secret": "DO_NOT_SERVE",
    })
    write(root / NAMES[1], {
        "status": "COMPLETED", "device": "cpu", "execution_source_sha": "b" * 40,
        "config_sha256": "c" * 64, "merkle_root": "d" * 64,
        "executed_optimizer_steps": 8, "test_set_evaluated": False,
        "decision": "RETAIN_PARENT_VALIDATION_LOSS_WORSENED",
        "validation": [{"label": "baseline", "rows": 10, "duration_s": 1,
                        "anticube_accuracy": 0.6, "anticube_ce": 1,
                        "delta_g_star_mse": 0.3, "loss": 1.1,
                        "response": "PRIVATE_RESPONSE"}],
        "steps": [{"huge_raw_payload": "PRIVATE_RESPONSE"}],
    })
    write(root / NAMES[2], {
        "status": "SCORED_PUBLIC_PROXY_HOLDOUT", "device": "cpu",
        "source_sha": "e" * 64, "rows": 12, "genes": 99, "duration_s": 2,
        "failures_count": 0,
        "mse": {"no_change": 0.8, "train_only_fixed_prior": 0.7,
                "frozen_genesis_r3": 0.6, "response": "PRIVATE_RESPONSE"},
        "paired_mse_delta_genesis_minus_prior": -0.1,
        "paired_batch_bootstrap_95_interval": [-0.2, -0.05],
        "official_vcc_score": True, "raw_array": ["PRIVATE_RESPONSE"],
    })
    write(root / "UNAPPROVED_PRIVATE_RECEIPT.json", {"secret": "DO_NOT_SERVE"})

    data = load_vita_experiments(root)
    encoded = json.dumps(data)
    assert [x["id"] + ".json" for x in data["experiments"]] == list(NAMES)
    assert "PRIVATE_RESPONSE" not in encoded
    assert "DO_NOT_SERVE" not in encoded
    assert "/private/path" not in encoded
    assert "UNAPPROVED_PRIVATE_RECEIPT" not in encoded
    replay, successor, holdout = data["experiments"]
    assert replay["metrics"]["cells"][0]["anticube_accuracy"] == 0.5
    assert replay["metrics"]["cells"][0]["failures_count"] == 0
    assert successor["metrics"]["executed_optimizer_steps"] == 8
    assert successor["metrics"]["validation"][0]["label"] == "baseline"
    assert holdout["metrics"]["paired_batch_bootstrap_95_interval"] == [-0.2, -0.05]
    assert holdout["metrics"]["official_vcc_score"] is False
    assert all(len(x["receipt_sha256"]) == 64 for x in data["experiments"])


def test_synthetic_fixture_missing_invalid_and_partial_receipt_keeps_last_snapshot(tmp_path):
    root = tmp_path / "receipts"
    assert load_vita_experiments(root)["experiments"] == []
    path = root / NAMES[0]
    write(path, {"status": "COMPLETED", "device": "cpu", "source_sha": "a" * 64,
                 "cells": [{"anticube_accuracy": 0.25, "loss": 2.0}]})
    first = load_vita_experiments(root)["experiments"][0]
    path.write_text('{"status":"COMPLETED","cells":[')
    after_invalid = load_vita_experiments(root)["experiments"][0]
    assert after_invalid == first
    path.write_text(json.dumps({"status": "COMPLETED"}))
    after_partial = load_vita_experiments(root)["experiments"][0]
    assert after_partial == first


def test_dashboard_renders_actual_experiment_endpoint_and_scoped_claim_labels():
    assert "fetch('/experiments.json'" in HTML
    assert "Anticube [%]" in HTML
    assert "ΔG target MSE" in HTML
    assert "Genesis baseline MSE" in HTML
    assert "Candidate MSE (frozen Genesis)" in HTML
    assert "95% interval" in HTML
    assert "NOT PROVIDED" in HTML
    assert "public proxy holdout" in HTML.lower()
