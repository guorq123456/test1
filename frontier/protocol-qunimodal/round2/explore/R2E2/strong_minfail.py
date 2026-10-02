# For the strong certificate: smallest k' at which an rho' with parts in [2,r-1] fails (all rho' with k' <= 5 for r<=12,
# k' <= 3 for larger r), and in the equal families (t^k'), k' <= 60.  Prints one line per r.
import sys, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from strong_check import strong
for r in range(4, 31):
    kk = 5 if r <= 12 else 3
    mf_all = None
    for k in range(1, kk + 1):
        if any(not all(strong(r, list(rho))) for rho in itertools.combinations_with_replacement(range(2, r), k)):
            mf_all = k; break
    mf_eq = {}
    for t in range(2, r):
        for k in range(1, 61):
            if not all(strong(r, [t] * k)): mf_eq[t] = k; break
    print(f"r={r}: first failing k' among all rho' (k'<={kk}): {mf_all}; equal families first failing k' by t: {mf_eq}", flush=True)
