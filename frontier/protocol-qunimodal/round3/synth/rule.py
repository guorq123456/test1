"""
Synthesis r3 rule for unimodality of
    P(q) = [a_1]_q ... [a_k]_q * [b]_{q^r},   r >= 2, a_i >= 1, b >= 1.

predict(r, a, b) -> bool   strongest conjecture (S2, class-pair form).  It is EXACT on the whole space iff
                           Conjecture S2 holds; it is PROVED exact for r <= 6, for <= 3 parts >= 2, on the flat
                           domain (<= 2 middle residues), for exactly three middle residues (others +-1 mod r),
                           whenever r | some a_i, and for every b <= N*+2 (all r, all a).
domain(r, a)     -> bool   always True (rule defined for every r >= 2, a_i >= 1).
exact(r, a, b)   -> bool   PROVED exact criterion (Theorem 4.2 of synth/r2/proof.txt = Thm 1 of r3/proof.txt).
unimodal_set(r, a)         U(r,a) by the proved criterion (None means: all b).
pair_data(r, a)            class-pair data (N*, beta, Delta, per-pair n*).
closed_form(r, a)          proved aggregate closed forms where they exist (C43, flat, three-middle); else None.

Notation.  A(q) = prod [a_i]_q = sum alpha_x q^x, D = deg A, delta = (1-q)A, F = sum floor(a_i/r).
Class pair C: 0 < C < r, C == D+1 (mod 2); points x_n = (D+1-Z_n)/2, Z_n = C, 2r-C, 2r+C, 4r-C, ... (Z_n <= D+1);
y_n = delta_{x_n} >= 0;  A_n = y_0 - y_1 + ... + (-1)^n y_n;  a_n = (-1)^n A_n;  n*(C) = least n with a_n < 0.
N* = min_C n*(C);  Delta = min_{C : n*(C) = N*} ( y_{N*+2} + a_{N*} ).
PROVED:     U = [1,N*] u {N*+2, N*+4, ..., beta},  N*+2 in U  <=>  Delta >= 0.
CONJECTURE S2:  beta <= N*+2, i.e.  U = [1,N*]  or  U = [1,N*] u {N*+2}.

r3 additions.  d(q) := prod[a_i]_q / [r]_q (power series), y* := least y with [q^y]d < 0,
    Bd := 1 + floor((2y* - D - 1)/r).
PROVED (r3 Theorem 3):  Bd == F+1 (mod 2)  and  N* <= beta = max U <= Bd <= T6.
STRONGEST CONJECTURE (O):  N* >= Bd - 2   (implies S2), i.e.
    [1, Bd-2] c U c [1, Bd],   U in { [1,Bd], [1,Bd] minus {Bd-1}, [1,Bd-2] }  (P_{Bd-3} unimodal).
REFUTED (M): beta = Bd = max U is FALSE: r=500, k=39 and k=41 (M_counterexamples.txt), brute force: max U = Bd-2.
    So SC = (O)+(M) is false, and max U is not always given by Bd.
predict    = (O)-form: True for b <= Bd-2, exact test at b in {Bd-1, Bd}, False for b > Bd.
             It is exact iff (O) holds.
predict_sc = full SC (REFUTED, kept for reference): b <= Bd and (b != Bd-1 or exact(Bd-1)).
predict_s2 = the r2 S2 pair form.
"""
from functools import lru_cache


def _qint_prod(a, upto=None):
    c = [1]
    for ai in a:
        if ai <= 1:
            continue
        L = len(c)
        pre = [0] * (L + 1)
        s = 0
        for i, x in enumerate(c):
            s += x
            pre[i + 1] = s
        n = L + ai - 1
        if upto is not None:
            n = min(n, upto + 1)
        c = [pre[min(j, L - 1) + 1] - pre[max(0, j - ai + 1)] for j in range(n)]
    return c


