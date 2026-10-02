"""Rule C3 (pure closed-form asymptotic excess; no polynomial or window computation).

predict(r, a, b):
  * if r divides some a_i -> True (C43);  if b <= 1+F -> True (T1)
  * otherwise b <= 1 + F + E_pred,  E_pred = max(0, 2 floor((X + beta)/2)),  beta = -0.5,
    X = k (sigma1 - 2 theta*)/r - ln(k)/(r ln(1+1/theta*)),
    sigma1 = mean(s_i - 1), s_i = a_i mod r,
    L = (1/k) max_{1<=j<=r-1} sum_i ln|sin(pi j s_i/r)/sin(pi j/r)|,
    theta* = root of (1+t)ln(1+t) - t ln t = L.
Domain claimed: k >= 3, r divides no a_i, at least three a_i with residue in [2, r-2].
"""
import math

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


def E_pred(r, a, beta=BETA):
    s = [x % r for x in a]
    k = len(s)
    S1 = sum(x - 1 for x in s)
    th = _Hinv(_Lrate(r, s))
    X = (S1 - 2 * th * k) / r
    if th > 0:
        X -= math.log(k) / (r * math.log(1 + 1 / th))
    return max(0, 2 * math.floor((X + beta) / 2))


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
