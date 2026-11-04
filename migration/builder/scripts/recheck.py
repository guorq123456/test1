import sys
sys.path.insert(0, "/home/user/test1"); sys.path.insert(0, sys.argv[1] + "/ana")
import student_data as SD
from svsim.search import combo
games = {r["g"]: r for r in SD._lines(sys.argv[1] + "/selfplay.jsonl")}
bad = []
for key in open(sys.argv[2]).read().strip().split(","):
    _, g, at = key.split("|"); s = SD._state_at(games[int(g[1:])], int(at[2:]))
    line, p = combo.planned_lethal(s, 20000, tickers=True, fix=True, eot=True, discard=True)
    if not line:
        bad.append(key)
print("still lost by the planner:", len(bad), bad)
