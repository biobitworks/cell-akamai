"""Deterministic metrics and custody helpers for Vita runs; unit tests use synthetic fixtures."""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
from typing import Iterable, Mapping, Any


def _finite_number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be a finite number")
    return result


def throughput(count: int | float, duration: int | float) -> float:
    """Return count per second, rejecting invalid counts and durations."""
    count_value = _finite_number(count, "count")
    duration_value = _finite_number(duration, "duration")
    if count_value < 0:
        raise ValueError("count must be nonnegative")
    if duration_value <= 0:
        raise ValueError("duration must be positive")
    return count_value / duration_value


def throughput_acceleration(
    rate1: int | float, midpoint1: int | float,
    rate2: int | float, midpoint2: int | float,
) -> float:
    """Signed change in throughput per second between two time midpoints."""
    r1 = _finite_number(rate1, "rate1")
    t1 = _finite_number(midpoint1, "midpoint1")
    r2 = _finite_number(rate2, "rate2")
    t2 = _finite_number(midpoint2, "midpoint2")
    if r1 < 0 or r2 < 0:
        raise ValueError("rates must be nonnegative")
    if t2 <= t1:
        raise ValueError("midpoints must be strictly increasing")
    return (r2 - r1) / (t2 - t1)


def merkle_root(receipts: list[Mapping[str, Any]]) -> str:
    """Hash canonical JSON receipt leaves and build a duplicate-last Merkle tree."""
    if not receipts:
        raise ValueError("at least one receipt is required")
    level = []
    for receipt in receipts:
        canonical = json.dumps(receipt, sort_keys=True, separators=(",", ":"),
                               ensure_ascii=False, allow_nan=False).encode("utf-8")
        level.append(hashlib.sha256(b"\x00" + canonical).hexdigest())
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        level = [hashlib.sha256(b"\x01" + (level[i] + level[i + 1]).encode("ascii")).hexdigest()
                 for i in range(0, len(level), 2)]
    return level[0]


def checkpoint_sha256(path: str | os.PathLike[str], chunk_size: int = 1024 * 1024) -> str:
    """Compute a checkpoint digest with bounded memory while streaming the file."""
    if isinstance(chunk_size, bool) or not isinstance(chunk_size, int) or chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer")
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_checkpoint(path: str | os.PathLike[str], expected_sha256: str,
                      chunk_size: int = 1024 * 1024) -> bool:
    """Verify a streamed SHA-256, accepting bare hex or a sha256: prefix."""
    if not isinstance(expected_sha256, str):
        raise ValueError("expected_sha256 must be a string")
    expected = expected_sha256.removeprefix("sha256:").lower()
    if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
        raise ValueError("expected_sha256 must be a SHA-256 hex digest")
    return checkpoint_sha256(path, chunk_size) == expected


def atomic_write_json(path: str | os.PathLike[str], value: Any) -> None:
    """Atomically replace path with deterministic strict JSON, preserving old data on failure."""
    target = Path(path)
    payload = json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False,
                         allow_nan=False) + "\n"
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise
