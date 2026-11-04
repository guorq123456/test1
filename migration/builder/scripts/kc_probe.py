import sys, time, json
sys.path.insert(0, "/home/user/test1"); sys.path.insert(0, sys.argv[1] + "/ana")
import student_data as SD
from svsim.learn.features import extra_features
from svsim.learn.netdata import ENDED, rows
recs = list(SD._lines(f"{sys.argv[1]}/selfplay.jsonl"))[:6]
n, t0 = 0, time.perf_counter()
out = []
for rec in recs:
    for ph, me, st, res in rows(rec):
        if ph != ENDED: continue
        v = extra_features(st, me, ("kclock",))
        n += 1
        if n % 7 == 0: out.append([round(x, 2) for x in v] + [res])
dt = time.perf_counter() - t0
print(n, "ends", round(1e3 * dt / n, 2), "ms each (cold)")
for r in out[:12]: print(r)
t0 = time.perf_counter()
for rec in recs:
    for ph, me, st, res in rows(rec):
        if ph == ENDED: extra_features(st, me, ("kclock",))
print("warm", round(1e3 * (time.perf_counter() - t0) / n, 3), "ms each")
