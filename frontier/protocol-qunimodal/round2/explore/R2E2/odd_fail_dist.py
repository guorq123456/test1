# Small parts: for odd-family K (any K <= sigma+1-2r), where does ND_rho fail, relative to 2mu*_inf and 2mu*(rho)?
import sys, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import DS
from limit import tau
from residue_check import mustar_inf, nd_ok
from s3star import estar
from collections import Counter
r, kmax = int(sys.argv[1]), int(sys.argv[2])
C = Counter(); ex = {}
for k in range(1, kmax + 1):
    for rho in itertools.combinations_with_replacement(range(1, r), k):
        rho = list(rho); ds = DS(r, rho); tt = tau(r, rho); sigma = sum(x - 1 for x in rho)
        msi = mustar_inf(r, rho, tt); E, msr, bad = estar(r, rho, ds, tt)
        K = sigma + 1 - 2 * r
        while K >= -4 * r:
            even = ((K - sigma - 1) % (2 * r)) == 0
            if not even and not nd_ok(r, ds, tt, K):
                key = ('K-2mu*inf', (K - 2 * msi) // r, 'K-2mu*rho', (K - 2 * msr) // r)
                C[key] += 1
                if key not in ex: ex[key] = (rho, K, msi, msr)
            K -= r
print(r, kmax)
for k_, v in sorted(C.items()): print("  ", k_, v, ex[k_])
