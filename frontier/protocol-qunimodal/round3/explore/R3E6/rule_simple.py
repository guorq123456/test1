"""Candidate rule R_simple (four middle residues). Skeleton T6 (Gamma-level) + bounded low-order correction.
domain(r,a): r>=4, r divides no a_i, exactly four a_i with residue in [2,r-2], all others residue 1 or r-1.
Definitions: D = sum(a_i-1); A = prod [a_i]_q; B = (1-q)A; tau_t = sum_{j == t mod r} B_j;
mu = max{j in [1,r-1] : tau_j > 0} (0 if none); T6 = 1 + floor((D+1-2mu)/r);
g_i = sum_{m>=0} B_{i-rm} for i>=0 (coefficients of A/[r]_q), g_i = 0 for i<0.
For b in {T6-1, T6}: K = D+1-r(b+1), m0 = max(1, -floor((K-1)/2)).
  LOW(b) := [ g_{K+m} + tau_{(-m) mod r} >= 0 for all m in [m0, min(rb, m0+r)] ]
            and [ K < 1 or g_0 - g_K <= tau_0 ]      (g_0 = 1)
predict(r,a,b) = (b <= T6-2) or (b in {T6-1,T6} and LOW(b)).
Only g_0..g_{3r} are used, i.e. A mod q^(3r): the parts smaller than 3r and the number of parts.
Free parameters fitted: 0 (window length r chosen as the smallest of {0,1,3,r/2,r,2r} with 0 fit errors).
"""
import sys
sys.path.insert(0, '/tmp/claude-0/qu/explore3/R3E6')
from rule_low import domain, _data

def low(r, a, b):
    D, tau, mu, T6, g = _data(r, a)
    K = D+1-r*(b+1)
    G = lambda i: g[i] if i >= 0 else 0
    m0 = max(1, -((K-1)//2))
    for m in range(m0, min(r*b, m0+r)+1):
        if G(K+m) + tau[(-m) % r] < 0:
            return False
    if K >= 1 and 1 - g[K] > tau[0]:
        return False
    return True

def predict(r, a, b):
    a = sorted(a)
    D, tau, mu, T6, g = _data(r, a)
    if b <= T6-2: return True
    if b > T6: return False
    return low(r, a, b)
