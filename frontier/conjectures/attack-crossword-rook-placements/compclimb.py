# Local search over compositions (layered permutations) for n, vs conjectured family.
import sys, rp1, time
from layered import layered
def nbrs(c):
    c = list(c); out = set()
    for i in range(len(c)-1):
        out.add(tuple(c[:i] + [c[i]+c[i+1]] + c[i+2:]))           # merge
        if c[i] > 1: out.add(tuple(c[:i] + [c[i]-1, c[i+1]+1] + c[i+2:]))
        if c[i+1] > 1: out.add(tuple(c[:i] + [c[i]+1, c[i+1]-1] + c[i+2:]))
    for i in range(len(c)):
        for a in range(1, c[i]):
            out.add(tuple(c[:i] + [a, c[i]-a] + c[i+1:]))           # split
    return out
cache = {}
def f(c):
    if c not in cache: cache[c] = rp1.rp(layered(c))
    return cache[c]
for n in map(int, sys.argv[1:]):
    t = time.time()
    fam = max((f(tuple([m] + [1]*(n-2*m) + [m])), m) for m in range(2, n//2+1))
    starts = [tuple([m] + [1]*(n-2*m) + [m]) for m in (4, 5, 6) if 2*m <= n]
    best = (0, None)
    for c in starts:
        cur = c
        while True:
            nb = max(nbrs(cur), key=f)
            if f(nb) <= f(cur): break
            cur = nb
        if f(cur) > best[0]: best = (f(cur), cur)
    print(f"n={n}: conjectured max (m,1..1,m) = {fam[0]} (m={fam[1]}); best layered found {best[0]} shape {best[1]}; ratio {best[0]/fam[0]:.4f} ({time.time()-t:.0f}s, {len(cache)} evals)", flush=True)
