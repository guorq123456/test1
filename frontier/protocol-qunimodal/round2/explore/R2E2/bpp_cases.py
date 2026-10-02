# Cases where Bad meets (K'', K'] (K'=K_{E6-1}, K''=K'-r), E6>=2: show why hypothesis of Bpp fails.
import sys, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import *
from limit import tau
from decomp import *
from structure_helpers import mu_of
from collections import Counter
r, kmax, amax = map(int, sys.argv[1:4])
vals = [x for x in range(1, amax + 1) if x % r]
C = Counter(); shown = 0
for k in range(1, kmax + 1):
    for a in itertools.combinations_with_replacement(vals, k):
        a = list(a); ds = DS(r, a); tt = tau(r, a); bad = bad_set(r, a, ds, tt)
        sigma = sum((x % r) - 1 for x in a); mu = mu_of(tt, r)
        e6 = (sigma + 1 - 2 * mu) // r
        if e6 < 2: continue
        Kp = sigma + 1 - r * (e6 + 1); Kpp = Kp - r
        hit = [u for u in bad if Kpp < u <= Kp]
        if not hit: continue
        pf = [x for x in range(0, (Kp + 1) // 2) if 2 * x < Kp and ds(Kp - x) - ds(x) < -tt[x % r]]
        badbig = [u for u in bad if u > Kp]
        key = ('P(Kp) fails' if pf else 'P ok', 'Bad>Kp' if badbig else '-', 'hit<=Kp/2' if all(2*u <= Kp for u in hit) else 'hit>Kp/2')
        C[key] += 1
        if shown < 12 and Kp >= 0:
            shown += 1
            print(a, "mu", mu, "Kp", Kp, "Kpp", Kpp, "bad", bad, "Pfail x", pf, "tau", tt, "d0..", [ds(i) for i in range(0, r)])
print(r, kmax, amax, sorted(C.items()))
