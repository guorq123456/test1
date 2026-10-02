# In the limit criterion  h_x <= h_{K-x} (x < K/2), h_x = f_x - tau_x/2 (f_x=0 for x<0),
# list failing pairs for the first j beyond J_inf and for gaps.
import sys, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from limit import dinf_seq, tau, Jinf
from fractions import Fraction

def hfun(r, rho):
    k = len(rho); sigma = sum(x - 1 for x in rho)
    tt = tau(r, rho)
    L = sigma + 4 * r + 10
    dd = dinf_seq(k, r, L)
    def h(x):
        return Fraction(dd[x] if x >= 0 else 0) - Fraction(tt[x % r], 2)
    return h, sigma, tt

def fails(r, rho, j):
    h, sigma, tt = hfun(r, rho)
    K = sigma + 1 - r * (j + 2)
    out = []
    x = (K - 1) // 2
    lo = min(x, -1) - 3 * r
    while x >= lo:
        if h(x) > h(K - x): out.append((x, K - 2 * x))
        x -= 1
    return out, K

if __name__ == '__main__':
    r, k = int(sys.argv[1]), int(sys.argv[2])
    for rho in itertools.combinations_with_replacement(range(1, r), k):
        rho = list(rho)
        J = Jinf(r, rho); E = max(J)
        h, sigma, tt = hfun(r, rho)
        f1, K1 = fails(r, rho, E + 1)
        f2, K2 = fails(r, rho, E + 2)
        print(rho, "sigma", sigma, "tau", tt, "J", J, "| j=E+1 K", K1, "fails(x,gap)", f1[:6], "| j=E+2 K", K2, f2[:4])
