"""Item generation. Matches recovered RUN001 `question()` (numpy default_rng, width 8). NO oracle here."""
import numpy as np

RULES = (30, 90, 110, 184)


def make_item(rule: int, seed: int, width: int = 8) -> dict:
    x = np.random.default_rng(seed).integers(0, 2, size=width, dtype=np.int64)
    return {"item_id": f"ECA-{rule}-{seed}", "rule": rule, "seed": seed, "width": width, "initial_state": x.tolist()}


def make_items(seed_start: int, per_rule: int) -> list[dict]:
    """per_rule items for each rule, consecutive seeds from seed_start (disjoint from calibration 41031-41034)."""
    items, s = [], seed_start
    for rule in RULES:
        for _ in range(per_rule):
            assert s not in (41031, 41032, 41033, 41034)
            items.append(make_item(rule, s))
            s += 1
    return items
