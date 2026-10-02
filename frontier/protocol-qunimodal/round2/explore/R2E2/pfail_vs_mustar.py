# For each a: K (=sigma+1 mod r, 0<=K<=D+1-2r) where P(K) fails, relative to 2*mu*.  Also check y* formula.
import sys, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import *
from limit import tau
from decomp import *
from structure_helpers import mu_of
from s3star import estar
from collections import Counter
mode = sys.argv[1]
C = Counter(); ex = {}
def run(r, a):
    ds = DS(r, a); tt = tau(r, a)
    E, ms, bad = estar(r, a, ds, tt)
    D = ds.D
    # y* check
    y = 0
    while ds(y) >= 0: y += 1
    assert D + 1 - r - y == ms, (r, a, y, ms)
    K = (D + 1) % r
    while K <= D + 1 - 2 * r:
        if not P_ok(r, ds, tt, K):
            key = K - 2 * ms
            C[key] += 1
            if key not in ex: ex[key] = (r, a, K, ms)
        K += r
if mode == 'eq':
    for r in range(4, 11):
        for t in range(1, r):
            for k in range(1, 61): run(r, [t] * k)
else:
    r, kmax, amax = map(int, sys.argv[2:5])
    vals = [x for x in range(1, amax + 1) if x % r]
    for k in range(1, kmax + 1):
        for a in itertools.combinations_with_replacement(vals, k): run(r, list(a))
print(sys.argv[1:], "P-failure K - 2mu* :", sorted(C.items()))
for k_, v in sorted(ex.items()): print("  ", k_, v)
