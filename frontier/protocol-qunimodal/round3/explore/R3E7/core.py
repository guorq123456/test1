# R3E7 core: residue-level U_inf, window criterion with exact g, sharp stabilization threshold.
from math import comb
from functools import lru_cache

def in_box(r, a):
    """Fit box check for a concrete instance (r, a)."""
    k = len(a)
    if r >= 1000: return True
    if r > 120 or k > 140 or max(a) > 400: return False
    res = [x % r for x in a]
    mid = sum(1 for x in res if 2 <= x <= r-2)
    oth_pm1 = all((x == 1 or x == r-1) for x in res if not (2 <= x <= r-2))
    if k >= 20 and mid in (4, 5) and oth_pm1: return False
    if k >= 55 and sum(1 for x in res if x == r-1) > 50: return False
    if k >= 60:
        vals = set(a)
        if len(vals) == 2 and all(2 <= (v % r) <= r-2 for v in vals): return False
    return True

def tau_of(r, s):
    # (1-q) prod [s_i]_q mod q^r - 1
    v = [0]*r; v[0] = 1
    for si in s:
        nv = [0]*r
        for t in range(r):
            if v[t]:
                for j in range(si):
                    nv[(t+j) % r] += v[t]
        v = nv
    return [v[t] - v[(t-1) % r] for t in range(r)]

def w_table(r, k, N):
    """w_n = [q^n] 1/((1-q)^{k-1}(1-q^r)), n=0..N"""
    if k >= 2:
        B = [comb(n+k-2, k-2) for n in range(N+1)]
    else:
        B = [1] + [0]*N
    w = [0]*(N+1)
    for n in range(N+1):
        w[n] = B[n] + (w[n-r] if n >= r else 0)
    return w

class Res:
    def __init__(self, r, s):
        self.r = r; self.s = sorted(s); self.k = len(s)
        assert all(1 <= x <= r-1 for x in s)
        self.S = sum(s); self.K0 = self.S - self.k + 1
        self.tau = tau_of(r, self.s)
        pos = [t for t in range(r) if self.tau[t] > 0]
        self.mu = max(pos) if pos else 0
        self.T = 1 + (self.K0 - 2*self.mu)//r
        self.N = max(0, self.K0//2 + r + 2)
        self.w = w_table(r, self.k, self.N)
        self.Uinf = [1] + [e for e in range(2, self.T+1) if self.Rk(e, self.wf)]
    def wf(self, n):
        return self.w[n] if n >= 0 else 0
    def Delta(self, e):
        return self.K0 - self.r*(e+1)
    def window(self, e):
        D = self.Delta(e); h = D//2
        return D, range(h+1, h+self.r+1)
    def Rk(self, e, gf):
        D, W = self.window(e)
        for m in W:
            if gf(m) - gf(D-m) < self.tau[m % self.r]:
                return False
        return True
    def slack(self, e):
        D, W = self.window(e)
        return [(m, D-m, self.wf(m) - self.wf(D-m) - self.tau[m % self.r]) for m in W]
    def aL(self, L):
        r = self.r
        out = []
        for x in self.s:
            v = x
            if v < L: v += r*((L - v + r - 1)//r)
            out.append(v)
        return sorted(out)
    def gfun(self, a):
        """exact g_n (n<=self.N) for instance a with these residues: g = X*w, X=prod(1-q^{a_i})"""
        N = self.N
        g = list(self.w)
        for ai in a:
            if ai > N: continue
            for n in range(N, ai-1, -1):
                g[n] -= g[n-ai]
        return lambda n: g[n] if n >= 0 else 0
    def stable(self, a):
        gf = self.gfun(a)
        return all(self.Rk(e, gf) for e in self.Uinf if e >= 2)
    def U_of(self, a):
        """predicted full U(a) using window criterion with exact g (valid for any a with these residues, parts>=2)"""
        F = sum(x//self.r for x in a)
        gf = self.gfun(a)
        U = list(range(1, F+2))
        for e in range(2, self.T+1):
            if self.Rk(e, gf): U.append(F+e)
        return U
    def L0_R2E7(self):
        return max(1, (self.S - self.k + 3 - self.r)//2)
    def sharpL0(self):
        top = max(2, self.L0_R2E7())
        L = 2
        # find least L>=2 with aL stable; a^L only changes at certain L, scan all
        best = None
        for L in range(2, top+1):
            if self.stable(self.aL(L)):
                return L
        return top
