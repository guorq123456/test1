"""Rule C11 (asymptotic excess, clipped to the proven residue-only window).

predict(r, a, b):
  * if r divides some a_i                      -> True   (C43)
  * if b <= 1 + F                              -> True   (T1)
  * otherwise                                  -> b <= 1 + F + E_pred(r, a)
E_pred:
  s_i = a_i mod r, k = len(a), S1 = sum(s_i - 1), sigma1 = S1/k
  L      = (1/k) max_{1<=j<=r-1} sum_i ln|sin(pi j s_i/r)/sin(pi j/r)|
  theta* = root of H(theta) = L,   H(t) = (1+t)ln(1+t) - t ln t
  lambda = ln(1 + 1/theta*)
  X      = k (sigma1 - 2 theta*)/r - ln(k)/(r lambda)               (asymptotic excess, Thm 3)
  e0     = 2 floor((X + beta)/2),  beta = -0.5  (one fitted constant; E is even)
  window (Thm 1 / Cor 1): tau = (1-q) prod [s_i]_q mod (q^r - 1), M = max tau,
     delta_n = [q^{n+1}] 1/((1-q)^{k-2}(1-q^r)),
     n_lo = min{n>=0: delta_n >= M}, n_hi = min{n in Z: 2r delta_{n+r-1} >= M},
     E_lo = floor((S1+1-2r-2n_lo)/r), E_hi = floor((S1+1-2r-2n_hi)/r)
  E_pred = e0 clipped to [smallest even >= max(E_lo,0), largest even <= E_hi] (if that range is nonempty).
Domain claimed: k >= 3, r divides no a_i, at least three a_i with residue in [2, r-2].
"""
import math
from math import comb

BETA = -0.5


def _H(t):
    if t <= 0:
        return 0.0
    return (1 + t) * math.log(1 + t) - t * math.log(t)


def _Hinv(L):
    if L <= 0:
        return 0.0
    lo, hi = 0.0, 1.0
    while _H(hi) < L:
        hi *= 2
    for _ in range(200):
        mid = (lo + hi) / 2
        if _H(mid) < L:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _Lrate(r, s):
    best = -math.inf
    for j in range(1, r):
        den = abs(math.sin(math.pi * j / r))
        tot = 0.0
        for x in s:
            num = abs(math.sin(math.pi * j * x / r))
            if num < 1e-12:
                tot = -math.inf
                break
            tot += math.log(num / den)
        best = max(best, tot)
    return best / len(s)


def _tau(r, s):
    v = [0] * r
    v[0] = 1
    for x in s:
        w = [0] * r
        for i in range(r):
            if v[i]:
                for j in range(x):
                    w[(i + j) % r] += v[i]
        v = w
    return [v[t] - v[(t - 1) % r] for t in range(r)]


def _window(r, s):
    k = len(s)
    S1 = sum(x - 1 for x in s)
    M = max(_tau(r, s))

    def delta(n):
        if n < -1:
            return 0
        tot = 0
        m = n + 1
        while m >= 0:
            tot += comb(m + k - 3, k - 3)
            m -= r
        return tot
    n = 0
    while delta(n) < M:
        n += 1
    n_lo = n
    n = -r
    while 2 * r * delta(n + r - 1) < M:
        n += 1
    n_hi = n
    return (S1 + 1 - 2 * r - 2 * n_lo) // r, (S1 + 1 - 2 * r - 2 * n_hi) // r


def E_pred(r, a, beta=BETA):
    s = [x % r for x in a]
    k = len(s)
    S1 = sum(x - 1 for x in s)
    L = _Lrate(r, s)
    th = _Hinv(L)
    X = (S1 - 2 * th * k) / r
    if th > 0:
        X -= math.log(k) / (r * math.log(1 + 1 / th))
    e = 2 * math.floor((X + beta) / 2)
    Elo, Ehi = _window(r, s)
    lo = max(Elo, 0)
    lo += lo % 2
    hi = Ehi - (Ehi % 2)
    if lo <= hi:
        e = min(max(e, lo), hi)
    return max(e, 0)


def domain(r, a):
    if len(a) < 3 or any(x % r == 0 for x in a):
        return False
    return sum(1 for x in a if 2 <= x % r <= r - 2) >= 3


def predict(r, a, b):
    a = sorted(a)
    if any(x % r == 0 for x in a):
        return True
    F = sum(x // r for x in a)
    if b <= 1 + F:
        return True
    if len(a) < 3:
        return False
    return b <= 1 + F + E_pred(r, a)
