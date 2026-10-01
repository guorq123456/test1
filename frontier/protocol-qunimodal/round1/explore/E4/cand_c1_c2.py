#!/usr/bin/env python3
"""
Candidates C1 and C2 (both discarded / superseded), evaluated on the target domain
   b <= 1 + M,  M = sum floor(a_i/r),  inside the fit box.

alpha_j = A_j - A_{j-1} (0 <= j <= D/2) is the Lambda (chain) decomposition of A = prod [a_i]_q:
   A = sum_j alpha_j q^j [L_j]_q,  L_j = D+1-2j.
A single chain q^j[L][b]_{q^r} is unimodal iff L >= r(b-1) or r | L  (Prop 5.3 of the paper).

C1 ("chain by chain"): certify P unimodal iff every chain with alpha_j>0 is individually good.
C2 ("runs"): certify iff alpha = sum of nonnegative integer multiples of
     - singletons {j} with chain j individually good,
     - runs {s,...,s+t-1} (t>=2) with r | t  or  r | (L_s - t + 1)
       (such a run equals q^s [c][n] with r | c, hence is good for every b).
   Feasibility decided exactly with z3 (integer program).  Only run for k <= KC2.
Usage: python3 cand_c1_c2.py KC2
"""
import sys, itertools
import numpy as np
from z3 import Int, Solver, Sum, sat

KC2 = int(sys.argv[1]) if len(sys.argv) > 1 else 4

def Apoly(a):
    c = np.ones(1, dtype=np.int64)
    for x in a:
        c = np.convolve(c, np.ones(x, dtype=np.int64))
    return c

def chain_good(L, r, b):
    return L >= r*(b-1) or L % r == 0

def c2_feasible(alpha, D, r, b):
    J = len(alpha)
    Ls = [D + 1 - 2*j for j in range(J)]
    good = [chain_good(Ls[j], r, b) for j in range(J)]
    runs = []
    for s in range(J):
        for t in range(2, J - s + 1):
            if t % r == 0 or (Ls[s] - t + 1) % r == 0:
                runs.append((s, t))
    xs = [Int('x%d' % i) for i in range(len(runs))]
    S = Solver()
    for x in xs: S.add(x >= 0)
    for j in range(J):
        cov = [xs[i] for i, (s, t) in enumerate(runs) if s <= j < s + t]
        tot = Sum(cov) if cov else 0
        if good[j]:
            S.add(tot <= alpha[j])
        else:
            S.add(tot == alpha[j])
    return S.check() == sat

res = {}
for r in range(2, 7):
    n_dom = n_c1_fail = 0
    n_dom_c2 = n_c2_fail = n_c1_fail_k = 0
    for k in range(1, 9):
        for a in itertools.combinations_with_replacement(range(1, 13), k):
            A = Apoly(a); D = len(A) - 1
            J = D // 2 + 1
            alpha = [int(A[j] - (A[j-1] if j > 0 else 0)) for j in range(J)]
            M = sum(x // r for x in a)
            bmax = min(M + 1, 60)
            n_dom += bmax
            bad = [D + 1 - 2*j for j in range(J) if alpha[j] > 0 and (D + 1 - 2*j) % r != 0]
            # C1 fails at b iff some bad length L has L < r(b-1), i.e. b >= floor(Lmin/r)+2
            if bad:
                n_c1_fail += max(0, bmax - (min(bad) // r + 1))
            if k <= KC2:
                for b in range(1, bmax + 1):
                    n_dom_c2 += 1
                    ok1 = all(chain_good(D + 1 - 2*j, r, b) for j in range(J) if alpha[j] > 0)
                    if not ok1:
                        n_c1_fail_k += 1
                        if not c2_feasible(alpha, D, r, b):
                            n_c2_fail += 1
    res[r] = dict(domain=n_dom, C1_fail=n_c1_fail, domain_kle=n_dom_c2,
                  C1_fail_kle=n_c1_fail_k, C2_fail_kle=n_c2_fail)
    print('r=%d' % r, res[r], flush=True)
tot = {key: sum(res[r][key] for r in res) for key in res[2]}
print('TOTAL (k<=%d for C2 columns)' % KC2, tot)
