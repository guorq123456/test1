# T15 closed form (three middle residues, all other parts residue 1 or r-1): U = [1, B*].
def domain(r, a):
    if r < 4: return False
    if any(x % r == 0 for x in a): return False
    mid = [x for x in a if 2 <= x % r <= r - 2]
    return len(mid) == 3
def _Bstar(r, a):
    D = sum(x - 1 for x in a)
    F = sum(x // r for x in a)
    rho = [x % r for x in a if x % r >= 2]
    # cyclic class sums Gamma of prod [rho_i]_q modulo q^r - 1 (O(k r)), tau_t = Gamma_t - Gamma_{t-1}
    G = [0] * r; G[0] = 1
    for m in rho:
        P = [0] * (r + 1)
        for t in range(r): P[t + 1] = P[t] + G[t]
        tot = P[r]
        H = [0] * r
        for t in range(r):
            lo = t - m + 1  # sum of G over indices t-m+1..t (cyclic), m < r
            if lo >= 0: H[t] = P[t + 1] - P[lo]
            else: H[t] = P[t + 1] + (tot - P[r + lo])
        G = H
    tau = [G[t] - G[t - 1] for t in range(r)]
    mu = 0
    for j in range(1, r):
        if tau[j] > 0: mu = j
    T6 = 1 + (D + 1 - 2 * mu) // r
    s = (D + 1) % r
    fire = tau[s] <= -2 and s >= 2 * mu
    return T6 - 2 * fire
def predict(r, a, b):
    a = sorted(a)
    if any(x % r == 0 for x in a): return True
    return b <= _Bstar(r, a)
