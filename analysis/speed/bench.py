"""Search speed on step 1's turn starts (RC 6f11111): level-strong's search (mcts:200+plan+learned+phased) chooses
the first move at each of the first N training starts; iterations per second of ISMCTS.choose alone, and ms per
decision of the whole agent (lethal search included). One process, one thread; the median of R rounds.
usage: bench.py STEP1_DIR [N] [R] [--profile OUT]"""
import cProfile, json, pstats, statistics, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
S = sys.argv[1]
N = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 30
R = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else 3
prof = sys.argv[sys.argv.index("--profile") + 1] if "--profile" in sys.argv else None
sys.path.insert(0, f"{S}/ana")
import student_data as SD
from svsim.core.engine import legal_actions
from svsim.tools.arena import make_agent
from svsim.tools.gate import _search
games = {r["g"]: r for r in SD._lines(f"{S}/selfplay.jsonl")}
starts = [r for r in SD._lines(f"{S}/starts.jsonl") if r["split"] == "train"][:N]
states = [SD._state_at(games[r["game"]], r["at"]) for r in starts]
states = [s for s in states if len(legal_actions(s)) > 1]

def run():
    it = t_search = t_agent = 0.0
    for i, s in enumerate(states):
        agent = make_agent("mcts:200+plan+learned+phased", i)
        search = _search(agent)
        t = time.perf_counter(); search.choose(s.clone()); t_search += time.perf_counter() - t
        it += search.last_iterations
        agent = make_agent("mcts:200+plan+learned+phased", i)
        t = time.perf_counter(); agent.act(s.clone(), legal_actions(s)); t_agent += time.perf_counter() - t
    return it / t_search, 1000 * t_agent / len(states)

if prof:
    cProfile.run("run()", prof)
    pstats.Stats(prof).sort_stats("tottime").print_stats(40)
else:
    run()                                           # warm-up (imports, model loading, caches)
    rounds = [run() for _ in range(R)]
    print(json.dumps({"positions": len(states), "iterations_per_second": round(statistics.median(r[0] for r in rounds), 1),
                      "ms_per_decision": round(statistics.median(r[1] for r in rounds), 1),
                      "rounds": [[round(a, 1), round(b, 1)] for a, b in rounds]}))
