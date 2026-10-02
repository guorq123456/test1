# Test (Par*): floor((2y* - D - 1)/r) == F (mod 2), y* = first negative coefficient of A(q)/[r]_q.
# Exhaustive over small ranges + random fit-box instances.  Usage: python3 test_parity_ystar.py
import sys, itertools, random
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import DS, Fval
def ystar(ds):
    y = 0
    while ds(y) >= 0: y += 1
    return y
tot = 0; bad = 0
for r in range(2, 10):
    vals = [x for x in range(1, 2 * r + 4) if x % r]
    for k in range(1, 6 if r > 5 else 7):
        for a in itertools.combinations_with_replacement(vals, k):
            a = list(a); ds = DS(r, a)
            y = ystar(ds); D = ds.D; F = Fval(r, a)
            tot += 1
            if ((2 * y - D - 1) // r - F) % 2: bad += 1; print("FAIL", r, a, y, D, F)
print("exhaustive: tested", tot, "failures", bad)
random.seed(7); tot2 = 0; bad2 = 0
for it in range(20000):
    r = random.randint(2, 30)
    if random.random() < 0.3:
        k = random.randint(1, 60); t = random.randint(1, 100)
        if t % r == 0: continue
        a = [t] * k
    else:
        k = random.randint(1, 40); a = [random.randint(1, 100) for _ in range(k)]
        a = [x for x in a if x % r]
        if not a: continue
    if sum(x - 1 for x in a) > 3000: continue
    ds = DS(r, a); y = ystar(ds); D = ds.D; F = Fval(r, a)
    tot2 += 1
    if ((2 * y - D - 1) // r - F) % 2: bad2 += 1; print("FAIL", r, sorted(a), y, D, F)
print("random: tested", tot2, "failures", bad2)
