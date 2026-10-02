# Decomposition of the unimodality criterion into three parts (derived from d-criterion; see proof file):
#   K = D+1-r(b+1)
#   N(K):  tau_x >= 0 for all integers x with K < x < K/2          (only bites when K<0)
#   Bad(a) = {u >= 0 : d_u < tau_u}  ;  Zb: Bad subset [0,K]  (i.e. no bad u > K)
#   P(K):  for 0 <= x < K/2 : d_{K-x} - d_x >= -tau_x              (only bites when K>=2)
#   unimodal  <=>  N(K) and Zb and P(K)
import sys, itertools, random
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import *
from limit import tau

def bad_set(r, a, ds=None, tt=None):
    if ds is None: ds = DS(r, a)
    if tt is None: tt = tau(r, a)
    D = ds.D
    return [u for u in range(0, (D + 1 - r) // 2 + 2) if ds(u) < tt[u % r]]

def N_ok(r, tt, K):
    return all(tt[x % r] >= 0 for x in range(K + 1, -(-K // 2)) if 2 * x < K)

def P_ok(r, ds, tt, K):
    return all(ds(K - x) - ds(x) >= -tt[x % r] for x in range(0, (K + 1) // 2) if 2 * x < K)

def decomp(r, a, b, ds=None, tt=None, bad=None):
    if ds is None: ds = DS(r, a)
    if tt is None: tt = tau(r, a)
    if bad is None: bad = bad_set(r, a, ds, tt)
    K = ds.D + 1 - r * (b + 1)
    n = N_ok(r, tt, K)
    z = all(u <= K for u in bad)
    p = P_ok(r, ds, tt, K)
    return n, z, p, K

if __name__ == '__main__':
    random.seed(5)
    mism = 0; tot = 0
    for _ in range(int(sys.argv[1])):
        r = random.randint(3, 9); k = random.randint(1, 9)
        a = sorted(random.randint(1, 3 * r) for _ in range(k))
        if any(x % r == 0 for x in a): continue
        ds = DS(r, a); tt = tau(r, a); bad = bad_set(r, a, ds, tt)
        for b in range(1, T6(r, a) + 3):
            n, z, p, K = decomp(r, a, b, ds, tt, bad)
            u = unimodal_d(ds, b)
            tot += 1
            if (n and z and p) != u:
                mism += 1
                if mism < 5: print("MISMATCH", r, a, b, n, z, p, u)
    print("checked", tot, "mismatches", mism)
