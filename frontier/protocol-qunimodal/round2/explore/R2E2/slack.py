# For small-part a, b = E6-1 (i.e. j=E6-2, K=D+1-r(b+1) >= 2mu): list slack s(m) = tau_m + d_{K-m} - d_m over m<K/2, m>=1-rb.
import sys, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import *
from limit import tau
from e6_vs_inf import E6
def mu_of(r, a):
    t = tau(r, a)
    for m in range(r):
        if all(t[s] <= 0 for s in range(m + 1, r)): return m
def slacks(r, a, b):
    ds = DS(r, a); D = ds.D; t = tau(r, a)
    K = D + 1 - r * (b + 1)
    out = []
    m = (K - 1) // 2
    while m >= 1 - r * b:
        out.append((m, t[m % r] + ds(K - m) - ds(m)))
        m -= 1
    return K, out
if __name__ == '__main__':
    r, k = int(sys.argv[1]), int(sys.argv[2])
    for a in itertools.combinations_with_replacement(range(1, r), k):
        a = list(a); e6 = E6(r, a)
        if e6 < 2: continue
        b = e6 - 1
        K, sl = slacks(r, a, b); mu = mu_of(r, a)
        mn = min(s for _, s in sl)
        tight = [m for m, s in sl if s == mn]
        print(a, "D", sum(x-1 for x in a), "mu", mu, "K", K, "tau", tau(r, a), "min slack", mn, "at m", tight[:5])
