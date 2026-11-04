import sys, time
sys.path.insert(0, "/home/user/test1"); sys.path.insert(0, sys.argv[1] + "/ana")
import student_data as SD
from svsim.learn.features import extra_features, features
from svsim.learn.netdata import ENDED, rows
import svsim.search.combo as C
from svsim.learn.contrast import features_of
recs = list(SD._lines(f"{sys.argv[1]}/selfplay.jsonl"))[:40]
ends = [(st, me) for rec in recs for ph, me, st, res in rows(rec) if ph == ENDED]
for st, me in ends: extra_features(st, me, ("kclock",))      # warm profiles
for nodes in (300, 100, 50):
    C._NEXT_TURN.clear()
    t = time.perf_counter()
    for st, me in ends:
        C.next_turn_damage(st, me, nodes); C.next_turn_damage(st, 1 - me, nodes, hand=False)
    print(nodes, "nodes: planner ms per end", round(1e3 * (time.perf_counter() - t) / len(ends), 3))
t = time.perf_counter()
for st, me in ends: features_of(st, me, 2, ())
print("v2 features ms per end", round(1e3 * (time.perf_counter() - t) / len(ends), 3), len(ends))
