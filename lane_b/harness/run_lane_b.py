#!/usr/bin/env python3
"""Run Lane B arms B0-B3 against an OpenAI-compatible endpoint (Ollama /v1, vLLM, ...).

This script never computes or sees oracle outputs. It writes answers.jsonl and COMMIT.json
(sha256 of answers.jsonl); score_lane_b.py verifies the commit, then scores independently.
Usage: run_lane_b.py CONFIG.json OUT_DIR
"""
import hashlib, json, random, re, sys, time
from pathlib import Path
import requests
sys.path.insert(0, str(Path(__file__).parent))
from items import make_items

ARMS = ["B0_FIXED", "B1_GENESIS", "B2_GENESIS_DAISY", "B3_RANDOM_CONTROL"]
GENESIS_POLICY = "GENESIS_POLICY_PROXY_V0_NOT_THE_RECOVERED_GENESIS_TRANSFORMER"

SYS = "You simulate elementary cellular automata exactly. End with a final line 'ANSWER: <8 bits>' (or 'ANSWER: ABSTAIN')."


def prob(it):
    return (f"Elementary cellular automaton, Wolfram rule {it['rule']}, width 8, periodic (wrap-around) boundary. "
            f"Neighborhood (left,center,right) as a 3-bit number L*4+C*2+R; new cell = bit (that number) of the rule number. "
            f"Current state (index 0..7): {''.join(map(str, it['initial_state']))}. Give the state after ONE step.")


def parse(text):
    m = re.findall(r"ANSWER:\s*([01]{8}|ABSTAIN)", text or "")
    return m[-1] if m else None


def make_chat(cfg):
    def chat(messages):
        t0 = time.monotonic()
        r = requests.post(cfg["base_url"].rstrip("/") + "/chat/completions", timeout=cfg.get("timeout_s", 300),
                          headers={"Authorization": "Bearer " + cfg.get("api_key_env_value", "none")},
                          json={"model": cfg["model"], "messages": messages, "temperature": cfg["temperature"],
                                "seed": cfg["decode_seed"], "max_tokens": cfg["max_tokens_per_call"]})
        dt = time.monotonic() - t0
        r.raise_for_status()
        j = r.json()
        text = j["choices"][0]["message"].get("content") or ""
        usage = (j.get("usage") or {}).get("completion_tokens")  # None if absent; never inferred
        return text, usage, dt
    return chat


def call(chat, rec, user):
    text, usage, dt = chat([{"role": "system", "content": SYS}, {"role": "user", "content": user}])
    rec["calls"].append({"completion_tokens": usage, "wall_s": dt, "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                         "text": text})
    return text


def run_item(arm, it, chat, cfg):
    rec = {"item_id": it["item_id"], "arm": arm, "calls": []}
    p = prob(it)
    if arm == "B0_FIXED":
        ans = [parse(call(chat, rec, p))]
    elif arm == "B1_GENESIS":  # 3 independent derivations (distinct prompt variants), majority vote
        v = [p, p + " Work cell by cell, listing each neighborhood.", p + " Verify by recomputing the table of the rule first."]
        ans = [parse(call(chat, rec, x)) for x in v]
    else:  # B2 / B3: answer, challenge, adjudicate (identical call count and schedule)
        a1 = parse(call(chat, rec, p))
        if arm == "B2_GENESIS_DAISY":  # informed, oracle-free challenge
            c = call(chat, rec, p + f" A candidate answer is {a1}. Independently find any cell that is wrong and give the corrected state.")
        else:  # randomized uninformative challenge: seeded cell index, no information about correctness
            rng = random.Random(f"{cfg['decode_seed']}-{it['item_id']}")
            c = call(chat, rec, p + f" A candidate answer is {a1}. Please re-check cell {rng.randrange(8)} and restate the full state.")
        a2 = parse(c)
        adj = parse(call(chat, rec, p + f" Two candidate answers: A={a1}, B={a2}. Pick the correct one by recomputing; reply 'ANSWER: <8 bits>'."))
        ans = [adj]
    valid = [a for a in ans if a]
    final = sorted(valid, key=lambda a: (-valid.count(a), a))[0] if valid else None  # majority; deterministic tie-break
    toks = [c["completion_tokens"] for c in rec["calls"]]
    rec.update({"final_answer": final, "tokens_total": None if None in toks else sum(toks),
                "wall_s_total": sum(c["wall_s"] for c in rec["calls"]), "n_calls": len(rec["calls"]),
                "over_budget": bool(None not in toks and sum(toks) > cfg["item_token_cap"])
                or len(rec["calls"]) > cfg["item_call_cap"]})
    return rec


def main(cfg_path, out, chat=None):
    cfg = json.loads(Path(cfg_path).read_text())
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    chat = chat or make_chat(cfg)
    items = make_items(cfg["seed_start"], cfg["per_rule"])
    (out / "items.jsonl").write_text("".join(json.dumps(i, sort_keys=True) + "\n" for i in items))
    with open(out / "answers.jsonl", "w") as f:
        for arm in ARMS:
            for it in items:
                try:
                    rec = run_item(arm, it, chat, cfg)
                except Exception as e:  # failures are retained, not dropped
                    rec = {"item_id": it["item_id"], "arm": arm, "calls": [], "final_answer": None, "failure": type(e).__name__,
                           "tokens_total": None, "wall_s_total": 0.0, "n_calls": 0, "over_budget": False}
                f.write(json.dumps(rec, sort_keys=True) + "\n")
    sha = hashlib.sha256((out / "answers.jsonl").read_bytes()).hexdigest()
    (out / "COMMIT.json").write_text(json.dumps({"answers_sha256": sha, "config_sha256": hashlib.sha256(Path(cfg_path).read_bytes()).hexdigest(),
                                                "genesis_policy": GENESIS_POLICY, "oracle_accessed": False}, indent=2))
    print("answers committed", sha)


if __name__ == "__main__":
    main(*sys.argv[1:3])
