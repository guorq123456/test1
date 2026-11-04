import sys, json
sys.path.insert(0, "/home/user/test1"); sys.path.insert(0, sys.argv[1] + "/ana")
import student_data as SD
from svsim.search import combo
from svsim.core.engine import apply, legal_actions
from svsim.tools.arena import make_agent
games = {r["g"]: r for r in SD._lines(sys.argv[1] + "/selfplay.jsonl")}
s = SD._state_at(games[109], 73)
kw = dict(tickers=True, fix=True, eot=True)
print("lethal3", bool(combo.planned_lethal(s, 20000, **kw)[0]), "adaptive", bool(combo.planned_lethal(s, 20000, adaptive=True, **kw)[0]))
# play it out with the agent on several rng outcomes
wins = 0
for seed in range(8):
    t = s.clone(); t.rng.seed(1000 + seed)
    a = make_agent("level-strong+lethal3+adaptive", seed); me = t.active
    while not t.over and t.active == me:
        apply(t, a.act(t, legal_actions(t)))
    wins += t.winner == me
print("agent wins", wins, "/ 8")
