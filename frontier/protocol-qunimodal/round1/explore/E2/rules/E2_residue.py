"""Rule E2_residue (Theorem B gives '=>' unconditionally; '<=' holds when y* = c - r and no K>0 obstruction).
c = max{c in {0..r-1} : tau_c > 0}, tau from the values p(zeta^j) (depends only on t_i = a_i mod r).
Predict unimodal  <=>  r | some a_i  or  r(b-1) <= D + 1 - 2c.
Equivalently b <= 1 + S + floor(e*/r), S = sum floor(a_i/r), e* = sum(t_i-1) + 1 - 2c.
"""
def _tau(r, a):
    t = [x % r for x in a]
    if any(x == 0 for x in t):
        return [0] * r
    f = [0] * r; f[0] = 1
    for ti in t:                      # multiply by [ti]_q modulo q^r - 1
        g = [0] * r
        for i, v in enumerate(f):
            if v:
                for j in range(ti):
                    g[(i + j) % r] += v
        f = g
    return [f[m] - f[(m - 1) % r] for m in range(r)]
def _d(r, a, L):
    p = [1]
    for A in a:
        n = [0] * (len(p) + A - 1); s = 0
        for t in range(len(n)):
            if t < len(p): s += p[t]
            if 0 <= t - A < len(p): s -= p[t - A]
            n[t] = s
        p = n
    d = [0] * max(L, 0)
    for u in range(L):
        dp = (p[u] if u < len(p) else 0) - (p[u - 1] if 0 <= u - 1 < len(p) else 0)
        d[u] = dp + (d[u - r] if u >= r else 0)
    return d
def cval(r, a):
    tau = _tau(r, a)
    return max(c for c in range(r) if tau[c] > 0)
def predict(r, a, b):
    a = sorted(a)
    if any(x % r == 0 for x in a): return True
    D = sum(x - 1 for x in a)
    return r * (b - 1) <= D + 1 - 2 * cval(r, a)
def domain(r, a): return True
