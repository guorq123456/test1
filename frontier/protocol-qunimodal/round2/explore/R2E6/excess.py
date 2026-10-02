"""Exact computation of U = {b : P unimodal} and the excess E = B* - 1 - F.

Fit box enforced: r<=30, k<=40 (k<=60 if all a_i equal), a_i<=100.

Method (exact, big integers):  P(q)(1-q) = G(q)(1-q^{rb}) with G = A(q)/[r]_q
(power series, coefficients g_n).  P is palindromic, so P unimodal iff
c_i - c_{i-1} = g_i - g_{i-rb} >= 0 for 1 <= i <= floor(N/2), N = D + r(b-1).
For i <= rb-1 this says g_i >= 0; for rb <= i <= N/2 it is g_i >= g_{i-rb}.
For n > D, g_n = tau_{n mod r} (periodic tail).
"""
from functools import lru_cache


def in_box(r, a):
    k = len(a)
    if r > 30 or max(a) > 100:
        return False
    if len(set(a)) == 1:
        return k <= 60
    return k <= 40


def poly_a(a):
    c = [1]
    for A in a:
        n = len(c) + A - 1
        d = [0] * n
        s = 0
        L = len(c)
        for t in range(n):
            if t < L:
                s += c[t]
            if 0 <= t - A < L:
                s -= c[t - A]
            d[t] = s
        c = d
    return c


class Inst:
    def __init__(self, r, a):
        a = sorted(a)
        assert in_box(r, a), "outside fit box"
        self.r, self.a = r, a
        self.k = len(a)
        self.D = sum(x - 1 for x in a)
        self.F = sum(x // r for x in a)
        self.S1 = sum((x % r) - 1 for x in a if x % r)  # not used when r|a_i
        c = poly_a(a)
        D = self.D
        delta = [c[0]] + [c[j] - c[j - 1] for j in range(1, D + 1)] + [-c[D]]
        self.delta = delta  # coefficients of A(q)(1-q), j=0..D+1
        g = [0] * (D + 2 + r)
        for n in range(D + 2 + r):
            v = delta[n] if n <= D + 1 else 0
            if n >= r:
                v += g[n - r]
            g[n] = v
        self.gfull = g
        self.tau = [g[D + 1 + ((t - (D + 1)) % r)] for t in range(r)]
        # first negative index of g (g_n for n > D+1+r is periodic = tau)
        fn = None
        for n in range(D + 2 + r):
            if g[n] < 0:
                fn = n
                break
        self.first_neg = fn  # None means g >= 0 everywhere (tau == 0 case)

    def g(self, n):
        if n < 0:
            return 0
        if n < len(self.gfull):
            return self.gfull[n]
        return self.tau[n % self.r]

    def unimodal(self, b):
        r, D = self.r, self.D
        N = D + r * (b - 1)
        h = N // 2
        lim = min(r * b - 1, h)
        if self.first_neg is not None and self.first_neg <= lim:
            return False
        for i in range(r * b, h + 1):
            if self.g(i) < self.g(i - r * b):
                return False
        return True

    def T6(self):
        # 1 + floor((D+1-2mu)/r); mu = least t with Gamma_t >= ... >= Gamma_{r-1}
        c = poly_a(self.a)
        r = self.r
        Gam = [sum(c[t::r]) for t in range(r)]
        mu = r - 1
        while mu > 0 and Gam[mu - 1] >= Gam[mu]:
            mu -= 1
        return 1 + (self.D + 1 - 2 * mu) // r

    def U(self, bmax=None):
        if any(x % self.r == 0 for x in self.a):
            return None  # unimodal for all b (C43)
        if bmax is None:
            bmax = self.T6() + 2
        return [b for b in range(1, bmax + 1) if self.unimodal(b)]

    def excess(self):
        U = self.U()
        return max(U) - 1 - self.F, U
