"""Quantities for the asymptotic analysis of the excess E = B* - 1 - F.

M      = max_t(-tau_t)  (= max_t tau_t by antisymmetry)
delta_n = g_{n+1} - g_n  where g = power-series coefficients of A(q)/[r]_q   (actual a)
dgam_n  = gamma_{n+1}-gamma_n = [q^{n+1}] 1/((1-q)^{k-2}(1-q^r))           (B4 limit)
Sandwich (proved in proof file for the B4 regime, min a_i large):
  n_lo = min{n>=0 : delta_n >= M},  n_hi = min{n in Z : 2r*delta_{n+r-1} >= M}
  floor((S1+1-2r-2 n_lo)/r) <= E <= floor((S1+1-2r-2 n_hi)/r)
Asymptotics: E = k(sigma1 - 2 theta*)/r - log k/(r*ln(1+1/theta*)) + O(1),
  sigma1 = mean(s_i-1), L = max_j mean_i ln|sin(pi j s_i/r)/sin(pi j/r)|, H(theta*) = L,
  H(t) = (1+t)ln(1+t) - t ln t.
"""
import math
from math import comb
import sys
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E6')
from b4limit import tau_of, gamma_seq


def H(t):
    if t <= 0:
        return 0.0
    return (1 + t) * math.log(1 + t) - t * math.log(t)


def Hinv(L):
    if L <= 0:
        return 0.0
    lo, hi = 0.0, 1.0
    while H(hi) < L:
        hi *= 2
    for _ in range(200):
        mid = (lo + hi) / 2
        if H(mid) < L:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def ell(r, s, j):
    """mean over residues of ln|[s]_{omega^j}|, omega = exp(2 pi i/r); -inf if some factor vanishes"""
    tot = 0.0
    for x in s:
        num = abs(math.sin(math.pi * j * x / r))
        den = abs(math.sin(math.pi * j / r))
        if num < 1e-12:
            return -math.inf
        tot += math.log(num / den)
    return tot / len(s)


def Lrate(r, s):
    return max(ell(r, s, j) for j in range(1, r))


def asym_pred(r, s):
    """leading-order + log term prediction (no constant)"""
    k = len(s)
    sigma1 = sum((x % r) - 1 for x in s) / k
    L = Lrate(r, s)
    th = Hinv(L)
    c = (sigma1 - 2 * th) / r
    kappa = 1.0 / (r * math.log(1 + 1 / th)) if th > 0 else 0.0
    return dict(sigma1=sigma1, L=L, theta=th, c=c, kappa=kappa,
                lead=c * k, withlog=c * k - kappa * math.log(k))


def sandwich_from_delta(r, S1, M, delta, ncap=10**9):
    """delta: function n -> delta_n (nondecreasing assumed). returns (n_lo, n_hi, E_lo, E_hi)"""
    n = 0
    while delta(n) < M:
        n += 1
        if n > ncap:
            return None
    n_lo = n
    n = -r  # delta_{n+r-1} = 0 for n < -r, so the minimum over all integers is >= -r
    while 2 * r * delta(n + r - 1) < M:
        n += 1
    n_hi = n
    E_lo = (S1 + 1 - 2 * r - 2 * n_lo) // r
    E_hi = (S1 + 1 - 2 * r - 2 * n_hi) // r
    return n_lo, n_hi, max(E_lo, 0), E_hi


def sandwich_b4(r, s):
    k = len(s)
    S1 = sum((x % r) - 1 for x in s)
    tau = tau_of(r, s)
    M = max(-t for t in tau)
    cache = {}

    def dgam(n):
        if n < -1:
            return 0
        # [q^{n+1}] 1/((1-q)^{k-2}(1-q^r))
        tot = 0
        m = n + 1
        while m >= 0:
            tot += comb(m + k - 3, k - 3) if k >= 3 else (1 if m == 0 else 0)
            m -= r
        return tot
    return sandwich_from_delta(r, S1, M, dgam), M


