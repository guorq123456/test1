# For residue vectors rho with k parts, all lifts s in [0,Smax]^k (sorted-symmetric dedup not applied), record
# whether J(s) is a prefix of J_inf(rho), S2 shape, parity of max J(s).
import sys, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import *
from limit import Jinf
r, k, Smax = map(int, sys.argv[1:4])
only_gap = len(sys.argv) > 4 and sys.argv[4] == 'gap'
tot = 0; s2bad = 0; notprefix = 0; ex = []
for rho in itertools.combinations_with_replacement(range(1, r), k):
    rho = list(rho)
    Ji = Jinf(r, rho)
    if only_gap and Ji == list(range(max(Ji) + 1)): continue
    seen = set()
    for s in itertools.product(range(Smax + 1), repeat=k):
        a = tuple(sorted(rho[i] + r * s[i] for i in range(k)))
        if a in seen or max(a) > 100: continue
        seen.add(a)
        J = Jset(r, list(a)); tot += 1
        if not S2_shape(J): s2bad += 1; print("S2FAIL", r, a, J)
        pref = [x for x in Ji if x <= max(J)]
        if J != pref:
            notprefix += 1
            if len(ex) < 10: ex.append((a, J, Ji))
print(f"r={r} k={k} Smax={Smax} gaponly={only_gap}: instances {tot}, S2 fails {s2bad}, not-prefix {notprefix}")
for e in ex: print("  ", e)
