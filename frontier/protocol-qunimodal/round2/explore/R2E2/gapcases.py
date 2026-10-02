# Gap cases: P(K_{E*-1}) fails. Print a, mu, beta, mu*, K, failing pairs, h values near 0.
import sys, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import *
from limit import tau
from decomp import *
from structure_helpers import mu_of
from s3star import estar
from fractions import Fraction as Fr
def hval(ds, tt, r, x):
    if x < 0: return Fr(-tt[x % r], 2)
    return Fr(ds(x)) - Fr(tt[x % r], 2)
def show(r, a):
    ds = DS(r, a); tt = tau(r, a)
    E, ms, bad = estar(r, a, ds, tt)
    sigma = sum((x % r) - 1 for x in a); mu = mu_of(tt, r)
    K = sigma + 1 - r * (E + 1)
    pf = [(x, K - x) for x in range(0, (K + 1) // 2) if 2 * x < K and ds(K - x) - ds(x) < -tt[x % r]]
    if not pf: return False
    hs = [str(hval(ds, tt, r, x)) for x in range(-r, K + 2)]
    print(f"r={r} a={a} sigma={sigma} D={ds.D} mu={mu} bad={bad} mu*={ms} E*={E} K'={K} fails={pf}\n    tau={tt}\n    h[-r..K+1]={hs}")
    return True
if __name__ == '__main__':
    mode = sys.argv[1]; n = 0
    if mode == 'eq':
        for r in range(4, 11):
            for t in range(1, r):
                for k in range(1, 61):
                    if show(r, [t] * k):
                        n += 1
                        if n > 12: sys.exit()
    else:
        r, kmax, amax = map(int, sys.argv[2:5])
        vals = [x for x in range(1, amax + 1) if x % r]
        for k in range(1, kmax + 1):
            for a in itertools.combinations_with_replacement(vals, k):
                if show(r, list(a)):
                    n += 1
                    if n > 6: sys.exit()
