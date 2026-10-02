"""
Rule for the all-equal family P(q) = [a]_q^k [b]_{q^r},  a = n*r + s,  s = a mod r in [2, r-2],  k >= 3.

Notation (all integers):
  Gamma_t = #{ x in {0,...,s-1}^k : x_1+...+x_k = t (mod r) }      (residue sums of [s]_q^k)
  tau_t   = Gamma_t - Gamma_{t-1}                                    (indices mod r)
  c_j     = sum_{l>=0, lr<=j} C(j - l r + k - 2, k - 2)  for j>=0,  c_j = 0 for j<0
            (= coefficient of q^j in 1/((1-q)^(k-1) (1-q^r)))
  d_j     = coefficient of q^j in [s]_q^k (1-q)/(1-q^r)   (power series; d_j = 0 for j<0)
  e       = b - 1 - k n           (excess over 1+F, F = kn)
  K       = k(s-1) + 1 - r(2+e)

Rule:
  b <= kn+1                       -> unimodal.
  otherwise, with h = c if n >= 1 and h = d if n = 0:
      unimodal  iff  tau_{m mod r} + h_{K-m} - h_m >= 0  for each of the r integers m with K/2 - r <= m < K/2.

Equivalently: for n >= 1, U = [1, kn+1] U (kn+1+E_inf(r,s,k)), E_inf depending only on (r, s, k).
"""
from math import comb
from functools import lru_cache

@lru_cache(maxsize=None)
def _tau(r, s, k):
    G = [0] * r
    G[0] = 1
    for _ in range(k):
        H = [0] * r
        for t in range(r):
            v = G[t]
            if v:
                for x in range(s):
                    H[(t + x) % r] += v
        G = H
    return tuple(G[t] - G[t - 1] for t in range(r))

def _c(r, k, L):
    c = [0] * (L + 1)
    for j in range(L + 1):
        v = comb(j + k - 2, k - 2)
        if j >= r:
            v += c[j - r]
        c[j] = v
    return c

def _d(r, s, k, L):
    # coefficients of [s]^k up to L, then times (1-q)/(1-q^r)
    S = [1]
    for _ in range(k):
        n = min(len(S) + s - 1, L + 1)
        T = [0] * n
        acc = 0
        for t in range(n):
            if t < len(S): acc += S[t]
            if 0 <= t - s < len(S): acc -= S[t - s]
            T[t] = acc
        S = T
    S = S + [0] * (L + 1 - len(S))
    d = [0] * (L + 1)
    for j in range(L + 1):
        v = S[j] - (S[j - 1] if j >= 1 else 0)
        if j >= r:
            v += d[j - r]
        d[j] = v
    return d

@lru_cache(maxsize=None)
def _hser(r, s, k, flat, L):
    return tuple(_c(r, k, L)) if flat else tuple(_d(r, s, k, L))

def domain(r, a):
    if r < 4 or len(a) < 3: return False
    if any(x != a[0] for x in a): return False
    s = a[0] % r
    return 2 <= s <= r - 2

def predict(r, a, b):
    k = len(a); a0 = a[0]; n, s = divmod(a0, r)
    if b <= k * n + 1:
        return True
    e = b - 1 - k * n
    K = k * (s - 1) + 1 - r * (2 + e)
    m0 = (K - 1) // 2                     # largest integer m with 2m < K
    L = max(K - (m0 - r + 1), 0) + 1      # largest index needed
    tau = _tau(r, s, k)
    h = _hser(r, s, k, n >= 1, max(L, k * (s - 1) // 2 + 2 * r + 2))
    H = lambda j: h[j] if j >= 0 else 0
    for m in range(m0, m0 - r, -1):
        if tau[m % r] + H(K - m) - H(m) < 0:
            return False
    return True
