# Core library for R2E2 (peeling path for S2).
# All computations exact (Python ints).
# P(q) = prod [a_i]_q * [b]_{q^r}.
# d = coefficients of A(q)(1-q)/(1-q^r)  (= A/[r]_q as power series).
# Unimodal(P) <=> d_n >= d_{n-rb} for 0<=n<=floor(N/2), N = D + r(b-1).
#   (Proof: Delta p_n = sum_{y<b} e_{n-ry} = d_n - d_{n-rb}; P symmetric.)

def polyA(a):
    c = [1]
    for A in a:
        n = len(c) + A - 1
        d = [0] * n
        s = 0
        for t in range(n):
            if t < len(c): s += c[t]
            if 0 <= t - A < len(c): s -= c[t - A]
            d[t] = s
        c = d
    return c

def dseq(a, r):
    """d_x for 0<=x<=D+r (beyond D: periodic with period r)."""
    c = polyA(a)
    D = len(c) - 1
    L = D + r + 1
    e = [0] * L
    for x in range(L):
        e[x] = (c[x] if x <= D else 0) - (c[x - 1] if 1 <= x <= D + 1 else 0)
    d = [0] * L
    for x in range(L):
        d[x] = e[x] + (d[x - r] if x >= r else 0)
    return d, D

class DS:
    def __init__(self, r, a):
        self.r = r; self.a = sorted(a)
        self.d, self.D = dseq(self.a, r)
    def __call__(self, x):
        if x < 0: return 0
        if x <= self.D + self.r: return self.d[x]
        D, r = self.D, self.r
        # reduce into [D+1, D+r]
        y = D + 1 + ((x - D - 1) % r)
        return self.d[y]

def unimodal_d(ds, b):
    r, D = ds.r, ds.D
    N = D + r * (b - 1)
    rb = r * b
    for n in range(0, N // 2 + 1):
        if ds(n) < ds(n - rb):
            return False
    return True

def Fval(r, a): return sum(x // r for x in a)
def Dval(a): return sum(x - 1 for x in a)

def gammas(r, a):
    c = polyA(a)
    G = [0] * r
    for i, v in enumerate(c): G[i % r] += v
    return G

def T6(r, a):
    G = gammas(r, a)
    mu = r - 1
    for t in range(r):
        if all(G[s] >= G[s + 1] for s in range(t, r - 1)):
            mu = t; break
    return 1 + (Dval(a) + 1 - 2 * mu) // r

def Uset(r, a, extra=2):
    """Set of b in [1, T6+extra] with P unimodal."""
    ds = DS(r, a)
    top = T6(r, a) + extra
    return [b for b in range(1, top + 1) if unimodal_d(ds, b)]

def Jset(r, a, extra=2):
    F = Fval(r, a)
    return [b - 1 - F for b in Uset(r, a, extra) if b - 1 - F >= 0]

def S2_shape(J):
    """J: list of j>=0 (j=b-1-F). S2 says J = [0,E] or [0,E]\\{E-1}, E even."""
    if not J: return False
    E = max(J)
    if E % 2: return False
    full = set(range(E + 1))
    s = set(J)
    return s == full or (E >= 2 and s == full - {E - 1})
