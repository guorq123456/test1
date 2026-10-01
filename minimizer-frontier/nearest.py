import sys, numpy as np
from w2 import solve
from walkrules import mk
from pnu import alt_vec
nu = int(sys.argv[1]); rule = sys.argv[2] if len(sys.argv) > 2 else 'argmax<argmin'
h = mk(rule, nu)
sols = solve(nu, True, enumerate_all=True, cap=100000)
best = None
for c in sols:
    hh = np.array([c[W << 1] for W in range(1 << nu)])
    d = int(np.sum(hh != h))
    if best is None or d < best[0]: best = (d, hh)
d, hh = best
diff = [(''.join(map(str, alt_vec(W, nu))), int(h[W]), int(hh[W])) for W in range(1 << nu) if h[W] != hh[W]]
print(f"nu={nu} rule={rule}: nearest optimal solution at Hamming distance {d} of {1<<nu}; differing flipped windows (f, rule, optimal): {diff}")
