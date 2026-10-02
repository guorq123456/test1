"""B4-limit (all a_i -> infinity, residues fixed) version of the exact criterion.

For residues s_1..s_k (none 0 mod r):
  tau   = (1-q) prod [s_i]_q  mod (q^r - 1)            (periodic tail, depends on residues only)
  gamma = coefficients of 1/((1-q)^(k-1) (1-q^r))     (= g_n for n < min a_i)
  S1    = sum (s_i - 1)
For e = b-1-F, K = S1 + 1 - r(2+e).  Exact criterion (all a): P unimodal iff
   g_{K-m} - g_m + tau_{m mod r} >= 0   for all -rb <= m < K/2.
In the B4 limit g -> gamma on the relevant window, so
   e in U_inf  iff  gamma_{K-m} - gamma_m + tau_{m mod r} >= 0 for all integers m < K/2.
"""
from math import comb


def tau_of(r, s):
    v = [0] * r
    v[0] = 1
    for x in s:
        x %= r
        w = [0] * r
        for i in range(r):
            if v[i]:
                for j in range(x):
                    w[(i + j) % r] += v[i]
        v = w
    # multiply by (1-q)
    return [v[t] - v[(t - 1) % r] for t in range(r)]


def gamma_seq(r, k, nmax):
    # coefficients of 1/((1-q)^(k-1)(1-q^r)), n = 0..nmax
    base = [comb(n + k - 2, k - 2) if k >= 2 else (1 if n == 0 else 0) for n in range(nmax + 1)]
    g = [0] * (nmax + 1)
    for n in range(nmax + 1):
        g[n] = base[n] + (g[n - r] if n >= r else 0)
    return g


def U_inf(r, s, emax=None):
    k = len(s)
    S1 = sum((x % r) - 1 for x in s)
    tau = tau_of(r, s)
    M = max(max(-t for t in tau), 0)
    if emax is None:
        emax = S1 // r + 2
    cache = {'nmax': S1 + 4 * r + 10}
    cache['gam'] = gamma_seq(r, k, cache['nmax'])

    def G(n):
        if n < 0:
            return 0
        if n > cache['nmax']:
            cache['nmax'] = 2 * n
            cache['gam'] = gamma_seq(r, k, cache['nmax'])
        return cache['gam'][n]

    out = []
    for e in range(0, emax + 1):
        K = S1 + 1 - r * (2 + e)
        ok = True
        # m < K/2 ; for m very negative gamma_{K-m} grows and exceeds M; scan down until gamma_{K-m} > M
        m = (K - 1) // 2 if K % 2 else K // 2 - 1
        while True:
            lhs = G(K - m) - G(m) + tau[m % r]
            if lhs < 0:
                ok = False
                break
            if m < 0 and G(K - m) > M:
                break
            m -= 1
        if ok:
            out.append(e)
    return out, tau, M, S1


def E_inf(r, s):
    U, tau, M, S1 = U_inf(r, s)
    return max(U)
