# Rule file for conjecture S3* (refinement of S2), derived on the peeling path.
#
# Let A(q) = prod [a_i]_q (degree D), and let d_y be the coefficients of the power series A(q)/[r]_q
# = A(q)(1-q)/(1-q^r).  Let y* = least y with d_y < 0 (exists whenever r divides no a_i).
# Let B = 1 + floor((2 y* - D - 1)/r)   (equivalently B = max{b : N_b = D + r(b-1) < 2 y*}).
# Proven:   P unimodal  =>  b <= B.
# Conjectured (S3*):  B == 1 + F (mod 2),  every b <= B-2 gives a unimodal P, and
#                     (B-1 unimodal) => (B unimodal).   Hence U = [1,B] or [1,B]\{B-1}.
# predict() below is EXACT only modulo the single undecided value b = B-1, which it decides by the
# one remaining pair-condition  Phi(K) with K = D+1-r(b+1):  for all 0<=x<K/2,  Q_{K-x} >= d_x,
# where Q_u = d_u - tau_{u mod r}, tau_t = sum_{x = t mod r} [(1-q)A]_x.  (No fitted parameters.)

def _polyA(a):
    c = [1]
    for A in a:
        n = len(c) + A - 1; d = [0] * n; s = 0
        for t in range(n):
            if t < len(c): s += c[t]
            if 0 <= t - A < len(c): s -= c[t - A]
            d[t] = s
        c = d
    return c

def _data(r, a):
    c = _polyA(a); D = len(c) - 1
    L = D + r + 1
    e = [(c[x] if x <= D else 0) - (c[x - 1] if 1 <= x <= D + 1 else 0) for x in range(L)]
    d = [0] * L
    for x in range(L): d[x] = e[x] + (d[x - r] if x >= r else 0)
    tau = [0] * r
    for x in range(L): tau[x % r] += e[x]
    def dd(x):
        if x < 0: return 0
        if x < L: return d[x]
        return d[D + 1 + ((x - D - 1) % r)]
    return c, D, dd, tau

def domain(r, a):
    return all(x % r != 0 for x in a)

def Bvalue(r, a):
    c, D, dd, tau = _data(r, a)
    y = 0
    while dd(y) >= 0: y += 1
    return 1 + (2 * y - D - 1) // r

def predict(r, a, b):
    a = sorted(a)
    if not domain(r, a): return True          # C43: r | a_i  => unimodal
    c, D, dd, tau = _data(r, a)
    y = 0
    while dd(y) >= 0: y += 1
    B = 1 + (2 * y - D - 1) // r
    if b > B: return False                     # proven necessary condition
    if b != B - 1: return True                 # conjecture S3*: all b <= B except possibly B-1
    return _phi(r, D, dd, tau, b)              # b == B-1: decided by the pair condition Phi(K)

def _phi(r, D, dd, tau, b):
    K = D + 1 - r * (b + 1)
    for x in range(0, (K + 1) // 2):
        if 2 * x >= K: break
        if dd(K - x) - tau[(K - x) % r] < dd(x): return False
    return True
