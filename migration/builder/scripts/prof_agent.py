import cProfile, pstats, sys, time
sys.path.insert(0, "."); sys.path.insert(0, f"{sys.argv[1]}/ana")
import student_data as SD
from svsim.core.engine import legal_actions
from svsim.tools.arena import make_agent
S = sys.argv[1]
games = {r["g"]: r for r in SD._lines(f"{S}/selfplay.jsonl")}
starts = [r for r in SD._lines(f"{S}/starts.jsonl")][:120]
states = [SD._state_at(games[r["game"]], r["at"]) for r in starts]
states = [s for s in states if len(legal_actions(s)) > 1]
def run():
    for i, s in enumerate(states):
        agent = make_agent("mcts:200+plan+learned+phased", i)
        agent.act(s.clone(), legal_actions(s))
run()  # warm
cProfile.run("run()", f"{S}/prof_agent.out")
p = pstats.Stats(f"{S}/prof_agent.out"); p.sort_stats("cumtime").print_stats(45)
