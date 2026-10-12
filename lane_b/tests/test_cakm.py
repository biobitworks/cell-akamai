import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "companion"))
import cakm


def test_percentile_nearest_rank():
    assert cakm.percentile([1, 2, 3, 4], 50) == 2 and cakm.percentile([1, 2, 3, 4], 95) == 4
    assert cakm.percentile([], 50) is None and cakm.percentile([None, 5], 50) == 5


def test_kv_bytes_standard_attention_matches_hand_calc():
    mi = {"general.architecture": "qwen3", "qwen3.block_count": 28, "qwen3.attention.head_count_kv": 8,
          "qwen3.attention.key_length": 128, "qwen3.embedding_length": 2048, "qwen3.attention.head_count": 16}
    assert cakm.kv_bytes_per_token(mi) == 2 * 28 * 8 * 128 * 2 == 114688  # 112 KiB/token at f16


def test_kv_unknown_for_hybrid_or_array_metadata():
    mi = {"general.architecture": "lfm2", "lfm2.block_count": 16, "lfm2.attention.head_count_kv": None,
          "lfm2.attention.head_count": 32, "lfm2.embedding_length": 2048}
    assert cakm.kv_bytes_per_token(mi) is None  # never guess


def test_run_concurrent_count_and_order():
    res, wall = cakm.run_concurrent(lambda i: i * i, 10, 3)
    assert res == [i * i for i in range(10)] and wall >= 0
