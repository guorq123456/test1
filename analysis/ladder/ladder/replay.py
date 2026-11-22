"""Replaying a logged game (phase 1, 重放检查).

    python -m ladder.replay games.jsonl [--sample 20] [--seed S] [--decisions]

Two checks, both must hold on the machine and Python the games ran on (ENVIRONMENT 9.4):
- moves: a fresh game from the log's seed, decks and first player, the logged moves applied one by one; every move
  must be legal when it comes and the game must end the same way;
- decisions (--decisions): the same strategies, rebuilt from their specs and seeds, play the game again; every
  decision must be the logged one.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))      # the repository root (svsim)
from ladder.runner import load_deck, play_job  # noqa: E402


def replay_moves(log: dict) -> tuple[bool, str]:
    from svsim.core.actions import from_dict
    from svsim.core.engine import apply, legal_actions
    from ladder import deal
    if log.get("result") in ("timeout", "void") or "actions" not in log:
        return True, "skipped (no full move list)"
    _, state = deal.start(log)                              # the keyed deal the log carries (base-2), if any
    if state.first != log.get("first"):
        return False, f"first player {state.first} != logged {log.get('first')}"
    for i, data in enumerate(log["actions"]):
        a = from_dict(data)
        if a not in legal_actions(state):
            return False, f"move {i} not legal on replay: {data}"
        apply(state, a)
    if log["result"] in ("normal", "draw"):
        winner = state.winner if state.winner in (0, 1) else None
        if winner != log["winner"]:
            return False, f"winner {winner} != logged {log['winner']}"
        if not state.over:
            return False, "game not over after the logged moves"
    return True, "ok"


def replay_decisions(log: dict) -> tuple[bool, str]:
    if log.get("result") in ("timeout", "void"):
        return True, "skipped"
    job = {k: log[k] for k in ("id", "seed", "decks", "strategies", "strategy_seeds")}
    job["deal"] = log.get("deal")
    job["first"] = log.get("first_arg")
    again = json.loads(json.dumps(play_job(job)))          # the same JSON shapes as the log (tuples -> lists)
    for i, (a, b) in enumerate(zip(again["actions"], log["actions"])):
        if a != b:
            return False, f"decision {i} differs: {a} vs logged {b}"
    if len(again["actions"]) != len(log["actions"]) or again["result"] != log["result"] \
            or again["winner"] != log["winner"]:
        return False, f"ended differently: {again['result']}/{again['winner']} vs {log['result']}/{log['winner']}"
    return True, "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log")
    ap.add_argument("--sample", type=int, default=0, help="check this many random games (0: all)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--decisions", action="store_true")
    a = ap.parse_args()
    logs = [json.loads(l) for l in Path(a.log).read_text(encoding="utf-8").splitlines() if l.strip()]
    if a.sample:
        logs = random.Random(a.seed).sample(logs, min(a.sample, len(logs)))
    bad = 0
    for log in logs:
        ok, why = replay_moves(log)
        if ok and a.decisions:
            ok, why = replay_decisions(log)
        if not ok:
            bad += 1
            print(f"{log['id']}: {why}")
    print(json.dumps({"checked": len(logs), "failed": bad}))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
