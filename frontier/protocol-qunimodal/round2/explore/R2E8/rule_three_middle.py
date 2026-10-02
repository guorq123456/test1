# Rule H1 for the "exactly three middle residues" class (path R2E8).
# domain: r>=4, r divides no a_i, exactly three a_i have residue a_i mod r in [2, r-2]
#         (all others then have residue 1 or r-1).
# tau = (1-q) * prod_i [a_i mod r]_q reduced mod (q^r - 1)   (= Gamma_t - Gamma_{t-1}),
# mu  = largest j in [1,r-1] with tau_j > 0 (0 if none)       (= the mu of Theorem C),
# T6  = 1 + floor((D+1-2mu)/r), D = sum(a_i - 1), s = (D+1) mod r.
# B*  = T6 - 2 if (tau_s <= -2 and s >= 2*mu) else T6.   predict: b <= B*.
# PROVED (proof_three_middle.txt) for r<=30 and #{i: a_i = -1 mod r} <= 37, any a_i sizes,
# any number of a_i = 1 mod r; conjectural beyond that.
def _tau(r, a):
    c = [0] * r; c[0] = 1; c[1 % r] -= 1
    for x in a:
        rho = x % r
        n = [0] * r
        for i, v in enumerate(c):
            if v:
                for j in range(rho):
                    n[(i + j) % r] += v
        c = n
    return c

def bstar(r, a):
    D = sum(x - 1 for x in a)
    tau = _tau(r, a)
    pos = [j for j in range(1, r) if tau[j] > 0]
    mu = max(pos) if pos else 0
    T6 = 1 + (D + 1 - 2 * mu) // r
    s = (D + 1) % r
    return T6 - 2 if (tau[s] <= -2 and s >= 2 * mu) else T6

def domain(r, a):
    return r >= 4 and all(x % r for x in a) and sum(1 for x in a if 2 <= x % r <= r - 2) == 3

def predict(r, a, b):
    return b <= bstar(r, a)
