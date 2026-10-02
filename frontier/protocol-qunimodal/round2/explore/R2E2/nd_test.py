# Near-diagonal reduction: Phi(K) <= Phi(K+r) and ND(K).  Test:
#  ND-even: K = sigma+1 mod 2r, K >= 2mu*, pairs x<u=K-x<=x+r : Q_u >= d_x ;  also whether d_u >= d_x alone holds.
#  ND-odd : K = sigma+1+r mod 2r, K >= 2mu*+2r : Q_u >= d_x.
import sys, itertools, random
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
    K = (sigma + 1) % (2 * r)  # residue class rep; iterate all K = sigma+1 mod r up to D+1-2r
    K = (D + 1) % r
    while K <= D + 1 - 2 * r:
        even = ((K - sigma - 1) % (2 * r)) == 0
        rel = (even and K >= 2 * ms) or ((not even) and K >= 2 * ms + 2 * r)
        if rel:
            for x in range((K - r + 1) // 2 - 1, (K + 1) // 2 + 1):
                u = K - x
                if not (0 < u - x <= r): continue
                dx = ds(x); Qu = ds(u) - tt[u % r]
                ok = Qu >= dx
                key = ('even' if even else 'odd', 'ND ok' if ok else 'ND FAIL', 'd_u>=d_x' if ds(u) >= dx else 'd_u<d_x')
                C[key] += 1
                if key not in ex: ex[key] = (r, a, K, ms, x, u, dx, ds(u), tt[u % r])
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
for k_, v in sorted(C.items()): print("  ", k_, v, ex[k_])
