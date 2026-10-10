"""Smoke test after installing "strong + discard pruning" (analysis/install/strong_xprune.py apply): level strong
plays itself for 2 pairs of the original Ramp mirror and 1 pair of 机锋 (nemesis-t) against 旗皇 (pirate-t), with
tools.gate's own game function. Every game must finish, and in the Ramp games the pruning must cut at least one
discard choice. Condition: the opponent's deck list is known (order and hand not).

    python -m svsim.tools.host analysis.install.strong_xprune_smoke --workers 3

Prints one line per game (pairing, seat, result, actions, discard choices cut) and "OK" or "FAILED"; exit 1 on a
failure.
"""
import argparse
import json
import sys

PAIRS = [("ramp", "ramp", 69900001), ("ramp", "ramp", 69900002), ("nemesis-t", "pirate-t", 69900003)]


def _pair(job):
    from svsim.cards import decks
    from svsim.search import xprune
    from svsim.tools import gate
    from svsim.ui.session import DECKS, LEVELS
    deck, opponent, seed = job
    cut = [0]
    real = xprune.XPrune.__call__

    def counted(self, state, action):
        out = real(self, state, action)
        cut[0] += bool(out)
        return out
    xprune.XPrune.__call__ = counted
    spec = "level-strong"
    rows = []
    for seat in (0, 1):
        cut[0] = 0
        mine, theirs = decks.build(DECKS[deck][1]), decks.build(DECKS[opponent][1])
        pts, record = gate._game(mine, theirs, seat, gate._agent(spec, 2 * seed + seat, None),
                                 gate._agent(spec, 2 * seed + 1 - seat + 7919, None), seed,
                                 f"{spec} / {spec}", [deck, opponent])
        rows.append({"pairing": f"{deck} / {opponent}", "seed": seed, "seat": seat, "points": pts,
                     "winner": record.get("winner"), "actions": len(record["actions"]), "cut": cut[0],
                     "strong": LEVELS["strong"]})
    return rows


def main():
    from multiprocessing import Pool
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()
    with Pool(min(args.workers, len(PAIRS))) as pool:
        rows = [r for rs in pool.map(_pair, PAIRS) for r in rs]
    for r in rows:
        print(json.dumps(r, ensure_ascii=False))
    ok = (all(r["winner"] is not None for r in rows) and "xprune" in rows[0]["strong"]
          and sum(r["cut"] for r in rows if r["pairing"] == "ramp / ramp") > 0)
    print("OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
