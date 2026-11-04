"""What +puct costs per decision (the architecture thread 2026-10-17, "B": equal-compute N for a gate).

On recorded positions (a held-out shard's searched decisions, learn.setpolicy.decisions; no game is played, so no
seed is drawn), each spec's agent (a fresh make_agent(spec, 0) per position) decides once; the specs take turns
position by position, so a drift of the machine falls on all of them alike. The wall time of agent.act per decision
is averaged per spec.

    python analysis/scaling/puct_cost.py --records REC --games 10 --spec NAME=SPEC ... --out OUT
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))

from svsim.learn import setpolicy as SP  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--records", required=True)
    ap.add_argument("--games", type=int, default=10)
    ap.add_argument("--spec", action="append", required=True, metavar="NAME=SPEC")
    ap.add_argument("--out", required=True)
    ap.add_argument("--deck", default=None, help="only the decisions of the side playing this deck (a non-mirror "
                                                "pairing's side; default every decision)")
    args = ap.parse_args()
    from svsim.core.engine import legal_actions
    from svsim.learn.netdata import _search
    from svsim.tools.arena import make_agent
    specs = [s.split("=", 1) for s in args.spec]
    for _, spec in specs:                                 # load every net once before timing
        make_agent(spec, 0)
    total = {name: 0.0 for name, _ in specs}
    iters = {name: 0 for name, _ in specs}
    n = 0
    with gzip.open(args.records, "rt") as fh:
        for g, line in enumerate(fh):
            if g >= args.games:
                break
            rec = json.loads(line)
            for i, state, legal, reps, group, pi, start in SP.decisions(rec):
                if args.deck and state.players[state.active].deck_name != args.deck:
                    continue
                order = specs[n % len(specs):] + specs[:n % len(specs)]
                for name, spec in order:
                    agent = make_agent(spec, 0)
                    s = state.clone()
                    t0 = time.perf_counter()
                    agent.act(s, legal_actions(s))
                    total[name] += time.perf_counter() - t0
                    search = _search(agent)
                    iters[name] += search.last_iterations or 0
                n += 1
    out = {"records": Path(args.records).name, "games": args.games, "deck": args.deck, "decisions": n,
           "specs": {name: {"spec": spec, "ms_per_decision": round(1e3 * total[name] / n, 2),
                            "iterations_per_decision": round(iters[name] / n, 1)} for name, spec in specs}}
    Path(args.out).write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
