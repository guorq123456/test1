# Scan: check S2 shape of J(a) = {b-1-F : b in U, b>=1+F} for r in R, multisets a (no a_i divisible by r).
# Usage: python3 scan_s2.py r kmax amax
import sys, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import *
r, kmax, amax = map(int, sys.argv[1:4])
vals = [x for x in range(1, amax + 1) if x % r]
tot = 0; bad = 0; shapes = {}
for k in range(1, kmax + 1):
    for a in itertools.combinations_with_replacement(vals, k):
        a = list(a)
        J = Jset(r, a)
        tot += 1
        ok = S2_shape(J)
        key = (tuple(J) == tuple(range(max(J) + 1))) if J else None
        shapes[key] = shapes.get(key, 0) + 1
        if not ok:
            bad += 1
            if bad <= 10: print("S2 FAIL", r, a, "U=", Uset(r, a), "J=", J)
print(f"r={r} kmax={kmax} amax={amax}: total {tot}, S2 failures {bad}, shape counts (interval?) {shapes}")
