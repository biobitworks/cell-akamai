import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('idle_queue', Path(__file__).resolve().parents[2] / 'tools/hour_scale/idle_queue.py')
queue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue)


def test_idle_requires_continuous_interval_and_resets_on_other_traffic():
    start, elapsed = queue.idle_duration(None, 100, True)
    assert (start, elapsed) == (100, 0)
    assert queue.idle_duration(start, 159, True) == (100, 59)
    assert queue.idle_duration(start, 160, False) == (None, 0)
    assert queue.idle_duration(None, 161, True) == (161, 0)
    assert queue.idle_duration(161, 221, True) == (161, 60)


def test_missing_activity_cannot_be_treated_as_idle():
    assert not queue.endpoint_idle({})
    assert not queue.endpoint_idle({'running': None, 'waiting': 0})
    assert not queue.endpoint_idle({'running': 0, 'waiting': 1})
    assert queue.endpoint_idle({'running': 0, 'waiting': 0})
