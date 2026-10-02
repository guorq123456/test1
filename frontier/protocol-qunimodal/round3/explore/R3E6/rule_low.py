"""Candidate rule R_low (four middle residues): Gamma/tau-level skeleton + bounded low-order correction.
domain: r>=4, r divides no a_i, exactly four a_i with residue in [2,r-2], all others residue 1 or r-1.
Let D=sum(a_i-1), A=prod[a_i]_q, B=(1-q)A, tau_t = sum_{j==t mod r} B_j, mu = max{j in [1,r-1]: tau_j>0} (0 if none),
T6 = 1+floor((D+1-2mu)/r). g_n = sum_{m>=0} B_{n-rm} (coefficients of A/[r]_q), only n < 2r+W are used (rule_low_v1 lacked (ia): discarded)
(they depend only on A mod q^(2r+W), i.e. on the parts < 2r+W and the number of parts).
LOW(b): with K = D+1-r(b+1), g_i = 0 for i<0:
   (ia) with m0=max(1,-floor((K-1)/2)): for every m with m0<=m<=min(r*b, m0+W):  g_{K+m} >= -tau_{(-m) mod r}
   (ib) for every n with 0<=n<min(r*b-m0+1, W) and K+(r*b-n)>=0:  g_n + tau_{n mod r} + tau_{(K-n) mod r} >= 0
   (ii) for every j with 0<=j<=floor((K-1)/2):  g_j - g_{K-j} <= tau_{j mod r}   (K < 2r here)
predict(b): b<=T6-2, or (b in {T6-1,T6} and LOW(b)).
Free parameter: W (window), W = 2r here (fixed by convention, not fitted per instance).
"""
import sys
sys.path.insert(0,'/tmp/claude-0/qu/explore3/R3E6')
from core import Apoly

def domain(r, a):
    if r < 4 or any(x % r == 0 for x in a): return False
    res = [x % r for x in a]
    return sum(1 for s in res if 2 <= s <= r-2) == 4 and all(s in (1, r-1) or 2 <= s <= r-2 for s in res)

_cache = {}
def _data(r, a):
    key = (r, tuple(a))
    if key in _cache: return _cache[key]
    D = sum(x-1 for x in a)
    A = Apoly(a)
    B = [(A[j] if j <= D else 0) - (A[j-1] if j >= 1 else 0) for j in range(D+2)]
    tau = [0]*r
    for j, v in enumerate(B): tau[j % r] += v
    mu = max([j for j in range(1, r) if tau[j] > 0], default=0)
    T6 = 1 + (D+1-2*mu)//r
    L = 5*r
    g = [0]*L
    for n in range(L):
        g[n] = (B[n] if n <= D+1 else 0) + (g[n-r] if n >= r else 0)
    _cache[key] = (D, tau, mu, T6, g)
    return _cache[key]

def low(r, a, b, W=None):
    D, tau, mu, T6, g = _data(r, a)
    if W is None: W = 2*r
    K = D+1-r*(b+1)
    G = lambda i: g[i] if i >= 0 else 0
    # (i-a) j=-m, m small: g_{K+m} >= -tau_{-m}
    m0 = max(1, -((K-1)//2))   # j=-m <= floor((K-1)/2)
    for m in range(m0, min(r*b, m0+W)+1):
        if G(K+m) < -tau[(-m) % r]:
            return False
    # (i-b) j=-m with n=rb-m small: g_n + tau_n + tau_{K-n} >= 0  (valid when K+m>=0)
    for n in range(0, min(r*b-m0+1, W)):
        if K + (r*b - n) >= 0 and g[n] + tau[n % r] + tau[(K-n) % r] < 0:
            return False
    # (ii) 0<=j<=(K-1)/2: g_j - g_{K-j} <= tau_j
    for j in range(0, (K-1)//2 + 1):
        if g[j] - g[K-j] > tau[j % r]:
            return False
    return True

def predict(r, a, b):
    a = sorted(a)
    D, tau, mu, T6, g = _data(r, a)
    if b <= T6-2: return True
    if b > T6: return False
    return low(r, a, b)
