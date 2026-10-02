# How often is d (coeffs of A/[r]_q) non-monotone on [0, L] for L = D/2 and L = D+1-2r?
import sys, itertools, random
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import DS
from collections import Counter
C = Counter(); ex = []
for r in range(3, 9):
    vals = [x for x in range(1, 2 * r + 3) if x % r]
    for k in range(1, 6):
        for a in itertools.combinations_with_replacement(vals, k):
            ds = DS(r, list(a)); D = ds.D
            firstdesc = next((y for y in range(1, D + r) if ds(y) < ds(y - 1)), None)
            C[('first descent <= D/2', firstdesc is not None and firstdesc <= D / 2)] += 1
            if firstdesc is not None and firstdesc <= D / 2 and len(ex) < 6: ex.append((r, a, D, firstdesc, [ds(i) for i in range(0, D // 2 + 2)]))
print(sorted(C.items(), key=str))
for e in ex: print(e)
