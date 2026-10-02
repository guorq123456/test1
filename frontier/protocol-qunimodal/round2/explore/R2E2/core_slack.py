# Core inequality for S3*: for K = sigma+1 mod r, 2mu*+2r <= K <= D+1-2r, x in [0,K/2): Q_{K-x} - d_x >= 0.
# Report the minimal slack and its location (gap g = K-2x) and offset K-2mu*.
import sys, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import *
from limit import tau
from s3star import estar
from collections import Counter
C = Counter(); worst = []
def run(r, a):
    ds = DS(r, a); tt = tau(r, a)
    E, ms, bad = estar(r, a, ds, tt)
    D = ds.D
    Q = lambda u: ds(u) - tt[u % r]
    K = (D + 1) % r
    while K <= D + 1 - 2 * r:
        if K >= 2 * ms + 2 * r:
            best = None
            for x in range(0, (K + 1) // 2):
                if 2 * x >= K: break
                s = Q(K - x) - ds(x)
                if best is None or s < best[0]: best = (s, x)
            if best is not None:
                s, x = best
                C[('slack<0' if s < 0 else ('slack0' if s == 0 else ('slack<=2' if s <= 2 else 'big')), 'gap', min(K - 2 * x, 9), 'x0' if x == 0 else 'x>0')] += 1
                if s <= 0 and len(worst) < 10: worst.append((r, a, K, ms, x, s))
        K += r
mode = sys.argv[1]
if mode == 'eq':
    for r in range(4, 11):
        for t in range(1, r):
            for k in range(1, 61): run(r, [t] * k)
else:
    r, kmax, amax = map(int, sys.argv[2:5])
    vals = [x for x in range(1, amax + 1) if x % r]
    for k in range(1, kmax + 1):
        for a in itertools.combinations_with_replacement(vals, k): run(r, list(a))
for k_, v in sorted(C.items(), key=str): print(k_, v)
for w in worst: print("  ", w)
