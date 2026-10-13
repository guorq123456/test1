"""The puzzle bank's scoreboard: Salem's positions (tests/puzzles/<name>/: setup.py with build(seed), answer.json with
the kind, the expected result and the source), each played for our turn by an agent spec on a few seeds.

    python -m svsim.tools.puzzles [--spec S ...] [--seeds 1,2,3] [--bank tests/puzzles] [--only NAME ...]

Per puzzle and seed: solved or not (a "lethal" puzzle: the enemy leader at 0 by the turn's end; a "setup" puzzle: the
answer's expected facts, if it gives any, else "open"), the enemy's defense and our play points left at the end, and
the milliseconds; a summary line per spec. A scoreboard, not a test: the bot failing a puzzle is what the bank is for
(the architecture thread 2026-10-10 02:15Z). Not wired into any level.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / "tests" / "puzzles"


def puzzles(bank: Path = BANK) -> list:
    """[(name, build, answer)] of every puzzle in the bank, by name."""
    tests = str(bank.parent)
    if tests not in sys.path:                 # the setups use tests/helpers.py
        sys.path.insert(0, tests)
    out = []
    for d in sorted(p for p in bank.iterdir() if (p / "setup.py").exists()):
        spec = importlib.util.spec_from_file_location(f"puzzle_{d.name.replace('-', '_')}", d / "setup.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        out.append((d.name, module.build, json.loads((d / "answer.json").read_text(encoding="utf-8"))))
    return out


def facts(state, me: int) -> dict:
    """The end of our turn as the answers state it."""
    p, o = state.players[me], state.players[1 - me]
    return {"won": state.winner == me, "enemy_hp": max(o.leader_hp, 0), "pp_left": p.pp, "hand": len(p.hand),
            "enemy_followers": len(o.followers), "our_hp": p.leader_hp, "ep": p.ep, "sep": p.sep}


def judge(answer: dict, f: dict):
    """True / False against the answer's expected facts ("enemy_hp": exact, "<fact>_at_most" / "_at_least"), or
    None when it expects nothing (an open set-up)."""
    expected = answer.get("expected") or {}
    if not expected:
        return None
    for key, want in expected.items():
        if key.endswith("_at_most"):
            ok = f[key[:-len("_at_most")]] <= want
        elif key.endswith("_at_least"):
            ok = f[key[:-len("_at_least")]] >= want
        else:
            ok = f[key] == want
        if not ok:
            return False
    return True


def play(build, spec: str, seed: int, max_actions: int = 60) -> tuple:
    """Our turn from build(seed) played by `spec`: (the end of the turn, our seat, ms)."""
    from svsim.core.actions import EndTurn
    from svsim.core.engine import apply, legal_actions
    from svsim.search.evaluate import after_end_of_turn
    from svsim.tools.arena import make_agent
    state = build(seed)
    me = state.active
    agent = make_agent(spec, seed)
    t = time.perf_counter()
    for _ in range(max_actions):
        if state.over or state.active != me:
            break
        a = agent.act(state, legal_actions(state))
        if isinstance(a, EndTurn):
            state = after_end_of_turn(state)
            break
        apply(state, a)
    return state, me, (time.perf_counter() - t) * 1000


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--spec", nargs="+", default=["level-strong"])
    parser.add_argument("--seeds", default="1,2,3")
    parser.add_argument("--bank", default=str(BANK))
    parser.add_argument("--only", nargs="*", default=None, help="these puzzles only")
    args = parser.parse_args()
    seeds = [int(x) for x in args.seeds.split(",") if x]
    bank = [p for p in puzzles(Path(args.bank)) if not args.only or p[0] in args.only]
    for spec in args.spec:
        solved = judged = 0
        total_ms = 0.0
        for name, build, answer in bank:
            for seed in seeds:
                end, me, ms = play(build, spec, seed)
                f = facts(end, me)
                verdict = judge(answer, f)
                solved += bool(verdict)
                judged += verdict is not None
                total_ms += ms
                print(json.dumps({"spec": spec, "puzzle": name, "kind": answer["kind"], "seed": seed,
                                  "solved": "open" if verdict is None else verdict, **f, "ms": round(ms)},
                                 ensure_ascii=False), flush=True)
        print(json.dumps({"spec": spec, "summary": f"{solved}/{judged} solved", "puzzles": len(bank),
                          "seeds": seeds, "ms_mean": round(total_ms / max(len(bank) * len(seeds), 1))}), flush=True)


if __name__ == "__main__":
    main()
