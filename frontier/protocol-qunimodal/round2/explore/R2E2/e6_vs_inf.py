# Compare E_inf = max J_inf(rho) with E6 = floor((sigma+1-2mu)/r) (mu from tau(rho)).
import sys, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from limit import Jinf, tau
def E6(r, rho):
    t = tau(r, rho); sigma = sum(x - 1 for x in rho)
    mu = r - 1
    for m in range(r):
        if all(t[s] <= 0 for s in range(m + 1, r)): mu = m; break
    return (sigma + 1 - 2 * mu) // r
if __name__ == '__main__':
    r, kmax = int(sys.argv[1]), int(sys.argv[2])
    st = {}
    for k in range(1, kmax + 1):
        for rho in itertools.combinations_with_replacement(range(1, r), k):
            rho = list(rho); J = Jinf(r, rho); E = max(J); e6 = E6(r, rho)
            key = (e6 - E, J != list(range(E + 1)))
            st[key] = st.get(key, 0) + 1
            if e6 < E or e6 % 2: print("ANOMALY", rho, J, e6)
    print(r, kmax, sorted(st.items()))
