# Residue-level statement: check S2 shape of J_inf(rho) for all residue multisets rho (entries in [1,r-1]).
# Usage: python3 scan_limit_s2.py rmin rmax kmax
import sys, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import S2_shape
from limit import Jinf
rmin, rmax, kmax = map(int, sys.argv[1:4])
for r in range(rmin, rmax + 1):
    tot = 0; bad = 0; nonint = 0
    for k in range(1, kmax + 1):
        for rho in itertools.combinations_with_replacement(range(1, r), k):
            J = Jinf(r, list(rho))
            tot += 1
            if not S2_shape(J):
                bad += 1
                if bad <= 5: print("FAIL", r, rho, J)
            elif J != list(range(max(J) + 1)):
                nonint += 1
    print(f"r={r} kmax={kmax}: residue vectors {tot}, S2 failures {bad}, non-interval S2 shapes {nonint}", flush=True)
