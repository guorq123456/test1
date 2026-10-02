"""
Synthesizer rule for unimodality of
    P(q) = [a_1]_q ... [a_k]_q * [b]_{q^r},   r >= 2, a_i >= 1, b >= 1.

predict(r, a, b) -> bool   (exact on the whole parameter space)
domain(r, a)     -> bool   (always True: the rule is exact everywhere)
closed_form_domain(r, a)   True where a closed form (no coefficient computation) decides every b
predict_closed(r, a, b)    the closed form, valid on closed_form_domain
unimodal_set(r, a)         the full set U(r,a) = {b : P unimodal} (finite unless r | some a_i)
structure_conjecture(r, a) checks Conjecture S2 (parity/gap) on (r,a)

Logic (see proof.txt for proofs):
  0. r | a_i for some i                       -> unimodal for all b              [C43 / Thm B]
  Otherwise let rho_i = a_i mod r, F = sum floor(a_i/r), D = sum (a_i - 1),
  Gamma_t = sum of coefficients of prod[a_i]_q in residue class t (mod r),
  mu = least t in [0,r-1] with Gamma_t >= Gamma_{t+1} >= ... >= Gamma_{r-1},
  T6 = 1 + floor((D + 1 - 2 mu)/r),   E6 = T6 - 1 - F  (always even, Lemma 7).
  1. b <= 1 + F                               -> unimodal                         [Thm B, = T1]
  2. b > T6                                   -> not unimodal                     [Thm C, = T6]
  3. at most two a_i with residue in [2, r-2] (always true for r <= 3)
                                              -> unimodal  (i.e. iff b <= T6)     [Thm E]
     (at most three a_i with residue outside {0,1}: T6 = 1+F, covered by 1-2)   [Thm D]
  4. otherwise: exact symmetrised criterion  h_m <= h_{K-m}  for all m in [1-rb, K/2),
     K = D + 1 - r(b+1)                                                           [Thm A]
"""
from functools import lru_cache


def _qint_prod(a):
    c = [1]
    for ai in a:
        if ai <= 1:
            continue
        L = len(c)
        pre = [0] * (L + 1)
        for i, x in enumerate(c):
            pre[i + 1] = pre[i] + x
        n = L + ai - 1
        c = [pre[min(j, L - 1) + 1] - pre[max(0, j - ai + 1)] for j in range(n)]
    return c


@lru_cache(maxsize=4096)
def _data(r, a):
    a = tuple(a)
    if any(x % r == 0 for x in a):
        return None
    A = _qint_prod(a)
    D = len(A) - 1
    G = [0] * r
    for i, x in enumerate(A):
        G[i % r] += x
    tau = [G[t] - G[(t - 1) % r] for t in range(r)]
    mu = r - 1
    while mu - 1 >= 0 and G[mu - 1] >= G[mu]:
        mu -= 1
    F = sum(x // r for x in a)
    T6 = 1 + (D + 1 - 2 * mu) // r
    M = D + 1 - r
    # g_n = [q^n] A(q)/[r]_q  (power series), n = 0..M
    g = [0] * max(M + 1, 0)
    for n in range(max(M + 1, 0)):
        d = (A[n] if n <= D else 0) - (A[n - 1] if 1 <= n <= D + 1 else 0)
        g[n] = d + (g[n - r] if n >= r else 0)
    nmid = sum(1 for x in a if (x % r) not in (0, 1, r - 1))
    return dict(A=A, D=D, G=G, tau=tau, mu=mu, F=F, T6=T6, M=M, g=g, nmid=nmid)


def _h2(dat, r, n):
    """2*h_n, the symmetrised (principal-value) coefficient of A/[r]_q."""
    tau, M, g = dat['tau'], dat['M'], dat['g']
    t = tau[n % r]
    if n < 0:
        return -t
    if n > M:
        return t
    return 2 * g[n] - t


def exact(r, a, b):
    """Theorem A: P unimodal <=> h_m <= h_{K-m} for all integers m with 1-rb <= m < K/2."""
    dat = _data(r, tuple(a))
    if dat is None:
        return True
    K = dat['D'] + 1 - r * (b + 1)
    m = 1 - r * b
    while 2 * m < K:
        if _h2(dat, r, m) > _h2(dat, r, K - m):
            return False
        m += 1
    return True


def closed_form_domain(r, a):
    a = tuple(a)
    if any(x % r == 0 for x in a):
        return True
    return r <= 3 or sum(1 for x in a if (x % r) not in (0, 1, r - 1)) <= 2


def predict_closed(r, a, b):
    """Closed form (Thm E): on closed_form_domain, unimodal iff r|a_i for some i or b <= 1+floor((D+1-2mu)/r)."""
    dat = _data(r, tuple(a))
    if dat is None:
        return True
    return b <= dat['T6']


def predict(r, a, b):
    a = tuple(a)
    dat = _data(r, a)
    if dat is None:
        return True                      # step 0
    if b <= 1 + dat['F']:
        return True                      # step 1
    if b > dat['T6']:
        return False                     # step 2
    if r <= 3 or dat['nmid'] <= 2:
        return True                      # step 3 (closed form)
    return exact(r, a, b)                # step 4


def domain(r, a):
    return True


def unimodal_set(r, a):
    dat = _data(r, tuple(a))
    if dat is None:
        return None  # all b
    return [b for b in range(1, dat['T6'] + 1) if predict(r, a, b)]


def structure_conjecture(r, a):
    """Conjecture S2: U = {1..B*} or {1..B*}\\{B*-1}, with B* = 1+F (mod 2)."""
    dat = _data(r, tuple(a))
    if dat is None:
        return True
    U = unimodal_set(r, a)
    Bs = max(U)
    miss = [b for b in range(1, Bs + 1) if b not in U]
    return (Bs - 1 - dat['F']) % 2 == 0 and miss in ([], [Bs - 1])


if __name__ == '__main__':
    print(unimodal_set(3, [2] * 6))                       # [1,2,3]
    print(unimodal_set(6, [2, 3, 3, 4, 4, 4, 5]))         # [1,3]
    print(predict(6, [2, 3, 4, 4, 4, 4, 4, 8], 4), predict(6, [2, 2, 3, 4, 4, 4, 4, 10], 4))  # True False
