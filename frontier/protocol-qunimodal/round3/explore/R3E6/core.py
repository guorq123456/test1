"""Core exact tools for R3E6 (four middle residues).
U(r,a): set of b>=1 with P unimodal, computed via Thm A g-form:
  P_b unimodal iff g_i >= g_{i-rb} for 0<=i<=floor(N/2), N = D + r(b-1),
  g = coefficients of A(q)/[r]_q (power series), g_i = 0 for i<0.
If r divides some a_i, U is infinite (returned as None).
Box guard enforced in check_box().
"""
import sys

def check_box(r, a):
    if 121 <= r <= 999:
        raise ValueError("forbidden r")
    if r >= 1000:
        return
    k = len(a)
    assert r <= 120 and k <= 140 and max(a) <= 400, (r, a)
    res = [x % r for x in a]
    mid = sum(1 for s in res if 2 <= s <= r - 2)
    if mid in (4, 5) and all(s in (1, r - 1) for s in res if not (2 <= s <= r - 2)) and k >= 20:
        raise ValueError("excluded (a)")
    if k >= 55 and sum(1 for s in res if s == r - 1) > 50:
        raise ValueError("excluded (b)")
    if k >= 60 and len(set(a)) == 2 and all(2 <= x % r <= r - 2 for x in set(a)):
        raise ValueError("excluded (c)")

def Apoly(a):
    c = [1]
    for A in a:
        if A == 1:
            continue
        deg = len(c) - 1
        nd = deg + A - 1
        d = [0] * (nd + 1)
        s = 0
        for t in range(nd + 1):
            if t <= deg:
                s += c[t]
            if 0 <= t - A <= deg:
                s -= c[t - A]
            d[t] = s
        c = d
    return c

def gseq(r, A, length):
    D = len(A) - 1
    B = [0] * (D + 2)
    for j in range(D + 2):
        B[j] = (A[j] if j <= D else 0) - (A[j - 1] if j >= 1 else 0)
    g = [0] * length
    for i in range(length):
        v = B[i] if i <= D + 1 else 0
        g[i] = v + (g[i - r] if i >= r else 0)
    return g, B

def inv(r, a):
    """Gamma-level data: D, F, tau (residue-level), Gamma."""
    D = sum(x - 1 for x in a)
    F = sum(x // r for x in a)
    A = Apoly(a)
    Gam = [0] * r
    for j, v in enumerate(A):
        Gam[j % r] += v
    tau = [Gam[t] - Gam[t - 1] for t in range(r)]
    return D, F, tau, Gam

def U(r, a, bmax=None):
    check_box(r, a)
    if any(x % r == 0 for x in a):
        return None
    D = sum(x - 1 for x in a)
    F = sum(x // r for x in a)
    A = Apoly(a)
    # T6 upper bound
    Gam = [0] * r
    for j, v in enumerate(A):
        Gam[j % r] += v
    mu = 0
    for t in range(r):
        if all(Gam[u] >= Gam[u + 1] for u in range(t, r - 1)):
            mu = t
            break
    T6 = 1 + (D + 1 - 2 * mu) // r
    if bmax is None:
        bmax = T6 + 2
    Nmax = D + r * (bmax - 1)
    g, B = gseq(r, A, Nmax // 2 + 2)
    out = []
    for b in range(1, bmax + 1):
        N = D + r * (b - 1)
        ok = True
        for i in range(0, N // 2 + 1):
            j = i - r * b
            if j >= 0 and g[i] < g[j]:
                ok = False; break
            if j < 0 and g[i] < 0:
                ok = False; break
        if ok:
            out.append(b)
    return out, T6, mu

if __name__ == '__main__':
    for line in sys.stdin:
        x = list(map(int, line.split()))
        r, k = x[0], x[1]
        print(U(r, sorted(x[2:2 + k])))
