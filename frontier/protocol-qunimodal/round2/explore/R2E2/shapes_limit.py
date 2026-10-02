# Distribution of J_inf shapes: (E, has_gap) per r, for residue multisets with k<=kmax.
import sys, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from limit import Jinf
from lib import S2_shape
rmin, rmax, kmax = map(int, sys.argv[1:4])
for r in range(rmin, rmax + 1):
    st = {}; bad = 0
    for k in range(1, kmax + 1):
        for rho in itertools.combinations_with_replacement(range(1, r), k):
            J = Jinf(r, list(rho)); E = max(J)
            gap = J != list(range(E + 1))
            if not S2_shape(J): bad += 1; print("FAIL", r, rho, J)
            st[(E, gap)] = st.get((E, gap), 0) + 1
    print(r, kmax, "S2 fails", bad, sorted(st.items()), flush=True)
