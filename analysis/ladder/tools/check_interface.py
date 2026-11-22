"""Item 2.1's acceptance on more games: the default strategy through the interface (ladder.interface.PlayerStrategy
with nothing overridden, and with every hook written out) against the default strategy itself (strategy.BotStrategy),
decision for decision, over `--games` games of the seven baseline lists (every ordered pair of classes in turn).

    python tools/check_interface.py [--games 40] [--out probe/interface-check-DATE.json]

Seeds 99001520-99001599 (host probe bank, SEEDS.md), one per game.
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE.parents[2]), str(HERE.parent / "tests")]

from test_interface import DECKS, LINES, Explicit, record  # noqa: E402
from ladder.interface import PlayerStrategy  # noqa: E402
from ladder.strategy import BotStrategy  # noqa: E402

SEEDS = (99001520, 99001600)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=40)
    ap.add_argument("--out")
    a = ap.parse_args()
    pairs = [p for p in itertools.permutations(range(len(DECKS)), 2)]
    rows, t0 = [], time.time()
    for g in range(min(a.games, SEEDS[1] - SEEDS[0])):
        da, db = pairs[g % len(pairs)]
        seed = SEEDS[0] + g
        ref = record(da, db, [BotStrategy(seed=2 * seed), BotStrategy(seed=2 * seed + 1)], seed)
        plain = record(da, db, [PlayerStrategy(seed=2 * seed), PlayerStrategy(seed=2 * seed + 1)], seed)
        expl = record(da, db, [BotStrategy(seed=2 * seed), Explicit(seed=2 * seed + 1)], seed)
        first_diff = next((i for i, (x, y) in enumerate(zip(ref[1], plain[1])) if x != y), None)
        rows.append({"seed": seed, "decks": [LINES[da][0], LINES[db][0]], "decisions": len(ref[1]),
                     "plain_same": plain == ref, "explicit_same": expl == ref, "first_difference": first_diff})
        print(json.dumps(rows[-1]), file=sys.stderr, flush=True)
    out = {"games": len(rows), "decisions": sum(r["decisions"] for r in rows),
           "plain_same": sum(r["plain_same"] for r in rows), "explicit_same": sum(r["explicit_same"] for r in rows),
           "seconds": round(time.time() - t0), "machine": "cloud container", "rows": rows}
    text = json.dumps(out, ensure_ascii=False, indent=1)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
