"""What one turn-end evaluation costs with the installed model, cand-kc-ramp-ramp and cand-nl-ramp-ramp (the search's
own call: search.evaluate.evaluate on ENDED positions of step-1 self-play), interleaved rounds, median; and what the
difference does to the strongest level's iterations per second (bench.py's rate for the installed search).
Condition: the opponent's deck list is known (order and hand not).
usage: nl_cost.py STEP1_DIR [GAMES] [ROUNDS] [INSTALLED_ITERATIONS_PER_SECOND]"""
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
SPECS = {"installed": "mcts:1043+plan+learned+phased",
         "cand-kc": "mcts:1043+plan+learned+phased=cand-kc-ramp-ramp",
         "cand-nl": "mcts:1043+plan+learned+phased=cand-nl-ramp-ramp"}


def main():
    d = sys.argv[1]
    games = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    rounds = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    rate = float(sys.argv[4]) if len(sys.argv) > 4 else 2137.0
    sys.path.insert(0, f"{d}/ana")
    import student_data as SD
    from svsim.learn.netdata import ENDED, rows
    from svsim.search.evaluate import evaluate
    from svsim.tools.arena import make_agent
    from svsim.tools.gate import _search
    recs = list(SD._lines(f"{d}/selfplay.jsonl"))[:games]
    ends = [(st, me) for rec in recs for ph, me, st, res in rows(rec) if ph == ENDED]
    W = {n: _search(make_agent(s, 0)).weights for n, s in SPECS.items()}
    for w in W.values():                               # warm the caches (card measurements, role sums)
        for st, me in ends:
            evaluate(st, me, w, False)
    times = {n: [] for n in W}
    for _ in range(rounds):
        for n, w in W.items():
            t = time.perf_counter()
            for st, me in ends:
                evaluate(st, me, w, False)
            times[n].append(1e6 * (time.perf_counter() - t) / len(ends))
    us = {n: round(statistics.median(v), 1) for n, v in times.items()}
    per_it = 1e6 / rate
    out = {"turn ends": len(ends), "us per evaluation (median)": us,
           "installed iterations per second (bench.py)": rate,
           "iterations per second if only the evaluation changes": {
               n: round(1e6 / (per_it + us[n] - us["installed"])) for n in us},
           "change": {n: f"{100 * (per_it / (per_it + us[n] - us['installed']) - 1):+.1f}%" for n in us}}
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