@lru_cache(maxsize=4096)
def pair_data(r, a):
    a = tuple(a)
    if any(x % r == 0 for x in a):
        return None                      # C43: every b unimodal
    D = sum(x - 1 for x in a)
    F = sum(x // r for x in a)
    X = (D + 1) // 2
    A = _qint_prod(a, upto=X)            # alpha_0..alpha_X suffice (palindromic)
    A += [0] * (X + 1 - len(A))

    def dl(x):                           # delta_x for 0 <= x <= (D+1)/2
        return A[x] - (A[x - 1] if x >= 1 else 0)

    pairs = []
    for C in range(1, r):
        if (C - (D + 1)) % 2:
            continue
        y = []
        n = 0
        while True:
            Z = (n // 2) * 2 * r + (C if n % 2 == 0 else 2 * r - C)
            if Z > D + 1:
                break
            y.append(dl((D + 1 - Z) // 2))
            n += 1
        y += [0] * 8
        As, s = [], 0
        for m, v in enumerate(y):
            s += v if m % 2 == 0 else -v
            As.append(s)

        def aa(m, As=As):
            v = As[m] if m < len(As) else As[-1]
            return v if m % 2 == 0 else -v

        def yy(m, y=y):
            return y[m] if m < len(y) else 0
        ns = next((m for m in range(len(As)) if aa(m) < 0), None)
        if ns is None:
            continue
        bb = ns + 2
        while aa(bb - 2) + yy(bb) >= 0:
            bb += 2
        pairs.append(dict(C=C, nstar=ns, beta=bb - 2, a_n=aa(ns), y2=yy(ns + 2)))
    Nst = min(p['nstar'] for p in pairs)
    beta = min(p['beta'] for p in pairs)
    Delta = min(p['y2'] + p['a_n'] for p in pairs if p['nstar'] == Nst)
    return dict(D=D, F=F, Nstar=Nst, beta=beta, Delta=Delta, pairs=pairs)


@lru_cache(maxsize=4096)
def Bd(r, a):
    """Bd = 1 + floor((2y*-D-1)/r), y* = first negative coefficient of prod[a_i]_q/[r]_q (None if r | some a_i)."""
    a = tuple(a)
    if any(x % r == 0 for x in a):
        return None
    D = sum(x - 1 for x in a)
    X = (D + 1) // 2
    A = _qint_prod(a, upto=X)
    A += [0] * (X + 1 - len(A))

    def dl(x):
        if x < 0 or x > D + 1:
            return 0
        if x <= X:
            return A[x] - (A[x - 1] if x >= 1 else 0)
        return -dl(D + 1 - x)
    acc = [0] * r
    y = 0
    while True:
        acc[y % r] += dl(y)
        if acc[y % r] < 0:
            return 1 + (2 * y - D - 1) // r
        y += 1


def exact(r, a, b):
    """PROVED: unimodal <=> b <= N*, or (b == N* mod 2 and N*+2 <= b <= beta)."""
    d = pair_data(r, tuple(a))
    if d is None:
        return True
    N, beta = d['Nstar'], d['beta']
    return b <= N or ((b - N) % 2 == 0 and b <= beta)


# ---------- proved closed forms (used only as fast paths / cross-checks) ----------
def _gamma_mu(r, a):
    """mu = least t in 0..r-1 with Gamma_t >= Gamma_{t+1} >= ... >= Gamma_{r-1}; Gamma from residues only."""
    g = [1] + [0] * (r - 1)                    # prod [rho_i]_q mod (q^r - 1), rho_i = a_i mod r
    for x in a:
        s = x % r
        if s <= 1:
            continue
        ng = [0] * r
        for t in range(r):
            if g[t]:
                for j in range(s):
                    ng[(t + j) % r] += g[t]
        g = ng
    t = r - 1
    while t - 1 >= 0 and g[t - 1] >= g[t]:
        t -= 1
    return g, t


def T6(r, a):
    D = sum(x - 1 for x in a)
    _, mu = _gamma_mu(r, a)
    return 1 + (D + 1 - 2 * mu) // r


def closed_form(r, a):
    """Returns U as ('all',) or ('interval', B) when a PROVED aggregate closed form applies, else None.
    C43: r | a_i.  Flat domain (r1 Thm E): <= 2 parts with residue in [2, r-2]  =>  U = [1, T6].
    r = 2 (T5) and r = 3 (T2) are contained in the flat domain statement up to the T2 formula (checked)."""
    if any(x % r == 0 for x in a):
        return ('all',)
    mid = [x for x in a if 2 <= x % r <= r - 2]
    if len(mid) <= 2:
        return ('interval', T6(r, a))
    return None


def predict(r, a, b):
    """Conjecture (O) form: U contains [1,Bd-2], U is contained in [1,Bd] (proved); exact test at Bd-1 and Bd."""
    a = tuple(a)
    cf = closed_form(r, a)
    if cf is not None:
        return True if cf[0] == 'all' else b <= cf[1]
    if b <= 1 + sum(x // r for x in a):
        return True                                   # T1 (proved)
    B = Bd(r, a)
    if b > B:
        return False                                  # Theorem 3 (proved)
    if b <= B - 2:
        return True                                   # conjecture (O)
    return exact(r, a, b)                             # proved criterion at b = Bd-1, Bd


def predict_sc(r, a, b):
    """Full Conjecture SC: U = [1,Bd] or [1,Bd] minus {Bd-1}."""
    a = tuple(a)
    B = Bd(r, a)
    if B is None:
        return True
    if b > B:
        return False
    if b == B - 1:
        return exact(r, a, b)
    return True


def predict_s2(r, a, b):
    """Conjecture S2 (class-pair form): U = [1,N*] u ({N*+2} if Delta >= 0)."""
    a = tuple(a)
    cf = closed_form(r, a)
    if cf is not None:
        return True if cf[0] == 'all' else b <= cf[1]
    F = sum(x // r for x in a)
    if b <= 1 + F:
        return True                                   # T1 (proved)
    if b > T6(r, a):
        return False                                  # T6 (proved)
    d = pair_data(r, a)
    N = d['Nstar']
    if b <= N:
        return True
    if b == N + 2:
        return d['Delta'] >= 0
    return False                                      # b == N*+1: proved; b >= N*+3: proved unless b == N* mod 2 (S2)


def domain(r, a):
    return True


def unimodal_set(r, a):
    d = pair_data(r, tuple(a))
    if d is None:
        return None
    N, beta = d['Nstar'], d['beta']
    return list(range(1, N + 1)) + list(range(N + 2, beta + 1, 2))


def s2_holds(r, a):
    d = pair_data(r, tuple(a))
    return d is None or d['beta'] <= d['Nstar'] + 2


if __name__ == '__main__':
    print(unimodal_set(3, (2,) * 6))                                  # [1, 2, 3]
    print(unimodal_set(6, (2, 3, 3, 4, 4, 4, 5)))                     # [1, 3]
    print(unimodal_set(6, (2, 3, 4, 4, 4, 4, 4, 8)), unimodal_set(6, (2, 2, 3, 4, 4, 4, 4, 10)))
    print(unimodal_set(20, (1, 14, 59, 65, 79, 105, 123)), unimodal_set(20, (3, 14, 21, 59, 65, 79, 205)))
