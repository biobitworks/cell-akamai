"""Unmodified raw /metrics bytes are retained by the collector; this module parses only select samples."""
from __future__ import annotations
import re
import math

METRIC_KEYS = (
    "vllm:generation_tokens_total", "vllm:prompt_tokens_total",
    "vllm:kv_cache_usage_perc", "vllm:gpu_cache_usage_perc",
    "vllm:num_requests_running", "vllm:num_requests_waiting",
    "vllm:num_requests_swapped", "vllm:num_preemptions_total",
)
METRIC_RE = re.compile(r'^([a-zA-Z_:][a-zA-Z0-9_:]*)(?:\{([^}]*)\})?\s+([^\s]+)(?:\s|$)')
LABEL_RE = re.compile(r'(\w+)="((?:\\.|[^"])*)"')


def parse_metrics(text: str, select: tuple[str, ...] = METRIC_KEYS) -> list[dict]:
    """Keep labels, distinguish multi-process samples, never silently sum gauges."""
    samples = []
    for line in text.splitlines():
        m = METRIC_RE.match(line)
        if not m or m.group(1) not in select:
            continue
        try:
            value = float(m.group(3))
            if not math.isfinite(value):
                continue
        except ValueError:
            continue
        labels = dict(LABEL_RE.findall(m.group(2) or ""))
        samples.append({"metric": m.group(1), "value": value, "labels": labels})
    return samples


def single_metric(samples: list[dict], key: str, model: str | None = None) -> float | None:
    candidates = [s["value"] for s in samples if s["metric"] == key and (
        model is None or s["labels"].get("model_name", model) == model)]
    return candidates[0] if len(candidates) == 1 else None
