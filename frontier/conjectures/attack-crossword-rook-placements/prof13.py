import os; os.environ["OPENBLAS_NUM_THREADS"]="1"
import numpy as np, time, itertools
import mitm
n=13; h=6; full=(1<<n)-1
pc = np.array([bin(m).count("1") for m in range(1 << n)])
sm = 0b0000001111110 # some S
e_t = 0; kt = h+1-e_t
masks = np.nonzero(pc == kt)[0]; K=len(masks)
ci_t = -np.ones(1 << n, dtype=np.int32); ci_t[masks] = np.arange(K, dtype=np.int32)
ci_b = -np.ones(1 << n, dtype=np.int32); ci_b[full ^ masks] = np.arange(K, dtype=np.int32)
t=time.time()
T = np.zeros((720, K)); seqT = np.zeros((720, h), dtype=np.int32)
U = np.zeros((5040, K)); seqB = np.zeros((5040, n-h), dtype=np.int32)
mitm.lib.half_vectors(n, h, sm, ci_t, K, T, seqT)
mitm.lib.half_vectors(n, n-h, full ^ sm, ci_b, K, U, seqB)
print("dp", time.time()-t); t=time.time()
nz = T.any(0) & U.any(0); print(nz.sum())
C = T[:, nz] @ U[:, nz].T
print("mm", time.time()-t); t=time.time()
V = np.rint(C).astype(np.int64)
print("rint", time.time()-t); t=time.time()
u,c=np.unique(V, return_counts=True)
print("unique", time.time()-t, len(u)); t=time.time()
print((u<2000).sum())
