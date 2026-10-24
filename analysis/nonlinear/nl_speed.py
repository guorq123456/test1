"""Search speed with each turn-end model: ISMCTS.choose's iterations per second on the first move of the first N
step-1 training starts (as analysis/speed/bench.py), for the installed model, cand-kc-ramp-ramp and cand-nl-ramp-ramp,
the same seeds, R alternating rounds, median. The iteration count is fixed (mcts:N), so the rate is what the
strongest level (mcts:1043, the same evaluation) loses or keeps at equal wall clock.
Condition: the opponent's deck list is known (order and hand not).
usage: nl_speed.py STEP1_DIR [N_STARTS] [ROUNDS] [ITERATIONS]"""
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def main():
    d = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    rounds = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    it = int(sys.argv[4]) if len(sys.argv) > 4 else 200
    sys.path.insert(0, f"{d}/ana")
    import student_data as SD
    from svsim.core.engine import legal_actions
    from svsim.tools.arena import make_agent
    from svsim.tools.gate import _search
    specs = {"installed": f"mcts:{it}+plan+learned+phased",
             "cand-kc": f"mcts:{it}+plan+learned+phased=cand-kc-ramp-ramp",
             "cand-nl": f"mcts:{it}+plan+learned+phased=cand-nl-ramp-ramp"}
    games = {r["g"]: r for r in SD._lines(f"{d}/selfplay.jsonl")}
    starts = [r for r in SD._lines(f"{d}/starts.jsonl") if r["split"] == "train"][:n]
    states = [SD._state_at(games[r["game"]], r["at"]) for r in starts]
    states = [s for s in states if len(legal_actions(s)) > 1]
    rate = {k: [] for k in specs}
    order = list(specs)
    for rd in range(rounds + 1):                      # round 0 warms the caches and isn't counted
        for name in (order if rd % 2 == 0 else order[::-1]):
            its = secs = 0.0
            for i, s in enumerate(states):
                search = _search(make_agent(specs[name], i))
                t = time.perf_counter()
                search.choose(s.clone())
                secs += time.perf_counter() - t
                its += search.last_iterations
            if rd:
                rate[name].append(its / secs)
    med = {k: round(statistics.median(v)) for k, v in rate.items()}
    print(json.dumps({"positions": len(states), "iterations": it,
                      "iterations per second (median)": med,
                      "rounds": {k: [round(x) for x in v] for k, v in rate.items()},
                      "vs installed": {k: f"{100 * (v / med['installed'] - 1):+.1f}%" for k, v in med.items()}},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
