"""Scaling test, step 3: what the net costs inside strong's search (the architecture thread: time per evaluation
kept apart, for the compute gate's conversion to simulations). Condition: the opponent's deck list is known (order
and hand not).

    python analysis/scaling/timing.py --records RECDIR --net analysis/scaling/models/net-10000.npz

One process, nothing else running. Two readings, both on holdout games (s_h = 70200000 + 2h):
- per evaluation: the installed turn-end model (LinearValue.logit) and the net (SetNet.logit, its encoding
  included) on the same turn-end positions, each timed over all of them several times;
- per decision: v2skx and v2skx+setnet=NET choosing at the same positions (the first main-phase decision of
  turns from the holdout games, the agents' seed fixed), whole act() time, the two in turn at each position, over
  several rounds; the ratio of the sums, and how much of the difference is the net's own time (its calls timed
  inside the search, less what the linear model would have cost for as many calls) and how much is the search
  going elsewhere with another evaluator.
Writes data/timing.json.
"""
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


def main():
    from svsim.core.engine import legal_actions
    from svsim.core.enums import Phase
    from svsim.learn.model import LinearValue
    from svsim.learn.netdata import ENDED, rows
    from svsim.learn.scaledata import SPEC
    from svsim.learn.setnet import load_cached
    from svsim.tools import records as R
    from svsim.tools.arena import make_agent
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", required=True)
    ap.add_argument("--net", required=True)
    ap.add_argument("--games", type=int, default=20)
    ap.add_argument("--decisions", type=int, default=120)
    ap.add_argument("--rounds", type=int, default=3)
    args = ap.parse_args()
    recs = []
    with gzip.open(Path(args.records) / "rec-70200000.jsonl.gz", "rt", encoding="utf-8") as fh:
        for line in fh:
            recs.append(json.loads(line))
            if len(recs) >= args.games:
                break
    ended = [(s, p) for r in recs for ph, p, s, _ in rows(r) if ph == ENDED]
    lin = LinearValue.load(HERE.parents[1] / "svsim/learn/phased_models/ramp-t-ramp-t-ended.json")
    net = load_cached(args.net)
    per_eval = {}
    for name, f in (("installed_linear", lin.logit), ("net", net.logit)):
        for s, p in ended[:20]:
            f(s, p)
        t0 = time.perf_counter()
        for _ in range(5):
            for s, p in ended:
                f(s, p)
        per_eval[name] = round((time.perf_counter() - t0) / (5 * len(ended)) * 1e3, 4)
    starts = []
    for r in recs:
        seen = set()
        for state, action in R.steps(r):
            if state.phase == Phase.MAIN and (state.active, state.turn) not in seen and state.turn >= 3:
                seen.add((state.active, state.turn))
                starts.append(state.clone())
    starts = starts[:args.decisions]
    from svsim.learn import setnet as SN
    spent = {"calls": 0, "s": 0.0}
    plain_logit = SN.SetNet.logit

    def timed(self, state, player):
        t = time.perf_counter()
        v = plain_logit(self, state, player)
        spent["s"] += time.perf_counter() - t
        spent["calls"] += 1
        return v
    SN.SetNet.logit = timed
    specs = {"v2skx": SPEC, "v2skx+setnet": f"{SPEC}+setnet={args.net}"}
    totals = {k: [] for k in specs}
    for _ in range(args.rounds):                      # both agents at each position in turn, several rounds
        t_round = {k: 0.0 for k in specs}
        for i, s in enumerate(starts):
            for name, spec in specs.items():
                agent = make_agent(spec, 1000 + i)
                t0 = time.perf_counter()
                agent.act(s.clone(), legal_actions(s))
                t_round[name] += time.perf_counter() - t0
        for k in specs:
            totals[k].append(t_round[k])
    SN.SetNet.logit = plain_logit
    n = len(starts) * args.rounds
    per_move = {k: round(sum(v) / n * 1e3, 1) for k, v in totals.items()}
    rounds = [round(b / a, 3) for a, b in zip(totals["v2skx"], totals["v2skx+setnet"])]
    net_ms = spent["s"] / n * 1e3
    out = {"turn_end_positions": len(ended), "per_evaluation_ms": per_eval,
           "net_over_linear": round(per_eval["net"] / per_eval["installed_linear"], 2),
           "decisions": len(starts), "per_decision_ms": per_move,
           "decision_ratio": round(per_move["v2skx+setnet"] / per_move["v2skx"], 3), "ratio_by_round": rounds,
           "net_calls_per_decision": round(spent["calls"] / n, 1),
           "net_ms_per_decision": round(net_ms, 1),
           "linear_ms_saved_per_decision": round(spent["calls"] / n * per_eval["installed_linear"], 1),
           "rest_of_difference_ms": round(per_move["v2skx+setnet"] - per_move["v2skx"] - net_ms
                                          + spent["calls"] / n * per_eval["installed_linear"], 1),
           "net": args.net}
    (HERE / "data/timing.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
