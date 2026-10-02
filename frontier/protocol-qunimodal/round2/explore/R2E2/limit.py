# Large-part limit J_inf(rho) computed from d_inf = 1/((1-q)^{k-1}(1-q^r)), tau(rho), K_j.
# j in J_inf  iff  for all m in W_j: dinf(m) <= tau(m mod r) + dinf(K_j - m),
#   K_j = sigma + 1 - r(j+2), sigma = sum(rho_i - 1).
import sys
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import polyA
from functools import lru_cache

def dinf_seq(k, r, L):
    # coefficients of 1/((1-q)^{k-1}(1-q^r)) up to index L
    c = [1] + [0] * L
    for _ in range(k - 1):
        for x in range(1, L + 1): c[x] += c[x - 1]
    for x in range(r, L + 1): c[x] += c[x - r]
    return c

def tau(r, rho):
    c = polyA(rho)
    e = [0] * (len(c) + 1)
    for x in range(len(e)):
        e[x] = (c[x] if x < len(c) else 0) - (c[x - 1] if x >= 1 else 0)
    t = [0] * r
    for x, v in enumerate(e): t[x % r] += v
    return t

def Jinf(r, rho, jmax=None):
    k = len(rho)
    sigma = sum(x - 1 for x in rho)
    tt = tau(r, rho)
    L = sigma + 2 * r + 5
    dd = dinf_seq(k, r, L)
    def di(x):
        return dd[x] if x >= 0 else 0
    J = []
    if jmax is None: jmax = sigma // r + 3
    for j in range(0, jmax + 1):
        K = sigma + 1 - r * (j + 2)
        ok = True
        # m >= 0 part: 0 <= m < K/2 ; negative part: r largest m with m<K/2, m<=-1
        M0 = min(-1, (K - 1) // 2)
        ms = list(range(M0 - r + 1, M0 + 1)) + list(range(0, (K - 1) // 2 + 1))
        for m in ms:
            if di(m) > tt[m % r] + di(K - m): ok = False; break
        if ok: J.append(j)
    return J
