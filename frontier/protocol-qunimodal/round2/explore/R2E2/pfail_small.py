# Small parts rho: for which K (K = sigma+1 mod r, K>=0) does P(K) fail?  Report K-2mu distribution (bucketed by r).
# Also Bad(rho) relative to mu and K' , K''.
import sys, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import *
from limit import tau
from decomp import *
from structure_helpers import mu_of
from collections import Counter
r, kmax = int(sys.argv[1]), int(sys.argv[2])
CP = Counter(); CB = Counter(); ex = {}
for k in range(1, kmax + 1):
    for a in itertools.combinations_with_replacement(range(1, r), k):
        a = list(a); ds = DS(r, a); tt = tau(r, a); bad = bad_set(r, a, ds, tt)
        sigma = sum(x - 1 for x in a); mu = mu_of(tt, r)
        K = (sigma + 1) % r
        while K <= sigma + 1 - 2 * r:
            if not P_ok(r, ds, tt, K):
                key = K - 2 * mu
                CP[key] += 1
                if key not in ex: ex[key] = (a, mu, K)
            K += r
        for u in bad: CB[u - mu] += 1
print("r", r, "kmax", kmax)
print("  P(K) failures by K-2mu:", sorted(CP.items()))
print("  examples:", sorted(ex.items())[:8])
print("  Bad elements by u-mu:", sorted(CB.items()))
