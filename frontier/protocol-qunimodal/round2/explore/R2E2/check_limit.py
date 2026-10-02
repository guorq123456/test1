# Check: J(a) for a = rho + r*S (all parts lifted by S) equals Jinf(rho) when S large; report where it stabilizes.
import sys, itertools, random
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import *
from limit import *
random.seed(2)
mism = 0; tot = 0
for r in range(4, 9):
    for k in range(1, 7):
        for rho in itertools.combinations_with_replacement(range(1, r), k):
            rho = list(rho)
            ji = Jinf(r, rho)
            S = (sum(x - 1 for x in rho) + 2 * r) // r + 1  # lift so that min a_i > sigma+r
            a = [x + r * S for x in rho]
            if max(a) > 100: continue
            Ja = Jset(r, a)
            tot += 1
            if Ja != ji:
                mism += 1
                if mism < 10: print("mismatch", r, rho, "Jinf", ji, "J(a)", Ja, a)
print("tested", tot, "mismatches", mism)
