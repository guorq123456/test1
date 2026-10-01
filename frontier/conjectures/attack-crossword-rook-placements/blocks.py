# For n, search w = dec(m1) (+) sigma (+) dec(m2) over all sigma in S_{n-m1-m2}
import sys, itertools, rp1, time
n = int(sys.argv[1]); pairs = [tuple(map(int, p.split(","))) for p in sys.argv[2:]]
for m1, m2 in pairs:
    t = time.time(); k = n - m1 - m2; best = (0, None); cnt = 0
    for s in itertools.permutations(range(1, k+1)):
        w = list(range(m1, 0, -1)) + [m1 + x for x in s] + list(range(n, n-m2, -1))
        v = rp1.rp(w); cnt += 1
        if v > best[0]: best = (v, w)
    print(f"n={n} m1={m1} m2={m2}: {cnt} perms, best {best[0]} {best[1]} ({time.time()-t:.0f}s)", flush=True)
