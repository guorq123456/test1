# Meet-in-the-middle exhaustive computation of |RP(Grid(w))| over S_n (stats version).
# usage: python3 mitm2.py n worker nworkers outprefix
import os, sys, itertools, ctypes, time, pickle
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np
from mitm import lib, fact
HB = 1 << 22      # exact histogram for values < HB

def run(n, worker, nworkers, outprefix):
    h = n // 2
    full = (1 << n) - 1
    pc = np.array([bin(m).count("1") for m in range(1 << n)])
    subsets = []
    for S in itertools.combinations(range(n), h):
        sm = sum(1 << s for s in S)
        rm = sum(1 << (n-1-s) for s in S)          # left-right mirror (w -> n+1-w)
        if rm < sm: continue
        subsets.append((sm, 1 if rm == sm else 2))
    subsets = subsets[worker::nworkers]
    hist = np.zeros(HB, dtype=np.int64)
    seen = np.zeros(1 << 20, dtype=bool)  # attained values (grown as needed)
    nbig = 0
    best = 0; bestw = []
    top = []           # (value, perm) candidates for top list
    smallwit = {}
    total = 0
    nT, nB = fact(h), fact(n-h)
    t0 = time.time()
    def mirror(w): return tuple(n+1-x for x in w)
    for idx, (sm, weight) in enumerate(subsets):
        e_t = (sm & 1) + ((sm >> (n-1)) & 1)
        kt = h + 1 - e_t
        masks = np.nonzero(pc == kt)[0]; K = len(masks)
        ci_t = -np.ones(1 << n, dtype=np.int32); ci_t[masks] = np.arange(K, dtype=np.int32)
        ci_b = -np.ones(1 << n, dtype=np.int32); ci_b[full ^ masks] = np.arange(K, dtype=np.int32)
        T = np.zeros((nT, K)); seqT = np.zeros((nT, h), dtype=np.int32)
        U = np.zeros((nB, K)); seqB = np.zeros((nB, n-h), dtype=np.int32)
        r1 = lib.half_vectors(n, h, sm, ci_t, K, T, seqT)
        r2 = lib.half_vectors(n, n-h, full ^ sm, ci_b, K, U, seqB)
        assert r1 == nT and r2 == nB, (r1, r2)
        nz = T.any(0) & U.any(0)
        C = T[:, nz] @ U[:, nz].T
        V = np.rint(C).astype(np.int64).ravel()
        assert np.abs(C.ravel() - V).max() < 1e-6
        assert V.min() >= 1
        total += weight * V.size
        def perm_of(flat):
            p, q = divmod(int(flat), nB)
            return tuple(int(x)+1 for x in list(seqT[p]) + list(seqB[q][::-1]))
        sm_mask = V < HB
        hist += weight * np.bincount(V[sm_mask], minlength=HB)
        mx = int(V.max())
        if mx >= len(seen):
            ns = np.zeros(max(mx + 1, 2 * len(seen)), dtype=bool); ns[:len(seen)] = seen; seen = ns
        seen[V] = True
        if mx >= best:
            if mx > best: best = mx; bestw = []
            for f in np.flatnonzero(V == mx):
                w = perm_of(f); bestw.append(w)
                if weight == 2: bestw.append(mirror(w))
        # top-8 entries of this block
        k = min(8, V.size)
        for f in np.argpartition(V, -k)[-k:]:
            top.append((int(V[f]), perm_of(f)))
        top = sorted(set(top), reverse=True)[:200]
        fi = np.flatnonzero(V < 3000)
        uu, first = np.unique(V[fi], return_index=True)
        for val, j in zip(uu.tolist(), first.tolist()):
            if val not in smallwit: smallwit[val] = perm_of(fi[j])
        if idx % 25 == 0:
            print(f"[w{worker}] {idx+1}/{len(subsets)} K={K} nz={nz.sum()} t={time.time()-t0:.1f}s", flush=True)
    with open(f"{outprefix}.pkl", "wb") as f:
        pickle.dump(dict(n=n, hist=hist, seen=np.packbits(seen), seenlen=len(seen), best=best, bestw=bestw,
                         top=top, smallwit=smallwit, total=total, time=time.time()-t0), f)
    print(f"[w{worker}] done total={total} best={best} time={time.time()-t0:.1f}s", flush=True)

if __name__ == "__main__":
    n, worker, nworkers = map(int, sys.argv[1:4])
    run(n, worker, nworkers, sys.argv[4])
