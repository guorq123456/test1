"""Candidate rule R_gen (four middle residues): residue-level closed form.
Same as rule_simple, but the low-order coefficients g_i are replaced by their 'generic' values
f_i = coefficients of 1/((1-q)^(k'-1) (1-q^r)), k' = #{i : a_i >= 2} (parts equal to 1 are trivial and dropped).
So predict depends only on r, the residue multiset of the nontrivial parts (via tau and k'), and D (equivalently F).
domain: r>=4, r divides no a_i, exactly four a_i with residue in [2,r-2], others residue 1 or r-1.
predict(r,a,b) = b<=T6-2 or (b in {T6-1,T6} and LOW_f(b)), with
LOW_f(b): K = D+1-r(b+1), m0 = max(1,-floor((K-1)/2));
   f_{K+m} + tau_{(-m) mod r} >= 0 for all m in [m0, min(rb, m0+r)]  (f at negative index = 0)
   and (K < 1 or 1 - f_K <= tau_0).
T6 = 1+floor((D+1-2mu)/r), mu = max{j in [1,r-1]: tau_j>0}, tau = (1-q) prod [a_i mod r]_q reduced mod q^r-1.
Free parameters fitted: 0.
"""
from math import comb
def domain(r, a):
    if r < 4 or any(x % r == 0 for x in a): return False
    res = [x % r for x in a]
    return sum(1 for s in res if 2 <= s <= r-2) == 4
def _tau(r, a):
    c = [1]+[0]*(r-1)
    for A in a:
        s = A % r; d = [0]*r
        for i, v in enumerate(c):
            if v:
                for j in range(s): d[(i+j) % r] += v
        c = d
    return [c[t]-c[t-1] for t in range(r)]
def _f(r, kp, L):
    # coefficients of 1/((1-q)^(kp-1)(1-q^r)) up to L
    e = [comb(i+kp-2, i) if kp >= 2 else (1 if i == 0 else 0) for i in range(L)]
    f = [0]*L
    for i in range(L): f[i] = e[i] + (f[i-r] if i >= r else 0)
    return f
def predict(r, a, b):
    a = [x for x in a if x != 1]
    kp = len(a)
    D = sum(x-1 for x in a); tau = _tau(r, a)
    mu = max([j for j in range(1, r) if tau[j] > 0], default=0)
    T6 = 1 + (D+1-2*mu)//r
    if b <= T6-2: return True
    if b > T6: return False
    K = D+1-r*(b+1); m0 = max(1, -((K-1)//2))
    f = _f(r, kp, max(4*r, K+m0+r+2))
    G = lambda i: f[i] if i >= 0 else 0
    for m in range(m0, min(r*b, m0+r)+1):
        if G(K+m) + tau[(-m) % r] < 0: return False
    if K >= 1 and 1 - f[K] > tau[0]: return False
    return True
