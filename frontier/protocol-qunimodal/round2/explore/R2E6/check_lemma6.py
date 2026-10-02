"""Numerical sanity check of Lemma 6: 0 < theta* < sigma1/2 (i.e. 0 < c < sigma1/r) for random residue
proportions with positive middle mass, r in [4,30]; and H(x) > ln(1+2x) on a grid."""
import sys, random, math
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E6')
from theory import H, Hinv
random.seed(3)
bad = 0; cmin = 1e9
for trial in range(20000):
    r = random.randint(4, 30)
    w = [random.random() ** 3 for _ in range(r - 1)]
    w[random.randint(1, r - 3)] += 0.05  # ensure middle mass
    tot = sum(w); p = [x / tot for x in w]  # p[s-1] = proportion of residue s
    sigma1 = sum(p[s - 1] * (s - 1) for s in range(1, r))
    L = max(sum(p[s - 1] * math.log(abs(math.sin(math.pi * j * s / r) / math.sin(math.pi * j / r))) if abs(math.sin(math.pi*j*s/r))>1e-12 else -1e9 for s in range(1, r)) for j in range(1, r))
    th = Hinv(L)
    if not (L > 0 and 0 < th < sigma1 / 2): bad += 1
    cmin = min(cmin, (sigma1 - 2 * th) / sigma1)
print("random distributions", 20000, "violations", bad, "min (sigma1-2theta*)/sigma1 = %.4f" % cmin)
print("H(x)-ln(1+2x) min on grid:", min(H(x) - math.log(1 + 2 * x) for x in [i / 1000 for i in range(1, 100001)]))
