import sys, numpy as np
from w2 import cycles
from pnu import alt_vec
from walkrules import mk, walk
nu = int(sys.argv[1]); rule = sys.argv[2] if len(sys.argv) > 2 else 'argmax<argmin'
m = nu + 2
h = mk(rule, nu)
for cyc in cycles(m):
    if len(cyc) == 1: continue
    e0 = cyc[0]; s = [(e0 >> (m - 1 - i)) & 1 for i in range(m)]
    vals = []; wins = []
    for j in range(m):
        W = 0
        for t in range(nu): W = (W << 1) | s[(j + t) % m]
        vals.append(int(h[W])); wins.append(W)
    d = [j for j in range(m) if vals[j] == vals[(j + 1) % m]]
    if len(d) != 1:
        U = [s[p % m] ^ (p & 1) for p in range(2 * m)]
        print(f"s={''.join(map(str,s))}  U={''.join(map(str,U))}  walk={walk(U)}")
        print(f"   h(window_j)={vals}  defects at j={d}")
        for j in range(m):
            v = alt_vec(wins[j], nu); y = walk(v)
            print(f"     j={j} f={''.join(map(str,v))} y={y} argmax={y.index(max(y))} argmin={y.index(min(y))} h={vals[j]}")
