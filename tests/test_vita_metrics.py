"""Synthetic fixture tests; these do not represent real service measurements."""
import hashlib
import json

import pytest

from tools.concurrency.vita_metrics import (
    atomic_write_json,
    checkpoint_sha256,
    merkle_root,
    throughput,
    throughput_acceleration,
    verify_checkpoint,
)


def test_synthetic_fixture_throughput_and_validation():
    assert throughput(120, 4) == 30
    for count, duration in [(-1, 1), (1, 0), (1, -1), (float("nan"), 1), (1, float("inf"))]:
        with pytest.raises(ValueError):
            throughput(count, duration)


def test_synthetic_fixture_signed_acceleration_and_time_validation():
    assert throughput_acceleration(10, 1, 4, 4) == -2
    assert throughput_acceleration(4, 1, 10, 4) == 2
    for args in [(1, 2, 3, 2), (1, 3, 3, 2), (1, 0, float("inf"), 2)]:
        with pytest.raises(ValueError):
            throughput_acceleration(*args)


def test_synthetic_fixture_merkle_odd_tree_and_tampering():
    receipts = [{"id": "fixture-a", "n": 1}, {"n": 2, "id": "fixture-b"}, {"id": "fixture-c", "n": 3}]
    leaves = [hashlib.sha256(b"\x00" + json.dumps(r, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest() for r in receipts]
    parent1 = hashlib.sha256(b"\x01" + (leaves[0] + leaves[1]).encode("ascii")).hexdigest()
    parent2 = hashlib.sha256(b"\x01" + (leaves[2] + leaves[2]).encode("ascii")).hexdigest()
    expected = hashlib.sha256(b"\x01" + (parent1 + parent2).encode("ascii")).hexdigest()
    assert merkle_root(receipts) == expected
    changed = [*receipts[:2], {"id": "fixture-c", "n": 4}]
    assert merkle_root(changed) != expected
    with pytest.raises(ValueError):
        merkle_root([])


def test_synthetic_fixture_checkpoint_streaming_verification_and_tamper(tmp_path):
    checkpoint = tmp_path / "fixture-checkpoint.bin"
    content = b"synthetic-checkpoint-" * 1000
    checkpoint.write_bytes(content)
    expected = hashlib.sha256(content).hexdigest()
    assert checkpoint_sha256(checkpoint, chunk_size=17) == expected
    assert verify_checkpoint(checkpoint, "sha256:" + expected, chunk_size=13)
    checkpoint.write_bytes(content + b"tampered")
    assert not verify_checkpoint(checkpoint, expected, chunk_size=11)
    with pytest.raises(ValueError):
        verify_checkpoint(checkpoint, "not-a-digest")


def test_synthetic_fixture_atomic_json_strictness_and_old_file_preservation(tmp_path):
    target = tmp_path / "nested" / "receipt.json"
    atomic_write_json(target, {"fixture": True, "value": 2})
    original = target.read_bytes()
    assert json.loads(original) == {"fixture": True, "value": 2}
    assert original.endswith(b"\n")
    with pytest.raises(ValueError):
        atomic_write_json(target, {"invalid": float("nan")})
    assert target.read_bytes() == original
    assert list(target.parent.iterdir()) == [target]
