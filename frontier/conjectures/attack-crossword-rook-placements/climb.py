# Basin-hopping / steepest-ascent search for max |RP(Grid(w))| over S_n.
# Moves: transpositions of positions, and moving one entry to another position.
import sys, random, time, rp1
def neighbors(w):
    n = len(w)
    for i in range(n):
        for j in range(i+1, n):
            v = w[:]; v[i], v[j] = v[j], v[i]; yield v
    for i in range(n):
        for j in range(n):
            if j == i or j == i+1: continue
            v = w[:]; x = v.pop(i); v.insert(j if j < i else j-1, x); yield v
def climb(w):
    f = rp1.rp(w)
    while True:
        best = None; bf = f
        for v in neighbors(w):
            g = rp1.rp(v)
            if g > bf: bf, best = g, v
        if best is None: return f, w
        w, f = best, bf
def kick(w, k):
    w = w[:]; n = len(w)
    for _ in range(k):
        i, j = random.sample(range(n), 2); w[i], w[j] = w[j], w[i]
    return w
if __name__ == "__main__":
    n = int(sys.argv[1]); seconds = float(sys.argv[2]); seed = int(sys.argv[3])
    random.seed(seed)
    t0 = time.time(); gbest = (0, None); runs = 0; hits = {}
    while time.time() - t0 < seconds:
        w = list(range(1, n+1)); random.shuffle(w)
        f, w = climb(w)
        # a few basin-hopping kicks from this local optimum
        for _ in range(5):
            f2, w2 = climb(kick(w, random.randint(2, 4)))
            if f2 > f: f, w = f2, w2
        runs += 1
        hits[f] = hits.get(f, 0) + 1
        if f > gbest[0]:
            gbest = (f, w); print(f"n={n} run {runs} t={time.time()-t0:.0f}s new best {f} {w}", flush=True)
    print(f"n={n} done runs={runs} best={gbest[0]} {gbest[1]}; local-opt value counts (top 5):",
          sorted(hits.items(), reverse=True)[:5], flush=True)
