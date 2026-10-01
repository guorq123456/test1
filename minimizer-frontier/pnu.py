"""Problem P(nu): h:{0,1}^nu -> {0,1}, nu odd, m=nu+2. Every cyclic m-word has exactly one monochromatic step
among its nu-windows (per period).  excess(h) = total defects - #cycles(len>1)."""
import numpy as np
from w2 import cycles

def excess(h, nu):
    m = nu + 2; mask = (1 << nu) - 1
    tot = 0; ncyc = 0
    for cyc in cycles(m):
        if len(cyc) == 1: continue
        ncyc += 1
        e0 = cyc[0]; s = [(e0 >> (m - 1 - i)) & 1 for i in range(m)]
        prev = None; first = None; d = 0
        for j in range(m):
            W = 0
            for t in range(nu): W = (W << 1) | s[(j + t) % m]
            v = int(h[W])
            if prev is not None and v == prev: d += 1
            if first is None: first = v
            prev = v
        if prev == first: d += 1
        tot += d * len(cyc) // m  # cycle of period p visited m/p times
    return tot - ncyc

def alt_vec(W, nu):
    return [((W >> (nu - 1 - i)) & 1) ^ (i & 1) for i in range(nu)]

def threshold_h(weights, theta, nu):
    h = np.zeros(1 << nu, dtype=np.int64)
    for W in range(1 << nu):
        v = alt_vec(W, nu)
        h[W] = 1 if sum(a * b for a, b in zip(weights, v)) >= theta else 0
    return h
