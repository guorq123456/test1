# Study Bad(a) = {u>=0 : d_u < tau_u}: relation to mu, K' = K_{E6-1}; and whether E6-1, E6 in J.
import sys, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import *
from limit import tau
from decomp import *
from structure_helpers import mu_of
from collections import Counter
r, kmax, amax = map(int, sys.argv[1:4])
vals = [x for x in range(1, amax + 1) if x % r]
C = Counter(); ex = {}
for k in range(1, kmax + 1):
    for a in itertools.combinations_with_replacement(vals, k):
        a = list(a); ds = DS(r, a); tt = tau(r, a); bad = bad_set(r, a, ds, tt)
        if not bad: continue
        if len(sys.argv) > 4 and (sum((x % r) - 1 for x in a) + 1 - 2 * mu_of(tt, r)) // r < 2: continue
        sigma = sum((x % r) - 1 for x in a); mu = mu_of(tt, r)
        e6 = (sigma + 1 - 2 * mu) // r
        Kp = sigma + 1 - r * (e6 + 1)
        J = Jset(r, a)
        key = ('max bad - mu', max(bad) - mu, 'bad residues<=mu', all(u % r <= mu for u in bad), 'Kp-2mu', Kp - 2*mu, 'E6-1 in J', (e6-1) in J, 'E6 in J', e6 in J)
        C[key] += 1
        if key not in ex: ex[key] = (a, bad, mu, Kp, tt)
print(r, kmax, amax)
for k_, v in sorted(C.items()): print("  ", k_, v, ex[k_])
