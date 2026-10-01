#!/usr/bin/env python3
"""
Discarded candidates C0 and C3, scored on the target domain b <= 1+M (M = sum floor(a_i/r))
inside the fit box (r in 2..6, k<=8, a_i<=12, b<=60).  "error" = domain instance the candidate
mechanism fails to certify.

C0 (Stanley product with one k=1 factor): certify iff some a_i >= r(b-1) or r | a_i
    (then [a_i]_q[b]_{q^r} is symmetric unimodal by Prop 5.3 and the remaining q-integers are
    symmetric unimodal, so the product is).  [The "split b-1 = sum (b_i-1)" version was discarded
    without computation: prod [b_i]_{q^r} != [b]_{q^r}.]
C3 (one-shot transfer identity, k=2 only): for a1 <= a2, a1 = r m1 + s1,
    [a1][a2] = [r m1][a2+s1] + q^{r m1}[s1][a2 - r m1];
    first piece good for all b (r | r m1, or zero if m1=0); certify iff the second piece times
    [b]_{q^r} is unimodal (checked numerically).  Only k=2 instances are scored.
"""
import itertools
import numpy as np

def unimodal(c):
    i = 0; N = len(c) - 1
    while i < N and c[i] <= c[i+1]: i += 1
    while i < N and c[i] >= c[i+1]: i += 1
    return i == N

def times_bx(p, r, b):
    out = np.zeros(len(p) + r*(b-1), dtype=np.int64)
    for y in range(b):
        out[r*y:r*y+len(p)] += p
    return out

tot0 = dict(domain=0, C0_err=0)
tot3 = dict(domain_k2=0, C3_err=0)
for r in range(2, 7):
    d0 = e0 = 0
    for k in range(1, 9):
        for a in itertools.combinations_with_replacement(range(1, 13), k):
            M = sum(x // r for x in a)
            bmax = min(M + 1, 60)
            div = any(x % r == 0 for x in a)
            amax = max(a)
            d0 += bmax
            if not div:
                # certified iff r(b-1) <= amax  <=> b <= amax//r + 1
                e0 += max(0, bmax - (amax // r + 1))
    d3 = e3 = 0
    for a1, a2 in itertools.combinations_with_replacement(range(1, 13), 2):
        m1, s1 = divmod(a1, r)
        M = a1 // r + a2 // r
        for b in range(1, min(M + 1, 60) + 1):
            d3 += 1
            if s1 == 0:
                continue
            rem = np.zeros(a1 + a2 - 1, dtype=np.int64)
            piece = np.convolve(np.ones(s1, dtype=np.int64), np.ones(a2 - r*m1, dtype=np.int64))
            rem[r*m1:r*m1 + len(piece)] += piece
            if not unimodal(np.trim_zeros(times_bx(rem, r, b))):
                e3 += 1
    print('r=%d C0: domain=%d err=%d | C3 (k=2): domain=%d err=%d' % (r, d0, e0, d3, e3), flush=True)
    tot0['domain'] += d0; tot0['C0_err'] += e0; tot3['domain_k2'] += d3; tot3['C3_err'] += e3
print('TOTAL', tot0, tot3)
