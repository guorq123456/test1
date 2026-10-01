"""Rule THRESHOLD (monotone in b; = condition (I) of the exact criterion).

With p = prod_i [a_i]_q, D = deg p, G(q) = p(q)/[r]_q = sum g_i q^i (power series), let
X+1 = the index of the first negative coefficient of G (X = infinity if none; this happens
iff r divides some a_i).  Predict: P unimodal  <=>  floor((D + r(b-1))/2) <= X,
i.e.  b <= B_A := 1 + floor((2X + 1 - D)/r).
Condition (I) is necessary for unimodality (proven); it is sufficient except when the overlap
condition (II) fails.  In the fit box it is wrong on exactly 85 instances (all r=6, false positives).
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
    g = _g(p, r, h)
    return all(x >= 0 for x in g)
