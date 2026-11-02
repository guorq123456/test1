"""Collect turn-start positions with ground-truth solver results."""
import sys, pickle, time
sys.path.insert(0, "/home/user/test1")
from svsim.search.lethal import LethalSearch
from svsim.tools.lethal import turn_starts
games = int(sys.argv[1]); budget = int(sys.argv[2]); out = sys.argv[3]; seed = int(sys.argv[4]) if len(sys.argv) > 4 else 0
search = LethalSearch(max_nodes=budget)
rows = []
for state, _ in turn_starts("starter", games, seed):
    r = search.solve(state)
    rows.append((state.clone(), r.sure, r.probability, r.complete, r.seconds, r.nodes))
pickle.dump(rows, open(out, "wb"))
print(len(rows), "positions;", sum(r[1] for r in rows), "sure;", sum(not r[3] for r in rows), "incomplete")
