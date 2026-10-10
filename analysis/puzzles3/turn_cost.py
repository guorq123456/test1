"""Compute check for +alloc=complex against level-strong on fixed positions: whole turns played from the first N
step-1 turn starts (6f11111, the Ramp mirror's own distribution of simple and complex turns) by both specs, the
same start and seed, alternating which goes first; total ms and total iterations of the search's decisions.
usage: turn_cost.py STEP1_DIR SPEC_A [N] [SPEC_B]"""
import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2])); sys.path.insert(0, sys.argv[1] + "/ana")
import student_data as SD
from svsim.core.engine import apply, legal_actions
from svsim.tools.arena import make_agent
from svsim.tools.gate import _search


def main():
    d, A = sys.argv[1], sys.argv[2]
    N = int(sys.argv[3]) if len(sys.argv) > 3 else 200
    B = sys.argv[4] if len(sys.argv) > 4 else "level-strong"
    games = {r["g"]: r for r in SD._lines(f"{d}/selfplay.jsonl")}
    starts = list(SD._lines(f"{d}/starts.jsonl"))[:N]
    tot = {A: [0.0, 0], B: [0.0, 0]}
    for i, r in enumerate(starts):
        for spec in ((A, B) if i % 2 == 0 else (B, A)):
            s = SD._state_at(games[r["game"]], r["at"])
            me, agent = s.active, make_agent(spec, 5000 + i)
            search = _search(agent)
            while not s.over and s.active == me:
                legal = legal_actions(s)
                search.last_iterations = None
                t = time.perf_counter()
                a = agent.act(s, legal)
                if search.last_iterations is not None:
                    tot[spec][0] += time.perf_counter() - t
                    tot[spec][1] += search.last_iterations
                apply(s, a)
    print(json.dumps({"starts": len(starts), "ms A/B": round(tot[A][0] / tot[B][0], 3),
                      "iterations A/B": round(tot[A][1] / tot[B][1], 3),
                      "ms per turn A / B": [round(1000 * tot[A][0] / len(starts), 1), round(1000 * tot[B][0] / len(starts), 1)]}))


if __name__ == "__main__":       # +par's workers are spawned and import this module
    main()
