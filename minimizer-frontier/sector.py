"""Mykkeltveit-style sector rules for sigma=w=2 odd k'.  n window bits, m=n+1, omega=e^{2 pi i/m}.
Variant A (edge rule): D = {e : arg z(e) in sector [theta, theta+2pi/m)}; fallback for z=0: min rotation. Check B-D bipartite.
Variant B (window rule): c(W) = idx(z(W)+ t*omega^{-1}) mod 2 for t in {0, 1/2, 1} (guess of the missing char)."""
import sys, cmath, math, numpy as np
from w2 import cycles, charged_count, bound_charged
from reps import bipartite_colouring, rotations

def zval(bitstr, m):
    om = cmath.exp(2j * math.pi / m)
    return sum(om ** i for i, b in enumerate(bitstr) if b == '1')

def sector_D(n, theta, fallback='min'):
    m = n + 1; D = set(); amb = 0
    for cyc in cycles(m):
        if len(cyc) == 1: D.add(cyc[0]); continue
        hits = []
        for e in cyc:
            z = zval(format(e, f'0{m}b'), m)
            if abs(z) < 1e-9: continue
            a = (cmath.phase(z) - theta) % (2 * math.pi)
            if a < 2 * math.pi / m - 1e-12: hits.append(e)
        if len(hits) == 1: D.add(hits[0])
        else:
            amb += 1
            D.add(min(cyc) if fallback == 'min' else max(cyc))
    return D, amb

def window_rule(n, t, theta):
    m = n + 1; om_inv = cmath.exp(-2j * math.pi / m)
    c = np.zeros(1 << n, dtype=np.int64)
    for W in range(1 << n):
        z = zval(format(W, f'0{n}b'), m) + t * om_inv
        if abs(z) < 1e-9: c[W] = 0; continue
        idx = int(((cmath.phase(z) - theta) % (2 * math.pi)) // (2 * math.pi / m))
        c[W] = idx & 1
    return c

if __name__ == '__main__':
    ns = [2, 4, 6, 8, 10, 12]
    print("Variant A (edge sector + fallback):")
    for frac in [0, 0.1, 0.25, 0.37, 0.5, 0.63, 0.75, 0.9]:
        res = []
        for n in ns:
            m = n + 1; theta = frac * 2 * math.pi / m
            D, amb = sector_D(n, theta)
            c = bipartite_colouring(n, D)
            res.append('Y' if c is not None and charged_count(c, n) == bound_charged(n) else ('b' if c is None else '.'))
        print(f"  theta={frac:.2f}*sector : {' '.join(res)}")
    print("Variant B (window sector parity):")
    for t in [0, 0.5, 1]:
        for frac in [0, 0.25, 0.5, 0.75]:
            res = []
            for n in ns:
                m = n + 1; theta = frac * 2 * math.pi / m
                c = window_rule(n, t, theta)
                ch = charged_count(c, n); b = bound_charged(n)
                res.append('Y' if ch == b else f"+{ch-b}")
            print(f"  t={t} theta={frac:.2f}*sector : {' '.join(res)}")
