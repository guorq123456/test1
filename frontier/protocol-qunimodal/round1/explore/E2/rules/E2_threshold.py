"""Rule E2_threshold (Corollary A1; exact whenever K=D+1-r(b+1)<=0, ignores the rare K>0 'pair obstructions').
y* = max{u in Z : d_u < tau_u}   (d_u = [q^u] p(q)(1-q)/(1-q^r), d_u=0 for u<0; tau = periodic residue imbalance).
Predict unimodal  <=>  r | some a_i  or  r(b+1) + 2 y* <= D+1.
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
def ystar(r, a):
    D = sum(x - 1 for x in a); tau = _tau(r, a)
    d = _d(r, a, max(D + 2 - r, 1))
    y = None
    for u in range(-r, D + 2 - r):
        du = d[u] if 0 <= u < len(d) else 0
        if du < tau[u % r]: y = u
    return y
def predict(r, a, b):
    a = sorted(a)
    if any(x % r == 0 for x in a): return True
    D = sum(x - 1 for x in a)
    return r * (b + 1) + 2 * ystar(r, a) <= D + 1
def domain(r, a): return True
