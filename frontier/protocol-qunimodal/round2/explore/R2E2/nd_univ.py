# Does ND(K) hold for ALL K (both families)?  Record failures by family and K - 2mu*.
import sys, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import DS
from limit import tau
from s3star import estar
from collections import Counter
C = Counter(); ex = {}
def run(r, a):
    ds = DS(r, a); tt = tau(r, a)
    E, ms, bad = estar(r, a, ds, tt)
    sigma = sum((x % r) - 1 for x in a); D = ds.D
    K = (D + 1) % r - 4 * r
    while K <= D + 1 - 2 * r:
        even = ((K - sigma - 1) % (2 * r)) == 0
        fail = False
        for x in range((K - r) // 2 - 1, (K + 1) // 2 + 1):
            u = K - x
            if not (0 < u - x <= r): continue
            if ds(u) - tt[u % r] < ds(x): fail = True; break
        if fail:
            key = ('even' if even else 'odd', 'K-2mu*', K - 2 * ms if K - 2*ms < 0 else ('[0,r)' if K - 2*ms < r else ('[r,2r)' if K - 2*ms < 2*r else '>=2r')))
            C[key] += 1
            if key not in ex: ex[key] = (r, a, K, ms)
        else:
            C[('even' if even else 'odd', 'ok')] += 1
        K += r
mode = sys.argv[1]
if mode == 'eq':
    for r in range(3, 11):
        for t in range(1, r):
            for k in range(1, 61): run(r, [t] * k)
else:
    r, kmax, amax = map(int, sys.argv[2:5])
    vals = [x for x in range(1, amax + 1) if x % r]
    for k in range(1, kmax + 1):
        for a in itertools.combinations_with_replacement(vals, k): run(r, list(a))
print(sys.argv[1:])
for k_, v in sorted(C.items(), key=str): print("  ", k_, v, ex.get(k_, ''))
