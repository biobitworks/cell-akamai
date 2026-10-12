"""Importer integrity rules and the committed evidence index. No network, no GPU."""
import glob, hashlib, io, json, sys, zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/dashboard"))
import import_evidence as I  # noqa: E402

REQ = ("experiment_id", "run_id", "source_archive", "source_sha256", "commit_sha", "dataset_sha256", "model_identity",
       "workload", "metric", "unit", "value", "state", "evidence_ref")


def latest():
    vs = sorted(glob.glob(str(ROOT / "evidence/dashboard/DASHBOARD_EVIDENCE_INDEX.v*.json")), key=lambda p: int(p.split(".v")[-1][:-5]))
    return json.loads(Path(vs[-1]).read_text())


def test_committed_index_rows_are_traceable():
    d = latest()
    assert d["schema"] == "cell_akamai.dashboard_evidence_index.v1" and d["rows"]
    for r in d["rows"]:
        assert all(k in r for k in REQ), r
        assert r["evidence_ref"]
        if r["state"].startswith("OBSERVED") and isinstance(r["value"], (int, float)) and not isinstance(r["value"], bool):
            assert r["source_archive"]
    states = {r["state"] for r in d["rows"]}
    assert {"NOT_TESTED", "AFTER_NOT_TESTED", "NOT_COMPUTED"} <= states  # unknowns stay visible
    assert d["claims"]["self_training"] == "NOT_TESTED" and d["claims"]["anticube"] == "NOT_COMPUTED"
    assert all(r["state"] in ("AFTER_NOT_TESTED", "NOT_TESTED", "IMPLEMENTED") for r in d["rows"] if r["experiment_id"] in ("CAKM-M08", "CAKM-M09"))
    assert all(r.get("data_class") == "ECA_DERIVED_FIXTURE" for r in d["rows"] if r["experiment_id"] == "CAKM-SIX-DATASET" and r["run_id"] != "six-all")


def _zip(files, manifest):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for k, v in files.items(): z.writestr(k, v)
        z.writestr("PACKAGE_MANIFEST.json", json.dumps({"files": manifest}))
    return buf.getvalue()


def test_failed_manifest_is_listed_not_ingested(tmp_path, monkeypatch):
    good = b'{"x":1}'
    (tmp_path / "CELL_AKAMAI_EVIDENCE_EXPORT.zip").write_bytes(_zip({"a/experiment_receipt.json": good}, {"a/experiment_receipt.json": "0" * 64}))
    monkeypatch.setattr(I, "OUT_DIR", tmp_path / "out")
    out = I.main(["--archives-dir", str(tmp_path), "--runs", str(tmp_path / "none")])
    d = json.loads(Path(out).read_text())
    src = {s["label"]: s for s in d["sources"]}
    assert src["EVIDENCE_EXPORT"]["manifest_state"] == "FAIL" and not [r for r in d["rows"] if r["experiment_id"].startswith("EXP-AKAMAI")]
    assert src["ALL_EVIDENCE"]["state"] == "NOT_RECOVERED" and src["M08_M09_HANDOFF"]["state"] == "NOT_RECOVERED"


def test_index_versions_are_append_only(tmp_path, monkeypatch):
    monkeypatch.setattr(I, "OUT_DIR", tmp_path / "out")
    a = I.main(["--archives-dir", str(tmp_path), "--runs", str(tmp_path / "none")])
    assert I.main(["--archives-dir", str(tmp_path), "--runs", str(tmp_path / "none")]) == a  # unchanged content: no new version
    (tmp_path / "CELL_AKAMAI_EVIDENCE_EXPORT.zip").write_bytes(_zip({}, {}))
    b = I.main(["--archives-dir", str(tmp_path), "--runs", str(tmp_path / "none")])
    assert Path(a).exists() and Path(b).name.endswith(".v2.json")


def test_prometheus_delta_derivation():
    before = 'vllm:generation_tokens_total{model_name="m"} 100.0\nvllm:time_to_first_token_seconds_sum{model_name="m"} 1.0\nvllm:time_to_first_token_seconds_count{model_name="m"} 10.0\n'
    after = 'vllm:generation_tokens_total{model_name="m"} 168.0\nvllm:time_to_first_token_seconds_sum{model_name="m"} 1.04\nvllm:time_to_first_token_seconds_count{model_name="m"} 11.0\n'
    b, a = I.prom(before), I.prom(after)
    assert a["vllm:generation_tokens_total"] - b["vllm:generation_tokens_total"] == 68.0
    ttft = (a["vllm:time_to_first_token_seconds_sum"] - b["vllm:time_to_first_token_seconds_sum"]) / (a["vllm:time_to_first_token_seconds_count"] - b["vllm:time_to_first_token_seconds_count"])
    assert abs(ttft - 0.04) < 1e-9


def test_dashboard_page_and_routes_exist():
    html = (ROOT / "tools/dashboard/evidence.html").read_text()
    for tab in ("Akamai GPU runs", "Six datasets", "B0–B3 evaluation", "Module 8", "Module 9", "Export comparison report"):
        assert tab in html
    srv = (ROOT / "tools/concurrency/serve_dashboard.py").read_text()
    assert "/evidence.json" in srv and "DASHBOARD_EVIDENCE_INDEX" in srv


def _run_nb(env_archives):
    import os
    import nbformat
    from nbclient import NotebookClient
    nb = nbformat.read(ROOT / "notebooks/85_dashboard_evidence_verify.ipynb", as_version=4)
    os.environ["CELL_AKAMAI_ARCHIVES"] = str(env_archives)
    NotebookClient(nb, timeout=120, kernel_name="python3", resources={"metadata": {"path": str(ROOT / "notebooks")}}).execute()
    return "\n".join(o.get("text", "") for c in nb.cells if c.cell_type == "code" for o in c.outputs)


def test_verification_notebook_without_archives(tmp_path):
    out = _run_nb(tmp_path)
    assert "INDEX DASHBOARD_EVIDENCE_INDEX" in out and "NOT_RECOVERED here" in out and "RECOMPUTATION NOT_TESTED" in out
    assert "PASS" not in out.split("RECOMPUTATION")[-1]  # no PASS without re-derivation
