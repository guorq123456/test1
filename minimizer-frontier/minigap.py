"""Optimal minimizer (all orders x tie rule) vs optimal forward scheme, sigma=2, w=2, small k."""
import itertools, numpy as np
from density import density_of, g_prime, minimizer_scheme
from w2 import bound_charged
sigma, w = 2, 2
for k in [1, 2, 3]:
    best = None
    n = w + k - 1
    for perm in itertools.permutations(range(sigma ** k)):
        order = np.array(perm)
        for tie in ('left', 'right'):
            f = np.zeros(sigma ** n, dtype=np.int64)
            for W in range(sigma ** n):
                from density import kmers_of_window
                ks = kmers_of_window(W, sigma, w, k)
                ranks = [order[x] for x in ks]
                mn = min(ranks)
                idx = [i for i, r in enumerate(ranks) if r == mn]
                f[W] = idx[0] if tie == 'left' else idx[-1]
            d, c, ok = density_of(f, sigma, w, k)
            if best is None or c < best[0]: best = (c, perm, tie)
    L = w + k
    fwd = bound_charged(n) if k % 2 == 1 else round(g_prime(sigma, w, k) * sigma ** L)
    print(f"k={k}: best minimizer charged={best[0]}/{sigma**L} (order {best[1]}, tie {best[2]})  optimal forward={fwd}  -> minimizer {'optimal' if best[0]==fwd else 'NOT optimal'}")
