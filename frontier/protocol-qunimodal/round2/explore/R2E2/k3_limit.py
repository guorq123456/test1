# Residue-level statement for k<=3 in the large-part limit:  mu*_inf = max{u : f_u < tau_u} > omega - 2r.
# f = coeffs of 1/((1-q)^{k-1}(1-q^r)) (0 for u<0).  Report which u witnesses (negative u via tau>0, or u>=0).
import sys, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from limit import tau, dinf_seq
from fractions import Fraction as Fr
from collections import Counter
C = Counter(); bad = []
for r in range(2, 31):
    for k in (1, 2, 3):
        for rho in itertools.combinations_with_replacement(range(1, r), k):
            rho = list(rho); tt = tau(r, rho); sigma = sum(x - 1 for x in rho)
            omega = Fr(sigma + 1, 2)
            f = dinf_seq(k, r, sigma + 3 * r)
            fu = lambda u: f[u] if u >= 0 else 0
            # mu*_inf: search u from high to low
            ms = None
            for u in range(sigma + 2 * r, -3 * r, -1):
                if fu(u) < tt[u % r]: ms = u; break
            ok = ms is not None and ms > omega - 2 * r
            Einf = (sigma + 1 - 2 * r - 2 * ms) // r
            C[('k', k, 'ok', ok, 'Einf', Einf, 'witness<0', ms < 0)] += 1
            if not ok and len(bad) < 10: bad.append((r, rho, ms, omega, tt))
for k_, v in sorted(C.items(), key=str): print(k_, v)
for b in bad: print("  BAD", b)
