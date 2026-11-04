import sys, time, cProfile, pstats
sys.path.insert(0, "/home/user/test1"); sys.path.insert(0, sys.argv[1] + "/ana")
import student_data as SD
from svsim.learn.features import extra_features
from svsim.learn.netdata import ENDED, rows
recs = list(SD._lines(f"{sys.argv[1]}/selfplay.jsonl"))[:40]
ends = [(st, me) for rec in recs for ph, me, st, res in rows(rec) if ph == ENDED]
for st, me in ends: extra_features(st, me, ("kclock",))
t = time.perf_counter()
for st, me in ends: extra_features(st, me, ("kclock",))
print("ms per end", round(1e3 * (time.perf_counter() - t) / len(ends), 4))
t = time.perf_counter()
for st, me in ends: extra_features(st, me, ("clock",))
print("old clock ms per end", round(1e3 * (time.perf_counter() - t) / len(ends), 4))
cProfile.run('for st, me in ends: extra_features(st, me, ("kclock",))', f"{sys.argv[1]}/../kc.prof")
pstats.Stats(f"{sys.argv[1]}/../kc.prof").sort_stats("tottime").print_stats(8)
