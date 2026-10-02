# Strong (k-independent) residue certificate covering any number of extra parts = 1 (mod r).
#  mu_neg(rho) = max{u<0 : tau_u > 0}  (a lower bound for mu*_inf for every number of extra residue-1 parts)
#  (O+_rho): ND_rho(K) for every K = sigma+1+r (mod 2r) with 2 mu_neg + 3r <= K <= sigma+1-2r
#  (TP_rho) and (E_rho) as in residue_check2 (they do not depend on residue-1 parts).
# Usage: python3 strong_check.py rmin rmax kmax  -> counts of rho' (parts in [2,r-1], 1<=k<=kmax) failing O+.
import sys, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import DS
from limit import tau
from residue_check import nd_ok
from residue_check2 import tp_rho
def mu_neg(r, tt):
    return max(u for u in range(-r, 0) if tt[u % r] > 0)
def strong(r, rho):
    ds = DS(r, rho); tt = tau(r, rho); sigma = sum(x - 1 for x in rho)
    mn = mu_neg(r, tt); okE = okO = True
    K = sigma + 1 - 2 * r
    while K >= 2 * mn:
        even = ((K - sigma - 1) % (2 * r)) == 0
        if even and not nd_ok(r, ds, tt, K): okE = False
        if (not even) and K >= 2 * mn + 3 * r and not nd_ok(r, ds, tt, K): okO = False
        K -= r
    return okE, okO, tp_rho(r, rho)
if __name__ == '__main__':
    rmin, rmax, kmax = map(int, sys.argv[1:4])
    for r in range(rmin, rmax + 1):
        tot = 0; fails = []
        for k in range(1, kmax + 1):
            for rho in itertools.combinations_with_replacement(range(2, r), k):
                tot += 1
                e, o, t = strong(r, list(rho))
                if not (e and o and t): fails.append((rho, e, o, t))
        print(f"r={r} k<={kmax}: rho' {tot}, strong-certificate failures {len(fails)}", fails[:4], flush=True)
