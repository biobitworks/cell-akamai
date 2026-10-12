# CELL-AKAMAI inference evidence

This branch preserves verified source fixtures, evidence recovery tools and an hour-scale evaluation implementation. Short pilot runs are distinct from the planned hour-scale study. No training or performance improvement is established.

Read [execution plan](docs/HOUR_SCALE_EXECUTION_PLAN.md), [experiment](experiments/EXP_001_HOUR_SCALE.md) and [original concurrency runbook](docs/CONCURRENCY_EXECUTION_RUNBOOK.md).

Run deterministic tests (synthetic test metrics are never GPU evidence):

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests/hour_scale tools/recovery/test_package_evidence.py evidence/20261012/successor/tests
```

Run local aggregate-only walkthrough dashboard:

```sh
python3 tools/hour_scale/serve_dashboard.py --snapshot evidence/hour_scale/latest.json --port 8767
```

Private raw response ledgers remain under ignored runs/. Dashboard exposes only whitelisted aggregate fields. Current nonstreaming transport cannot measure TTFT or inter-token latency; those fields remain null. Full matrix and rollout orchestration are pending implementation; do not interpret this branch as completed hour-scale execution.
