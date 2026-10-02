# Claim A (small parts): for a with all a_i in [1,r-1], J(a) contains [0,E6-2]; also record full shape stats.
import sys, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import *
from e6_vs_inf import E6
r, kmax = int(sys.argv[1]), int(sys.argv[2])
st = {}; bad = 0
for k in range(1, kmax + 1):
    for a in itertools.combinations_with_replacement(range(1, r), k):
        a = list(a); e6 = E6(r, a)
        J = Jset(r, a); E = max(J)
        ok = set(range(max(0, e6 - 1))) <= set(J) and E <= e6
        if not ok:
            bad += 1
            if bad < 10: print("CLAIM A FAIL", r, a, J, e6)
        key = (e6 - E, J != list(range(E + 1)))
        st[key] = st.get(key, 0) + 1
print(f"r={r} kmax={kmax} claimA fails {bad}", sorted(st.items()), flush=True)
