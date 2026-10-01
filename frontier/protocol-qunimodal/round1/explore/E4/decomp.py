#!/usr/bin/env python3
"""
Clebsch-Gordan peeling decomposition (candidate C4 in candidates.txt).

For A = [a_1]_q ... [a_k]_q (factors multiplied in the given order) build
    A = U + V
where
  * V = sum of centred chains q^j [L_j]_q, every L_j >= r*M + 1, M = sum floor(a_i/r);
  * U = sum of terms  q^e [c]_q H(q)  with r | c, c >= 1, H a product of q-integers.
Inductive step (proof file, Lemma 4): a chain q^j[L] (L = rM+1+e, e>=0) times [a'] (a' = rm'+s')
  is split at d0 = s' if s' <= e+1 else e+1 (capped at min(L,a')):
     top chains d < d0           -> V   (length L+a'-1-2d >= r(M+m')+1)
     q^{j+d0}[L-d0][a'-d0]       -> U   (r divides L-d0 or a'-d0).

This script (all r in 2..6, all sorted tuples a with k<=8, a_i<=12, i.e. inside the fit box):
  1. checks the exact polynomial identity A == U + V,
  2. checks every V chain has length >= rM+1,
  3. checks (assert) that every U term created has a factor [c] with r | c,
  4. optionally (--lemma K) for tuples with k <= K checks for every b <= min(M+1,60) that
     U(q)[b]_{q^r} and V(q)[b]_{q^r} are each unimodal (sanity check of Lemmas 2,3).
Prints counts.  Usage: python3 decomp.py [--lemma K]
"""
import sys
import numpy as np

AMAX, KMAX, BMAX = 12, 8, 60

def qint(n):
    return np.ones(n, dtype=object)

def mul(p, q):
    return np.convolve(p, q) if len(p) and len(q) else np.zeros(0, dtype=object)

def unimodal(c):
    i = 0; N = len(c) - 1
    while i < N and c[i] <= c[i+1]: i += 1
    while i < N and c[i] >= c[i+1]: i += 1
    return i == N

def times_bx(p, r, b):
    out = np.zeros(len(p) + r*(b-1), dtype=object)
    for y in range(b):
        out[r*y:r*y+len(p)] += p
    return out

stats = dict(nodes=0, identity_fail=0, vbound_fail=0, uterms=0, vchains_max=0,
             lemma_checks=0, lemma_fail_U=0, lemma_fail_V=0)

def step(state, ap, r):
    """state = (D, M, A, U, V) with V a dict j -> multiplicity (chain q^j [D+1-2j])."""
    D, M, A, U, V = state
    mp, sp = divmod(ap, r)
    D2, M2 = D + ap - 1, M + mp
    A2 = mul(A, qint(ap))
    U2 = mul(U, qint(ap)) if len(U) else np.zeros(D2 + 1, dtype=object)
    if len(U2) == 0:
        U2 = np.zeros(D2 + 1, dtype=object)
    V2 = {}
    for j, mu in V.items():
        L = D + 1 - 2*j
        e = L - r*M - 1
        assert e >= 0
        d0 = sp if sp <= e + 1 else e + 1
        n = min(L, ap)
        d0 = min(d0, n)
        for d in range(d0):                  # top chains -> V
            jj = j + d
            LL = D2 + 1 - 2*jj
            assert LL == L + ap - 1 - 2*d
            V2[jj] = V2.get(jj, 0) + mu
        if d0 < n:                           # remainder -> U
            c1, c2 = L - d0, ap - d0
            assert c1 % r == 0 or c2 % r == 0, (r, L, ap, d0)
            term = mul(qint(c1), qint(c2))
            U2[j + d0: j + d0 + len(term)] += mu * term
            stats['uterms'] += 1
    return (D2, M2, A2, U2, V2)

def Vpoly(D, V):
    p = np.zeros(D + 1, dtype=object)
    for j, mu in V.items():
        L = D + 1 - 2*j
        p[j:j+L] += mu
    return p

def dfs(state, start, k, r, lemmaK):
    D, M, A, U, V = state
    if k >= 1:
        stats['nodes'] += 1
        Vp = Vpoly(D, V)
        Up = U if len(U) == D + 1 else np.zeros(D + 1, dtype=object)
        if not np.array_equal(Up + Vp, A):
            stats['identity_fail'] += 1
        if V and min(D + 1 - 2*j for j in V) < r*M + 1:
            stats['vbound_fail'] += 1
        stats['vchains_max'] = max(stats['vchains_max'], len(V))
        if k <= lemmaK:
            for b in range(1, min(M + 1, BMAX) + 1):
                stats['lemma_checks'] += 1
                if not unimodal(times_bx(Up, r, b)): stats['lemma_fail_U'] += 1
                if not unimodal(times_bx(Vp, r, b)): stats['lemma_fail_V'] += 1
    if k == KMAX:
        return
    for ap in range(start, AMAX + 1):
        dfs(step(state, ap, r), ap, k + 1, r, lemmaK)

if __name__ == '__main__':
    lemmaK = 0
    if '--lemma' in sys.argv:
        lemmaK = int(sys.argv[sys.argv.index('--lemma') + 1])
    for r in range(2, 7):
        init = (0, 0, np.ones(1, dtype=object), np.zeros(1, dtype=object), {0: 1})
        dfs(init, 1, 0, r, lemmaK)
        print('r=%d done' % r, dict(stats), flush=True)
    print('FINAL', stats)
