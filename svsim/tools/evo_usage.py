"""When each side spends its evolution points over a game (the player's yardstick, 2026-10-07).

    python -m svsim.tools.evo_usage games.jsonl [more.jsonl ...] [--spec SPEC] [--min-turns N]

The player: the bot spends its evolution and super-evolution points as soon as it can and, in the long
games, has none left when they would matter. Per game and side, replaying the record: the own turn
(turns_taken) in which each of the four points (2 evolution, 2 super-evolution) was spent; the own turn
the last of them went; the turns between the first and the last; the points still held at the start of
own turn 8; the points never used. `--spec` keeps only the seats whose agent spec (record["ai"],
"seat 0 / seat 1") is SPEC; `--min-turns` only games that lasted that many own turns (long games).
The player's own numbers (their games against the bot): the fourth point at own turn 9.5 on average,
4.8 turns from the first to the last.
"""
from __future__ import annotations

import argparse
import gzip
import json


def usage(record: dict) -> list[dict]:
    """For each seat: {"spent": [own turn of each point spent], "held_at_8": points at the start of own turn
    8 (None if the game ended sooner), "left": points never used, "turns": own turns played}."""
    from svsim.core.enums import Phase
    from svsim.tools import records as R
    out = [{"spent": [], "held_at_8": None, "left": 0, "turns": 0} for _ in (0, 1)]
    last = None
    state = None
    for state, action in R.steps(record):
        for side in (0, 1):
            p = state.players[side]
            if out[side]["held_at_8"] is None and p.turns_taken >= 8 and state.active == side \
                    and state.phase == Phase.MAIN:
                out[side]["held_at_8"] = p.ep + p.sep
        now = [(p.ep, p.sep, p.turns_taken) for p in state.players]
        if last is not None:
            for side in (0, 1):
                spent = max(0, last[side][0] - now[side][0]) + max(0, last[side][1] - now[side][1])
                out[side]["spent"] += [now[side][2]] * spent
        last = now
    if state is not None:
        for side in (0, 1):
            p = state.players[side]
            out[side]["left"] = p.ep + p.sep
            out[side]["turns"] = p.turns_taken
    return out


def _open(path: str):
    return gzip.open(path, "rt", encoding="utf-8") if path.endswith(".gz") else open(path, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("games", nargs="+")
    parser.add_argument("--spec", default=None, help="only the seats played by this agent spec")
    parser.add_argument("--min-turns", type=int, default=0)
    args = parser.parse_args()
    rows = []
    for path in args.games:
        for line in _open(path):
            record = json.loads(line)
            specs = [x.strip() for x in str(record.get("ai", "")).split("/")]
            for side, u in enumerate(usage(record)):
                if args.spec is not None and (len(specs) != 2 or specs[side] != args.spec):
                    continue
                if u["turns"] < args.min_turns:
                    continue
                rows.append(u)
    if not rows:
        print("no seats")
        return
    mean = lambda xs: sum(xs) / len(xs) if xs else float("nan")
    full = [u for u in rows if len(u["spent"]) >= 4]
    fourth = mean([u["spent"][3] for u in full])
    spread = mean([u["spent"][3] - u["spent"][0] for u in full])
    held8 = [u["held_at_8"] for u in rows if u["held_at_8"] is not None]
    print(f"{len(rows)} seats ({len(full)} spent all four points)")
    print(f"fourth point at own turn {fourth:.2f}; first to fourth {spread:.2f} turns")
    print(f"points held at the start of own turn 8: {mean(held8):.2f} ({len(held8)} seats that got there)")
    print(f"points never used: {mean([u['left'] for u in rows]):.2f}")
    by = {}
    for u in rows:
        for t in u["spent"]:
            by[t] = by.get(t, 0) + 1
    print("points spent by own turn: " + ", ".join(f"{t}: {by[t] / len(rows):.2f}" for t in sorted(by)))


if __name__ == "__main__":
    main()