def sandwich_actual(I):
    """I: excess.Inst. uses actual g. Also reports whether delta is nondecreasing on [-1, nmax]."""
    r = I.r
    S1 = sum((x % r) - 1 for x in I.a)
    M = max(-t for t in I.tau)

    def delta(n):
        return I.g(n + 1) - I.g(n)
    res = sandwich_from_delta(r, S1, M, delta, ncap=(I.D + 1) // 2)
    if res is None:
        return None, M, False
    n_lo = res[0]
    top = 2 * n_lo + 2 * r
    mono = all(delta(n) <= delta(n + 1) for n in range(-1, top))
    return res, M, mono


# ---------- bounded-a regime: large-deviation rate of [q^n] prod [a_i]_q ----------
def Lam(theta, avals):
    """Lambda(theta) = inf_{0<z<1} [ mean_i ln [a_i]_z - theta ln z ]  (Legendre/Cramer rate, theta < mean (a_i-1)/2)"""
    def f(z):
        return sum(math.log((1 - z ** a) / (1 - z)) for a in avals) / len(avals) - theta * math.log(z)
    lo, hi = 1e-12, 1 - 1e-12
    # f is convex in log z; ternary search on u = ln z
    ulo, uhi = math.log(lo), math.log(hi)
    for _ in range(300):
        u1 = ulo + (uhi - ulo) / 3; u2 = uhi - (uhi - ulo) / 3
        if f(math.exp(u1)) < f(math.exp(u2)):
            uhi = u2
        else:
            ulo = u1
    z = math.exp((ulo + uhi) / 2)
    return f(z), z


def Laminv(L, avals):
    mean = sum(a - 1 for a in avals) / len(avals) / 2
    lo, hi = 0.0, mean
    if Lam(hi * 0.999999, avals)[0] < L:
        return None
    for _ in range(100):
        mid = (lo + hi) / 2
        if Lam(mid, avals)[0] < L:
            lo = mid
        else:
            hi = mid
    th = (lo + hi) / 2
    return th, Lam(th, avals)[1]


def asym_pred_bounded(r, a):
    k = len(a)
    s = [x % r for x in a]
    sigma1 = sum(x - 1 for x in s) / k
    L = Lrate(r, s)
    res = Laminv(L, a)
    if res is None:
        return None
    th, z = res
    c = (sigma1 - 2 * th) / r
    kappa = 1.0 / (r * (-math.log(z)))
    return dict(sigma1=sigma1, L=L, theta=th, z=z, c=c, kappa=kappa, lead=c * k, withlog=c * k - kappa * math.log(k))


# ---------- explicit window from (r, k, S1, L) only (Theorem 2 in proof file) ----------
def dgam_fn(r, k):
    def dgam(n):
        if n < -1:
            return 0
        tot = 0
        m = n + 1
        while m >= 0:
            tot += comb(m + k - 3, k - 3)
            m -= r
        return tot
    return dgam


def explicit_window(r, s):
    """M is replaced by its bounds  (2 sin(pi/r)/r) e^{kL} <= M <= (2(r-1)/r) e^{kL}.
       n_plus  = min{n>=0 : delta_n >= (2(r-1)/r) e^{kL}}
       n_minus = min{n in Z : 2r*delta_{n+r-1} >= (2 sin(pi/r)/r) e^{kL}}
       delta_n = [q^{n+1}] 1/((1-q)^{k-2}(1-q^r)).   Requires k>=3.
       Returns (E_minus, E_plus, n_plus, n_minus):
       E_minus = max(0, floor((S1+1-2r-2 n_plus)/r)) <= E <= floor((S1+1-2r-2 n_minus)/r) = E_plus."""
    k = len(s)
    S1 = sum((x % r) - 1 for x in s)
    kL = k * Lrate(r, s)
    up = math.log(2 * (r - 1) / r) + kL
    lo = math.log(2 * math.sin(math.pi / r) / r) + kL
    d = dgam_fn(r, k)

    def ld(n):
        v = d(n)
        return math.log(v) if v > 0 else -math.inf
    n = 0
    while ld(n) < up:
        n += 1
    n_plus = n
    n = -r
    while math.log(2 * r) + ld(n + r - 1) < lo:
        n += 1
    n_minus = n
    return max(0, (S1 + 1 - 2 * r - 2 * n_plus) // r), (S1 + 1 - 2 * r - 2 * n_minus) // r, n_plus, n_minus
