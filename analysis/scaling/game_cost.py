"""Time per decision of one side's specs through whole recorded games (N₀ for a non-mirror gate; the analysis line
2026-10-19 05:28Z: NM1's per-position N₀ was about 5% off each way against the gates' whole-game timing).

On recorded games (no game is played, so no seed is drawn), each spec plays the chosen side's every main-phase step
with one agent per game (make_agent(spec, side)), so what an agent keeps between its decisions is kept as in a game:
the lethal check's stamp, a reused tree, search.xprune's memory. The game goes on by the recorded moves. The specs
take turns game by game, in a rotating order, so a drift of the machine falls on all of them alike. The wall time of
agent.act is summed per spec.

    python analysis/scaling/game_cost.py --records REC [REC ...] --games 30 --deck ramp-t --spec NAME=SPEC ... --out OUT
"""
from __future__ import annotations

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import argparse  # noqa: E402
import gzip      # noqa: E402
import json      # noqa: E402
import sys       # noqa: E402
import time      # noqa: E402
from pathlib import Path  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--records", nargs="+", required=True)
    ap.add_argument("--games", type=int, default=30, help="the first this many games of each records file")
    ap.add_argument("--deck", required=True, help="the side timed: the one playing this deck")
    ap.add_argument("--spec", action="append", required=True, metavar="NAME=SPEC")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    from svsim.core.engine import legal_actions
    from svsim.core.enums import Phase
    from svsim.tools import records as R
    from svsim.tools.arena import make_agent
    specs = [s.split("=", 1) for s in args.spec]
    for _, spec in specs:                                 # load every net once before timing
        make_agent(spec, 0)
    total = {name: 0.0 for name, _ in specs}
    n = {name: 0 for name, _ in specs}
    games = 0
    for path in args.records:
        with gzip.open(path, "rt") as fh:
            for g, line in enumerate(fh):
                if g >= args.games:
                    break
                rec = json.loads(line)
                side = rec["names"].index(args.deck)
                states = [s.clone() for s, _a in R.steps(rec) if s.phase == Phase.MAIN and s.active == side]
                order = specs[games % len(specs):] + specs[:games % len(specs)]
                for name, spec in order:
                    agent = make_agent(spec, side)
                    for s in states:
                        st = s.clone()
                        t0 = time.perf_counter()
                        agent.act(st, legal_actions(st))
                        total[name] += time.perf_counter() - t0
                        n[name] += 1
                games += 1
    out = {"records": [Path(p).name for p in args.records], "games": games, "deck": args.deck,
           "decisions": n[specs[0][0]],
           "specs": {name: {"spec": spec, "ms_per_decision": round(1e3 * total[name] / max(n[name], 1), 2)}
                     for name, spec in specs}}
    Path(args.out).write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
