# refine one non-real equimodular point for given k by bisection on vertical line, and report top-4 |eigs|
import numpy as np, sys, mpmath as mp
from bkw import Tmat, gap
k = int(sys.argv[1])
res = []
for re in np.linspace(-3.0, 0.0, 61):
    ims = np.linspace(0.01, 2.0, 200)
    g = [gap(k, re+1j*im)[0] for im in ims]
    for i in range(1, len(ims)-1):
        if g[i] < g[i-1] and g[i] <= g[i+1] and g[i] < 3e-2:
            res.append((re, ims[i], g[i]))
print('k=%d coarse equimodular non-real points (re, im, gap):' % k)
for r in res: print('  %.3f %.3f %.1e' % r)
