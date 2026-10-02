# Test (Fold*): every integer u with Q_u < 0 (Q_u = d_u - tau_u two-sided; Q_u = -tau_u for u<0)
# satisfies (2u - sigma - 1) mod 2r in [r, 2r)  [equivalently u mod r in (omega - r/2, omega], omega=(sigma+1)/2].
# Also the weaker statement for tau alone (u<0): tau_t > 0 => t in window.
import sys, itertools, random
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import DS
from limit import tau
def inwin(u, sigma, r):
    return ((2 * u - sigma - 1) % (2 * r)) >= r
def check(r, a):
    ds = DS(r, a); tt = tau(r, a); D = ds.D
    sigma = sum((x % r) - 1 for x in a)
    badt = [t for t in range(r) if tt[t] > 0 and not inwin(t, sigma, r)]
    badq = [u for u in range(0, D + 2) if ds(u) - tt[u % r] < 0 and not inwin(u, sigma, r)]
    return badt, badq
tot = 0; ft = 0; fq = 0; ex = []
for r in range(2, 10):
    vals = [x for x in range(1, 2 * r + 4) if x % r]
    for k in range(1, 6 if r > 5 else 7):
        for a in itertools.combinations_with_replacement(vals, k):
            bt, bq = check(r, list(a)); tot += 1
            if bt: ft += 1
            if bq: fq += 1
            if (bt or bq) and len(ex) < 8: ex.append((r, a, bt, bq))
print("exhaustive tested", tot, "tau-window failures", ft, "Q-window failures", fq)
for e in ex: print("  ", e)
random.seed(3); tot = 0; ft = 0; fq = 0
for it in range(6000):
    r = random.randint(2, 30)
    if random.random() < 0.4:
        t = random.randint(1, 100); k = random.randint(1, 60)
        if t % r == 0: continue
        a = [t] * k
    else:
        a = [x for x in (random.randint(1, 100) for _ in range(random.randint(1, 30))) if x % r]
        if not a: continue
    if sum(x - 1 for x in a) > 2500: continue
    bt, bq = check(r, a); tot += 1
    if bt: ft += 1
    if bq: fq += 1
print("random tested", tot, "tau-window failures", ft, "Q-window failures", fq)
