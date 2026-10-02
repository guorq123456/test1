# For each a (r not dividing parts): classify; check (A) P(K_j) & Bad<=K_j for j<=E6-2; case of (B); Bad-set locations.
import sys, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import *
from limit import tau
from decomp import *
from collections import Counter
def mu_of(tt, r):
    for m in range(r):
        if all(tt[s] <= 0 for s in range(m + 1, r)): return m
r, kmax, amax = map(int, sys.argv[1:4])
vals = [x for x in range(1, amax + 1) if x % r]
C = Counter(); ex = {}
for k in range(1, kmax + 1):
    for a in itertools.combinations_with_replacement(vals, k):
        a = list(a); ds = DS(r, a); tt = tau(r, a); bad = bad_set(r, a, ds, tt)
        sigma = sum((x % r) - 1 for x in a); mu = mu_of(tt, r)
        degenerate = all(t == 0 for t in tt)
        e6 = (sigma + 1 - 2 * mu) // r
        Kj = lambda j: sigma + 1 - r * (j + 2)
        PA = all(P_ok(r, ds, tt, Kj(j)) for j in range(0, e6 - 1))
        ZA = all(all(u <= Kj(j) for u in bad) for j in range(0, e6 - 1))
        Kp = Kj(e6 - 1); K0 = Kj(e6)
        case = 'B1' if Kp < 0 else ('B2' if K0 < 0 else 'B3')
        badmax = max(bad) if bad else -1
        key = (case, PA, ZA, degenerate, 'bad<=Kp/2' if 2*badmax <= Kp else 'badbig')
        C[key] += 1
        if key not in ex: ex[key] = (a, bad, Kp, K0, tt)
print(r, kmax, amax)
for k_, v in sorted(C.items()): print("  ", k_, v, ex[k_])
