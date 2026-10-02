# Equal small parts a=(t^k), r given: J(a), E6, Bad, P-failures, sub-claims; k up to 60 (all equal -> allowed).
import sys
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import *
from limit import tau
from decomp import *
from structure_helpers import mu_of
r, t, kmax = map(int, sys.argv[1:4])
for k in range(1, kmax + 1):
    a = [t] * k
    ds = DS(r, a); tt = tau(r, a); bad = bad_set(r, a, ds, tt)
    sigma = sum(x - 1 for x in a); mu = mu_of(tt, r); e6 = (sigma + 1 - 2 * mu) // r
    J = Jset(r, a)
    pf = []
    K = (sigma + 1) % r
    while K <= sigma + 1 - 2 * r:
        if not P_ok(r, ds, tt, K): pf.append(K)
        K += r
    print(f"k={k} sigma={sigma} mu={mu} E6={e6} J={J} S2={S2_shape(J)} Bad={bad} Pfail K={pf} K'={sigma+1-r*(e6+1)}")
