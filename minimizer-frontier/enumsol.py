import sys, numpy as np
from w2 import solve, cycles, charged_count
kp = int(sys.argv[1]); restricted = '--even' in sys.argv
n = kp + 1; m = n + 1
sols = solve(kp, restricted, enumerate_all=True, cap=200000)
print(f"k'={kp} restricted={restricted}: {len(sols)} optimal colourings")
fmt = lambda e, b: format(e, f'0{b}b')
for c in sols[:6]:
    ones = [fmt(v, n) for v in range(1 << n) if c[v] == 1]
    defects = []
    for cyc in cycles(m):
        if len(cyc) == 1: continue
        for e in cyc:
            if c[e >> 1] == c[e & ((1 << n) - 1)]:
                defects.append(fmt(e, m))
    print(" colour-1 windows:", ' '.join(ones))
    print(" defect edges   :", ' '.join(sorted(defects)))
