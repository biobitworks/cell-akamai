import copy
from cell_akamai.kinetics import enrich_observations, verify_kinetics, content_digest
from cell_akamai.prometheus import parse_metrics, single_metric
from cell_akamai.custody import make_fco, make_edge


def test_throughput_and_midpoint_acceleration():
    rows = [
        {"started_mono_ns": 1_000_000_000, "ended_mono_ns": 3_000_000_000,
         "completion_tokens": 20, "first_content_mono_ns": 1_500_000_000},
        {"started_mono_ns": 4_000_000_000, "ended_mono_ns": 6_000_000_000,
         "completion_tokens": 40, "first_content_mono_ns": 4_250_000_000},
    ]
    result = enrich_observations(rows)
    assert result[0]["tokens_per_s"] == 10
    assert result[1]["tokens_per_s"] == 20
    assert result[0]["tokens_per_s2_inter_request"] is None
    assert abs(result[1]["tokens_per_s2_inter_request"] - 10/3) < 1e-12
    assert result[0]["ttfc_s"] == 0.5
    assert verify_kinetics(result)["status"] == "PASS"
    bad = copy.deepcopy(result)
    bad[1]["tokens_per_s2_inter_request"] = 999
    assert verify_kinetics(bad)["status"] == "FAILED"


def test_missing_usage_and_bad_clocks_preserve_null():
    result = enrich_observations([{"started_mono_ns": 4, "ended_mono_ns": 1, "completion_tokens": None}])
    assert result[0]["tokens_per_s"] is None
    assert result[0]["tokens_per_s2_inter_request"] is None


def test_prometheus_sample_units_and_labels():
    raw = '''# HELP vllm:kv_cache_usage_perc KV cache usage
vllm:kv_cache_usage_perc{model_name="Qwen/Qwen3-4B"} 0.75
vllm:num_requests_running{model_name="Qwen/Qwen3-4B"} 2.0
vllm:generation_tokens_total{model_name="Qwen/Qwen3-4B"} 124.0
'''
    parsed = parse_metrics(raw)
    assert single_metric(parsed, "vllm:kv_cache_usage_perc", "Qwen/Qwen3-4B") == .75
    assert single_metric(parsed, "vllm:num_requests_running", "Qwen/Qwen3-4B") == 2
    assert single_metric(parsed, "vllm:generation_tokens_total", "Qwen/Qwen3-4B") == 124


def test_fco_content_and_occurrence_identity():
    a = make_fco("Evidence", {"value": 3}, {"project": "x", "event": 1})
    b = make_fco("Evidence", {"value": 3}, {"project": "x", "event": 2})
    assert a["content_id"] == b["content_id"]
    assert a["occurrence_id"] != b["occurrence_id"]
    assert make_edge(a,b,"derived_from")["semantics"] == "DECLARED_NOT_CAUSAL"
