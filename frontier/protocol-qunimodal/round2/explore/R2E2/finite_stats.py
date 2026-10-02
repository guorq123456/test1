# Finite a: distribution of (E6 - maxJ(a), gap?, Einf - maxJ(a)) over all multisets a with entries <= amax (r not dividing).
import sys, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import *
from limit import Jinf
from e6_vs_inf import E6
r, kmax, amax = map(int, sys.argv[1:4])
vals = [x for x in range(1, amax + 1) if x % r]
st = {}; cache = {}
for k in range(1, kmax + 1):
    for a in itertools.combinations_with_replacement(vals, k):
        a = list(a); rho = sorted(x % r for x in a)
        key = tuple(rho)
        if key not in cache: cache[key] = (Jinf(r, rho), E6(r, rho))
        Ji, e6 = cache[key]
        J = Jset(r, a); E = max(J)
        kk = (e6 - E, max(Ji) - E, J != list(range(E + 1)))
        st[kk] = st.get(kk, 0) + 1
print(r, kmax, amax, sorted(st.items()))
