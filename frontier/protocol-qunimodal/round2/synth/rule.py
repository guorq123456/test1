"""
Synthesis r2 rule for unimodality of
    P(q) = [a_1]_q ... [a_k]_q * [b]_{q^r},   r >= 2, a_i >= 1, b >= 1.

predict(r, a, b) -> bool   conjectural closed structure (Conjecture S2, pair form); exact on the
                           whole space iff S2 is true.  Proven parts are marked below.
domain(r, a)     -> bool   always True.
exact(r, a, b)   -> bool   PROVEN exact criterion (Theorem P / Theorem Q of proof.txt).
unimodal_set(r, a)         U(r,a) via the proven criterion (None means "all b").
pair_data(r, a)            the class-pair data (N*, beta, per-pair n*, margins).

Notation.  A(q) = prod [a_i]_q = sum alpha_x q^x, D = deg A, delta_x = alpha_x - alpha_{x-1}
(delta(q) = (1-q) A(q)), F = sum floor(a_i/r).  For every integer C with 0 < C < r and
C == D+1 (mod 2) ("class pair" C) let
    x_0 > x_1 > x_2 > ...  be the integers x >= 0 with D+1-2x == +-C (mod 2r) and D+1-2x > 0,
    i.e. Z_n = D+1-2x_n runs through C, 2r-C, 2r+C, 4r-C, 4r+C, ...,
    y_n = delta_{x_n} (>= 0),  A_n = y_0 - y_1 + ... + (-1)^n y_n,  a_n = (-1)^n A_n.
n*(C) = least n >= 0 with a_n < 0 (always n* == F+1 mod 2; infinite iff tau == 0 on the pair).
N* = min_C n*(C).
PROVEN (Theorem Q):  U = [1, N*]  u  {N*+2, N*+4, ..., beta}  with beta = min_C beta_C,
    beta_C = largest b == F+1 (mod 2) with a_{b'-2} + y_{b'} >= 0 for all b' == F+1, b' <= b.
    In particular N*+1 is never in U, every b <= N* is, and N*+2 is in U iff
    |a_{N*}| <= y_{N*+2} for every pair C with n*(C) = N*.
CONJECTURE S2 (open):  beta <= N*+2, i.e.  U = [1,N*]  or  U = [1,N*] u {N*+2}.
NOTE: the pair-local version (beta_C <= n*(C)+2 for every pair) is FALSE
      (r = 50000 example in proof.txt, Section 10); S2 itself survives there.
"""
from functools import lru_cache


def _qint_prod(a):
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
        c = [pre[min(j, L - 1) + 1] - pre[max(0, j - ai + 1)] for j in range(n)]
    return c


@lru_cache(maxsize=2048)
def pair_data(r, a):
    a = tuple(a)
    if any(x % r == 0 for x in a):
        return None                      # tau == 0: every b unimodal (C43)
    A = _qint_prod(a)
    D = len(A) - 1
    F = sum(x // r for x in a)

    def dl(x):
        if x < 0 or x > D + 1:
            return 0
        return (A[x] if x <= D else 0) - (A[x - 1] if x >= 1 else 0)

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
        for n, v in enumerate(y):
            s += v if n % 2 == 0 else -v
            As.append(s)

        def aa(m, As=As):
            v = As[m] if m < len(As) else As[-1]
            return v if m % 2 == 0 else -v

        def yy(m, y=y):
            return y[m] if m < len(y) else 0
        ns = next((m for m in range(len(As)) if aa(m) < 0), None)
        if ns is None:
            continue
        b = ns + 2
        while aa(b - 2) + yy(b) >= 0:
            b += 2
        pairs.append(dict(C=C, nstar=ns, beta=b - 2,
                          a_n=aa(ns), y1=yy(ns + 1), y2=yy(ns + 2), y4=yy(ns + 4)))
    Nst = min(p['nstar'] for p in pairs)
    beta = min(p['beta'] for p in pairs)
    return dict(D=D, F=F, Nstar=Nst, beta=beta, pairs=pairs)


def exact(r, a, b):
    """PROVEN: P unimodal <=> b <= N*, or b == N* (mod 2) and N*+2 <= b <= beta."""
    d = pair_data(r, tuple(a))
    if d is None:
        return True
    N, beta = d['Nstar'], d['beta']
    return b <= N or ((b - N) % 2 == 0 and b <= beta)


def predict(r, a, b):
    """Conjecture S2 (pair form): U = [1,N*] u ({N*+2} if |a_{N*}| <= y_{N*+2} on every binding pair)."""
    d = pair_data(r, tuple(a))
    if d is None:
        return True                                   # r | a_i  [proved]
    N = d['Nstar']
    if b <= N:
        return True                                   # [proved]
    if b == N + 2:                                    # [proved]
        return all(-p['a_n'] <= p['y2'] for p in d['pairs'] if p['nstar'] == N)
    return False                                      # b == N+1 or b >= N+3: [proved for b == F mod 2]; S2 for b >= N+4


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
    print(unimodal_set(3, (2,) * 6))                       # [1, 2, 3]
    print(unimodal_set(6, (2, 3, 3, 4, 4, 4, 5)))          # [1, 3]
    print(unimodal_set(6, (2, 3, 4, 4, 4, 4, 4, 8)), unimodal_set(6, (2, 2, 3, 4, 4, 4, 4, 10)))  # [1,2,4] [1,2]
