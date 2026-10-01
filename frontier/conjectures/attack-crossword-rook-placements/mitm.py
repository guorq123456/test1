# Meet-in-the-middle exhaustive computation of |RP(Grid(w))| over S_n.
# usage: python3 mitm.py n worker nworkers outprefix [dump]
import os, sys, itertools, ctypes, time
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np
from math import comb
HERE = os.path.dirname(os.path.abspath(__file__))
lib = ctypes.CDLL(os.path.join(HERE, "libhalf.so"))
lib.half_vectors.restype = ctypes.c_int
lib.half_vectors.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int,
    np.ctypeslib.ndpointer(np.int32), ctypes.c_int,
    np.ctypeslib.ndpointer(np.float64), np.ctypeslib.ndpointer(np.int32)]

def fact(k):
    r = 1
    for i in range(2, k+1): r *= i
    return r

def run(n, worker, nworkers, outprefix, dump=False, symmetric=True):
    h = n // 2
    full = (1 << n) - 1
    pc = np.array([bin(m).count("1") for m in range(1 << n)])
    subsets = []
    for S in itertools.combinations(range(n), h):
        sm = sum(1 << s for s in S)
        rm = sum(1 << (n-1-s) for s in S)          # left-right mirror (w -> n+1-w)
        if symmetric:
            if rm < sm: continue                   # partner processed instead
            weight = 1 if rm == sm else 2
        else:
            weight = 1
        subsets.append((sm, weight))
    subsets = subsets[worker::nworkers]
    hist = {}
    best = 0; bestw = []
    smallwit = {}          # value -> witness for values < 2000
    cnt = {1: 0, 2: 0}
    total = 0
    dumpf = open(f"{outprefix}.dump", "w") if dump else None
    nT, nB = fact(h), fact(n-h)
    t0 = time.time()
    for idx, (sm, weight) in enumerate(subsets):
        e_t = ((sm >> 0) & 1) + ((sm >> (n-1)) & 1)
        kt = h + 1 - e_t
        masks = np.nonzero(pc == kt)[0]
        K = len(masks)
        ci_t = -np.ones(1 << n, dtype=np.int32); ci_t[masks] = np.arange(K, dtype=np.int32)
        ci_b = -np.ones(1 << n, dtype=np.int32); ci_b[full ^ masks] = np.arange(K, dtype=np.int32)
        T = np.zeros((nT, K)); seqT = np.zeros((nT, h), dtype=np.int32)
        U = np.zeros((nB, K)); seqB = np.zeros((nB, n-h), dtype=np.int32)
        r1 = lib.half_vectors(n, h, sm, ci_t, K, T, seqT)
        r2 = lib.half_vectors(n, n-h, full ^ sm, ci_b, K, U, seqB)
        assert r1 == nT and r2 == nB, (r1, r2)
        nz = T.any(0) & U.any(0)
        C = T[:, nz] @ U[:, nz].T
        V = np.rint(C).astype(np.int64)
        assert np.abs(C - V).max() < 1e-6
        assert V.min() >= 1      # paper: every permutation grid admits >= 1 placement
        total += weight * V.size
        u, c = np.unique(V, return_counts=True)
        for a, b in zip(u.tolist(), c.tolist()):
            hist[a] = hist.get(a, 0) + weight * b
        cnt[1] += weight * int((V == 1).sum()); cnt[2] += weight * int((V == 2).sum())
        mx = int(V.max())
        def perm_of(p, q):
            return tuple(int(x)+1 for x in list(seqT[p]) + list(seqB[q][::-1]))
        def mirror(w):
            return tuple(n+1-x for x in w)
        if mx >= best:
            if mx > best: best = mx; bestw = []
            for p, q in zip(*np.nonzero(V == mx)):
                w = perm_of(p, q); bestw.append(w)
                if weight == 2: bestw.append(mirror(w))
        small = u[u < 2000]
        for val in small.tolist():
            if val not in smallwit:
                p, q = np.argwhere(V == val)[0]
                smallwit[val] = perm_of(p, q)
        if dumpf:
            for p in range(nT):
                for q in range(nB):
                    w = perm_of(p, q)
                    dumpf.write("".join("%x" % x for x in w) + " %d\n" % V[p, q])
                    if weight == 2:
                        dumpf.write("".join("%x" % x for x in mirror(w)) + " %d\n" % V[p, q])
        if idx % 20 == 0:
            print(f"[w{worker}] {idx+1}/{len(subsets)} K={K} nz={nz.sum()} t={time.time()-t0:.1f}s", flush=True)
    if dumpf: dumpf.close()
    import pickle
    with open(f"{outprefix}.pkl", "wb") as f:
        pickle.dump(dict(n=n, hist=hist, best=best, bestw=bestw, smallwit=smallwit,
                         cnt=cnt, total=total, time=time.time()-t0), f)
    print(f"[w{worker}] done total={total} best={best} time={time.time()-t0:.1f}s", flush=True)

if __name__ == "__main__":
    n, worker, nworkers = map(int, sys.argv[1:4])
    run(n, worker, nworkers, sys.argv[4], dump=(len(sys.argv) > 5 and sys.argv[5] == "dump"))
