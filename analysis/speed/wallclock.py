"""Wall clock per decision for several specs on the same positions (the architecture thread 2026-10-10 14:36Z): the
whole agent's act (lethal check included) on the first move of the first N step-1 training starts (bench.py's), the
same seed per position; R rounds, the specs in alternating order, median of the rounds' totals. Also the search's
iterations per decision. Run from each checkout to compare code versions.
Condition: the opponent's deck list is known (order and hand not).
usage: wallclock.py STEP1_DIR OUT.json ROUNDS SPEC [SPEC ...]"""
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def main():
    d, out, rounds, specs = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4:]
    sys.path.insert(0, f"{d}/ana")
    import student_data as SD
    from svsim.core.engine import legal_actions
    from svsim.tools.arena import make_agent
    from svsim.tools.gate import _search
    games = {r["g"]: r for r in SD._lines(f"{d}/selfplay.jsonl")}
    starts = [r for r in SD._lines(f"{d}/starts.jsonl") if r["split"] == "train"][:30]
    states = [SD._state_at(games[r["game"]], r["at"]) for r in starts]
    states = [s for s in states if len(legal_actions(s)) > 1]
    ms = {s: [] for s in specs}
    its = {}
    for rd in range(rounds + 1):                       # round 0 warms the caches, not counted
        for spec in (specs if rd % 2 == 0 else specs[::-1]):
            tot, it = 0.0, 0
            for i, s in enumerate(states):
                agent = make_agent(spec, i)
                search = _search(agent)
                search.last_iterations = None
                t = time.perf_counter()
                agent.act(s.clone(), legal_actions(s))
                tot += time.perf_counter() - t
                it += search.last_iterations or 0
            if rd:
                ms[spec].append(1000 * tot / len(states))
                its[spec] = it / len(states)
    res = {s: {"ms per decision (median)": round(statistics.median(v), 1), "rounds": [round(x, 1) for x in v],
               "iterations per decision": round(its[s], 1)} for s, v in ms.items()}
    Path(out).write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
