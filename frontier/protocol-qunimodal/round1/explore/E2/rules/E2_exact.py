"""Rule E2_exact (Theorem A, proved in /tmp/claude-0/qu/explore/E2/proofs/main_proofs.txt).
P = prod[a_i]_q [b]_{q^r}.  Let D = sum(a_i-1), K = D+1-r(b+1).
d_u = coefficient of q^u in the power series p(q)(1-q)/(1-q^r)  (d_u = 0 for u<0);
tau_rho = (1/r) sum_{j=1}^{r-1} zeta^{-j rho}(1-zeta^j) p(zeta^j)  (r-periodic; computed exactly
          as the r-fold of (1-q)*prod[a_i mod r]_q);  E_u = d_u - tau_u.
P unimodal  <=>  r | some a_i, or  E_u >= d_{K-u} for every integer u with K/2 < u <= D+1-r.
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
def predict(r, a, b):
    a = sorted(a)
    if any(x % r == 0 for x in a):
        return True
    D = sum(x - 1 for x in a)
    tau = _tau(r, a)
    L = D + 2 - r
    d = _d(r, a, max(L, 1))
    def dd(v): return d[v] if 0 <= v < len(d) else 0
    K = D + 1 - r * (b + 1)
    u0 = max(K // 2 + 1, -r)          # tau is r-periodic: u in [-r,-1] covers all u<0
    for u in range(u0, D + 2 - r):
        E = dd(u) - tau[u % r]
        if E < dd(K - u):
            return False
    return True
def domain(r, a):
    return True
