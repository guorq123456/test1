import time
from dp import *
for k in range(1, 8):
    t = time.time()
    rng = range(k+1)
    states = {}
    for z0 in rng:
        S = frozenset((a, b) for a in rng for b in rng if min(a, b) == z0)
        states[S] = 1
    seen = set(states)
    frontier = list(states)
    while frontier:
        nf = []
        for S in frontier:
            trans = {}
            for (a, b) in S:
                for d in rng:
                    trans.setdefault(min(a, b, d), set()).add((b, d))
            for z, T in trans.items():
                T = frozenset(T)
                if T not in seen:
                    seen.add(T); nf.append(T)
        frontier = nf
    print(k, 'reachable DFA states', len(seen), round(time.time()-t, 2))
