"""Rule EXACT (proven, see /tmp/claude-0/qu/explore/E7/proof_criterion.txt).

P(q) = prod_i [a_i]_q * [b]_{q^r}.  Let p = prod_i [a_i]_q (degree D = sum(a_i-1)),
N = D + r(b-1), h = floor(N/2), and let g_0, g_1, ... be the coefficients of the power series
    G(q) = p(q) / [r]_q = p(q)(1-q)/(1-q^r),
computed by g_i = (p_i - p_{i-1}) + g_{i-r}  (p_j = 0 outside 0..D, g_j = 0 for j<0).
Then P is unimodal  <=>  g_i >= g_{i - r b} for every 0 <= i <= h   (g_j := 0 for j < 0).
Equivalently: (I) g_i >= 0 for all i <= h, and (II) g_i >= g_{i-rb} for rb <= i <= h.
"""
def _p(a):
    c = [1]
    for A in a:
        n = [0] * (len(c) + A - 1)
        for i, v in enumerate(c):
            for j in range(A):
                n[i + j] += v
        c = n
    return c

def _g(p, r, n):
    g = [0] * (n + 1)
    for i in range(n + 1):
        v = (p[i] if i < len(p) else 0) - (p[i - 1] if 1 <= i <= len(p) else 0)
        g[i] = v + (g[i - r] if i >= r else 0)
    return g

def predict(r, a, b):
    p = _p(a)
    D = len(p) - 1
    h = (D + r * (b - 1)) // 2
    rb = r * b
    g = _g(p, r, h)
    for i in range(h + 1):
        if g[i] < (g[i - rb] if i >= rb else 0):
            return False
    return True
