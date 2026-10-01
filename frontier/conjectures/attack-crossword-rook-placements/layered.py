# Evaluate |RP| for all layered permutations of size n (all compositions).
import sys, rp1, itertools, time
def layered(comp):
    w = []; s = 0
    for a in comp:
        w += list(range(s+a, s, -1)); s += a
    return w
def compositions(n):
    for cuts in range(1 << (n-1)):
        comp = []; last = 0
        for i in range(n-1):
            if cuts >> i & 1: comp.append(i+1-last); last = i+1
        comp.append(n-last); yield tuple(comp)
for n in range(int(sys.argv[1]), int(sys.argv[2])+1):
    t = time.time(); res = []
    for c in compositions(n):
        if c[::-1] < c: continue
        res.append((rp1.rp(layered(c)), c))
    res.sort(reverse=True)
    print(n, f"{time.time()-t:.1f}s", res[:4], flush=True)
