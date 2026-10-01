# RULE E (exact reformulation, proved in proof_e_identity.txt): 
# e(y) = Gamma_{y mod r} - H(y-r), H(n)=[q^n] A(q)/[r]_q (H(n)=0 for n<0).
# P unimodal <=> e(x) >= e(M-x) for all integers x < M/2, M=D+1-r(b-1).
# Only x with M-x <= D+r matter computationally (beyond that both sides periodic -> handled by
# reducing x: for x <= M-(D+1+r) the pair is compared using the periodic tails, see proof).
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import gamma
def domain(r, a):
    return True
def predict(r, a, b):
    a = sorted(a)
    G = gamma(r, a)
    D = sum(x-1 for x in a); M = D + 1 - r*(b-1)
    # A coefficients
    A = [1]
    for x in a:
        n = len(A)+x-1; B = [0]*n; s = 0
        for t in range(n):
            if t < len(A): s += A[t]
            if t-x >= 0 and t-x < len(A): s -= A[t-x]
            B[t] = s
        A = B
    L = D + 2*r + 2
    f = [(A[j] if j < len(A) else 0) - (A[j-1] if 0 <= j-1 < len(A) else 0) for j in range(L)]
    H = [0]*L
    for n in range(L):
        H[n] = f[n] + (H[n-r] if n >= r else 0)
    def Hx(n):
        if n < 0: return 0
        if n < L: return H[n]
        # for n >= D+1, H is r-periodic (= full class sums of f)
        return H[D+1 + ((n-(D+1)) % r)]
    def e(y):
        return G[y % r] - Hx(y-r)
    # x ranges over all integers < M/2; for x < M - (D+1+r) - r both x and M-x lie in
    # periodic regimes (x<r, M-x>=D+1+r) so it suffices to scan one extra period.
    lo = min(M - (D+1+r) - 2*r, -2*r)
    x = lo
    while 2*x < M:
        if e(x) < e(M-x):
            return False
        x += 1
    return True
