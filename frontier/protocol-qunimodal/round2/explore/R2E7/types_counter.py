# Random residue multisets (r<=30, k<=40): compare rule_types.shape with rule_B4.Uinf; print counterexamples
# and classify which part of the conjecture fails.  Usage: python3 types_counter.py SEED N
import sys, random
from collections import Counter
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E7')
from rule_B4 import Uinf, _tau
from rule_types import shape
rng = random.Random(int(sys.argv[1])); C = Counter(); n = 0; shown = 0
for _ in range(int(sys.argv[2])):
    r = rng.randint(4, 30); k = rng.choice([4, 5, 6, 8, 10, 12, 16, 20, 30, 40])
    res = sorted(rng.randint(1, r-1) for _ in range(k)); n += 1
    U = Uinf(r, res); Sh = shape(r, res)
    tau = _tau(r, res); mu = max([t for t in range(r) if tau[t] > 0], default=0); T = 1 + (sum(res)-k+1-2*mu)//r
    eo = max(e for e in U if e % 2); ee = max([e for e in U if e % 2 == 0], default=0)
    key = (T - eo, eo - ee, U == Sh)
    C[key] += 1
    if U != Sh and shown < 8:
        shown += 1; print('CE r=%d k=%d res=%s T=%d Uinf=%s shape=%s' % (r, k, res, T, sorted(U), sorted(Sh)))
print(f'seed={sys.argv[1]} multisets={n} histogram (T-e_odd, e_odd-e_even, shape-rule-correct): {dict(sorted(C.items()))}')
