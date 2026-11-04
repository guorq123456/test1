"""Time per decision in real games (the architecture thread 2026-10-20 13:54Z: the install N is set from whole games
played in the page's runtime, not from recorded positions). For each seed, each pair of specs plays one game
(learn.netdata.play, job (0, seed, deck, opponent, spec, 0.0, ..., opponent's spec): deal seed seed*100003, `deck` in
seat 0); the pairs take turns seed by seed in a rotating order, so a drift of the machine falls on all of them alike.
The wall time of every agent.act is summed per pair and per deck. Timing only: the result is not read.

    python analysis/scaling/selfplay_time.py --deck D --opponent O --seeds S ... --pair NAME=SPEC_D[|SPEC_O] ... --out OUT
"""
from __future__ import annotations

import argparse
import json
import time


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", required=True)
    ap.add_argument("--opponent", required=True)
    ap.add_argument("--seeds", type=int, nargs="+", required=True)
    ap.add_argument("--pair", action="append", required=True, metavar="NAME=SPEC_DECK[|SPEC_OPPONENT]")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    from svsim.learn import netdata
    from svsim.tools import arena
    pairs = []
    for item in args.pair:
        name, specs = item.split("=", 1)
        a, _, b = specs.partition("|")
        pairs.append((name, a, b or a))
    make = arena.make_agent
    seats: list = []                                   # (pair name, deck) of each agent made, in seat order

    def timed(spec, seed):
        agent = make(spec, seed)
        key = seats[len(made)]
        made.append(key)
        act = agent.act

        def wrapped(state, *a, **k):
            t = time.perf_counter()
            out = act(state, *a, **k)
            row = totals[key[0]][key[1]]
            row["ms"] += (time.perf_counter() - t) * 1000.0
            row["decisions"] += 1
            return out
        agent.act = wrapped
        return agent

    totals = {name: {d: {"ms": 0.0, "decisions": 0} for d in (args.deck, args.opponent)} for name, _, _ in pairs}
    games = {name: [] for name, _, _ in pairs}
    arena.make_agent = timed
    try:
        for k, seed in enumerate(args.seeds):
            for name, a, b in pairs[k % len(pairs):] + pairs[:k % len(pairs)]:
                seats[:] = [(name, args.deck), (name, args.opponent)]
                made: list = []
                t = time.perf_counter()
                rec = netdata.play((0, seed, args.deck, args.opponent, a, 0.0, 0.0, False, None, None, b))
                games[name].append({"seed": seed, "s": round(time.perf_counter() - t, 1), "turns": rec.get("turns"),
                                    "actions": len(rec["actions"])})
                print(name, seed, games[name][-1], flush=True)
    finally:
        arena.make_agent = make
    out = {"deck": args.deck, "opponent": args.opponent, "seeds": args.seeds,
           "pairs": {name: {"specs": {args.deck: a, args.opponent: b}, "games": games[name],
                            "decks": {d: dict(r, ms=round(r["ms"], 1),
                                              ms_per_decision=round(r["ms"] / max(r["decisions"], 1), 2))
                                      for d, r in totals[name].items()}}
                     for name, a, b in pairs}}
    with open(args.out, "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({n: {d: r["ms_per_decision"] for d, r in p["decks"].items()} for n, p in out["pairs"].items()}))


if __name__ == "__main__":
    main()
