# Rule for the large-part regime (path R2E7).  predict(r, a, b) -> bool, domain(r, a) -> bool.
# domain: r divides no a_i, k>=1, and min(a) >= L0(r,res) = max(1, floor((S-k+3-r)/2)),
#         S = sum of residues a_i mod r, k = len(a).
# predict: b <= F+1  or  R(Delta) with Delta = S-k+1-r(b-F+1),
#   R(Delta): for every integer m with Delta/2 < m <= Delta/2 + r:  w_m - w_{Delta-m} >= tau_{m mod r},
#   w_n = coefficient of q^n in 1/((1-q)^(k-1)(1-q^r)) (0 for n<0),
#   tau_t = sum of coefficients of (1-q)*prod_i [a_i mod r]_q in degrees = t mod r.
# Proved (proofs.txt Thm 3): exact on the domain for every b >= 1.

def _w(k, r, n):
    w = [1 if i % r == 0 else 0 for i in range(n+1)]
    for _ in range(k-1):
        s = 0
        for i in range(n+1):
            s += w[i]; w[i] = s
    return w

def _tau(r, res):
    c = [0]*r; c[0] = 1
    for s in res:
        n = [0]*r
        for t in range(r):
            if c[t]:
                for j in range(s): n[(t+j) % r] += c[t]
        c = n
    return [c[t] - c[(t-1) % r] for t in range(r)]

def L0(r, a):
    res = [x % r for x in a]
    return max(1, (sum(res) - len(a) + 3 - r)//2)

def domain(r, a):
    return len(a) >= 1 and all(x % r for x in a) and min(a) >= L0(r, a)

def R(r, k, tau, Delta):
    lo = Delta//2 + 1
    w = _w(k, r, max(lo + r, 0) + 1)
    W = lambda n: w[n] if n >= 0 else 0
    return all(W(m) - W(Delta - m) >= tau[m % r] for m in range(lo, lo + r))

def predict(r, a, b):
    a = sorted(a); k = len(a)
    if any(x % r == 0 for x in a): return True          # C43 (not part of the claimed domain)
    F = sum(x//r for x in a)
    if b <= F + 1: return True
    res = [x % r for x in a]
    Delta = sum(res) - k + 1 - r*(b - F + 1)
    return R(r, k, _tau(r, res), Delta)

def Uinf(r, res):
    """U_inf as offsets e = b-F (finite set containing 1)."""
    k = len(res); tau = _tau(r, res); K0 = sum(res) - k + 1
    out = {1}
    for e in range(2, K0//r + 4):
        if R(r, k, tau, K0 - r*(e+1)): out.add(e)
    return out
