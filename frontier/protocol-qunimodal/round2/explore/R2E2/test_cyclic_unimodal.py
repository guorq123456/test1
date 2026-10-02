# Test Lemma (cyclic unimodality): Gamma = prod [rho_i]_q mod (q^r - 1) satisfies, with c = sigma/2:
#   Gamma(t) >= Gamma(t') whenever cdist(t, c) <= cdist(t', c)   (cdist = distance on R/rZ).
import sys, itertools, random
from fractions import Fraction as Fr
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import polyA
def cdist(t, c, r):
    x = (Fr(t) - c) % r
    return min(x, r - x)
def check(r, rho):
    c = polyA(rho); G = [0] * r
    for i, v in enumerate(c): G[i % r] += v
    cen = Fr(sum(x - 1 for x in rho), 2)
    ds = [cdist(t, cen, r) for t in range(r)]
    for t in range(r):
        for u in range(r):
            if ds[t] <= ds[u] and G[t] < G[u]: return False
    return True
tot = 0; bad = 0
for r in range(2, 13):
    for k in range(1, 7 if r <= 8 else 5):
        for rho in itertools.combinations_with_replacement(range(1, r), k):
            tot += 1
            if not check(r, list(rho)): bad += 1; print("FAIL", r, rho)
random.seed(5)
for it in range(3000):
    r = random.randint(2, 30); k = random.randint(1, 40)
    rho = [random.randint(1, r - 1) for _ in range(k)] if r > 1 else [1]
    tot += 1
    if not check(r, rho): bad += 1; print("FAIL", r, rho)
print("tested", tot, "failures", bad)
