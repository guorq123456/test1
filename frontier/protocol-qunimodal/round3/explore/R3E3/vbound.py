# Rigorous integer upper bound for |tau_t| = |(1/r) sum_{j=1}^{r-1} zeta^{-jt}(1-zeta^j) A(zeta^j)|,
# maximized over residue configurations with k' parts >= 2 (residue 1 parts of size>=r+1 included),
# using |[a]_zeta| = |sin(pi j a/r)/sin(pi j/r)| (depends on a mod r only).
# For each j we bound |A(zeta^j)| by M_j^{k'} with M_j = max over residues rho in [1,r-1] of |[rho]_{zeta^j}|
# EXCEPT that we take the max over the joint choice: max over residue vectors of sum_j |1-z^j| prod_i |[rho_i]_{z^j}|
# is bounded by max over a single residue rho repeated? Not valid in general -> we use the safe bound
#   sum_j |1-z^j| * M_j^{k'}  (each j maximized separately), then floor after adding 1e-20 relative slack.
import mpmath as mp
from functools import lru_cache
mp.mp.dps=60
@lru_cache(None)
def Mj(r,j):
    return max(abs(mp.sin(mp.pi*j*rho/r)/mp.sin(mp.pi*j/r)) for rho in range(1,r))
@lru_cache(None)
def vmax(r,k):
    s=mp.mpf(0)
    for j in range(1,r):
        s+=abs(1-mp.e**(2j*mp.pi*j/r))*Mj(r,j)**k
    v=s/r
    return int(mp.floor(v*(1+mp.mpf(10)**-40)))
if __name__=='__main__':
    for r in (4,5,6):
        print(r,[vmax(r,k) for k in range(1,16)])
