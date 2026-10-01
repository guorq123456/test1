# Beraha-Kahane-Weiss heuristic: locate non-real points where the two dominant eigenvalues of T_k(x) have equal modulus.
import numpy as np, sys
def Tmat(k, x):
    S = 1 << (k+1)
    valid = [a for a in range(S) if not ((a & 1) and (a >> 1) & 1)]
    idx = {a: i for i, a in enumerate(valid)}
    T = np.zeros((len(valid), len(valid)), dtype=complex)
    for a in valid:
        uprev = a & 1; vold = (a >> k) & 1
        hist = 0
        for i in range(1, k): hist |= ((a >> i) & 1) << (i+1)
        for uj in (0, 1):
            for vj in (0, 1):
                if (uj and uprev) or (uj and vj) or (vj and vold): continue
                b = hist | uj | (vj << 1)
                T[idx[a], idx[b]] += x**(uj+vj)
    return T
def gap(k, x):
    ev = np.linalg.eigvals(Tmat(k, x)); m = np.sort(np.abs(ev))[::-1]
    return np.log(m[0]) - np.log(m[1]), m[:4]
if __name__ == '__main__':
    k = int(sys.argv[1])
    # sanity: trace check
    from crt import parse_line
    for line in open('tm_k%d.txt' % k):
        kk, m, c = parse_line(line)
        if m == 3*k+5:
            x0 = 0.3+0.2j
            val = sum(cc * x0**j for j, cc in enumerate(c))
            tr = np.trace(np.linalg.matrix_power(Tmat(k, x0), m))
            print('trace check n=%d' % m, val, tr)
            break
    # scan along vertical lines for gap minima (equimodular curve crossings)
    pts = []
    for re in np.linspace(-3, 0.2, 321):
        ims = np.linspace(0.005, 1.5, 300)
        g = np.array([gap(k, re+1j*im)[0] for im in ims])
        for i in range(1, len(ims)-1):
            if g[i] < g[i-1] and g[i] <= g[i+1] and g[i] < 2e-2:
                pts.append((re, ims[i], g[i]))
    print('approx equimodular non-real points (re, im, gap):')
    for p in pts[::max(1, len(pts)//40)]: print('  %.3f %.4f %.2e' % p)
