# Test whether [0,E6-2] subset J(a) for instances with larger E6 (random multisets, fit box).
import sys, random
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import *
from limit import Jinf
from e6_vs_inf import E6
random.seed(int(sys.argv[1]))
st = {}; n = 0
for it in range(int(sys.argv[2])):
    r = random.randint(4, 9)
    k = random.randint(6, 16)
    # bias to large residues so E6 is big
    a = []
    for _ in range(k):
        rho = random.choice([random.randint(1, r - 1), r - 1, r - 2, random.randint(r // 2, r - 1)])
        if rho == 0: rho = 1
        a.append(rho + r * random.choice([0, 0, 0, 1, 1, 2, 3]))
    a.sort()
    rho = sorted(x % r for x in a)
    e6 = E6(r, rho)
    if e6 < 4: continue
    J = Jset(r, a); E = max(J)
    gap = J != list(range(E + 1))
    key = (e6, e6 - E, gap)
    st[key] = st.get(key, 0) + 1
    if not S2_shape(J) or e6 - E > 2: print("NOTE", r, a, "J", J, "E6", e6, flush=True)
print(sorted(st.items()))
