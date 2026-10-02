# Test sub-claims on all multisets a (entries <= amax, r not dividing), k <= kmax:
#  A1: Bad(a) subset [0, mu]
#  A2: P(K_j) for all j <= E6-2  (K_j >= 2mu)
#  Bp: P(K'') holds where K'' = K_{E6}  (if K''>=2)
#  Bpp: [P(K') and Bad <= K'] => Bad <= K''   (K' = K_{E6-1})
#  B : E6-1 in J => E6 in J
import sys, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import *
from limit import tau
from decomp import *
from structure_helpers import mu_of
from collections import Counter
r, kmax, amax = map(int, sys.argv[1:4])
smallonly = len(sys.argv) > 4 and sys.argv[4] == 'small'
vals = [x for x in range(1, amax + 1) if x % r]
if smallonly: vals = list(range(1, r))
C = Counter(); ex = {}
def rec(name, ok, data):
    C[(name, ok)] += 1
    if not ok and (name) not in ex: ex[name] = data
for k in range(1, kmax + 1):
    for a in itertools.combinations_with_replacement(vals, k):
        a = list(a); ds = DS(r, a); tt = tau(r, a); bad = bad_set(r, a, ds, tt)
        if all(t == 0 for t in tt): C['degenerate'] += 1; continue
        sigma = sum((x % r) - 1 for x in a); mu = mu_of(tt, r)
        e6 = (sigma + 1 - 2 * mu) // r
        Kj = lambda j: sigma + 1 - r * (j + 2)
        rec('A1', all(u <= mu for u in bad), (a, bad, mu))
        if e6 >= 2:
            rec('A2', all(P_ok(r, ds, tt, Kj(j)) for j in range(0, e6 - 1)), (a, mu, e6))
            Kp, Kpp = Kj(e6 - 1), Kj(e6)
            rec('Bp', P_ok(r, ds, tt, Kpp), (a, mu, Kpp))
            hyp = P_ok(r, ds, tt, Kp) and all(u <= Kp for u in bad)
            if hyp: rec('Bpp', all(u <= Kpp for u in bad), (a, bad, mu, Kp, Kpp))
            J = Jset(r, a)
            if (e6 - 1) in J: rec('B', e6 in J, (a, J, e6))
print(r, kmax, amax, 'small' if smallonly else '')
for k_, v in sorted(C.items(), key=str): print("  ", k_, v)
for k_, v in ex.items(): print("  FAIL EXAMPLE", k_, v)
