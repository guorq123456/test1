import numpy as np
def T(k, z):
    S = 1 << (k+1); M = np.zeros((S,S), complex)
    for s in range(S):
        ui = s & 1; oldest = (s>>1)&1; vs = s>>1
        for up in (0,1):
            for vp in (0,1):
                if (up and ui) or (up and vp) or (vp and oldest): continue
                t = up | (((vs>>1) | (vp<<(k-1)))<<1)
                M[t, s] += z**(up+vp)
    return M
# check that Tr(T^n) reproduces the polynomial at a random point (sanity of matrix)
polys = {}
for line in open('polys_k2.txt'):
    k,n,cs = line.split(); polys[int(n)] = list(map(int, cs.split(',')))
z0 = -0.3+0.2j
print('trace check n=25:', np.trace(np.linalg.matrix_power(T(2,z0),25)), np.polyval(polys[25][::-1], z0))
for k in (2,4):
    for re in (-0.9,-0.8,-0.7):
        prev=None; hits=[]
        for im in np.linspace(1e-4, 0.3, 3000):
            ev = sorted(np.abs(np.linalg.eigvals(T(k, re+1j*im))), reverse=True)
            d = ev[0]-ev[1]
            if prev is not None and (d < 1e-6) != (prev < 1e-6): hits.append(round(im,4))
            prev = d
        ev0 = sorted(np.abs(np.linalg.eigvals(T(k, re+0.0001j))), reverse=True)[:2]
        print(k, re, 'equimodular-transition Im:', hits[:4], 'top2 at Im~0:', np.round(ev0,5))
print('--- min of |l1|-|l2| along vertical lines (excluding Im<0.005) ---')
for k in (2,4):
    best = []
    for re in np.linspace(-1.3, -0.5, 81):
        ims = np.linspace(0.005, 0.3, 600)
        ds = []
        for im in ims:
            ev = sorted(np.abs(np.linalg.eigvals(T(k, re+1j*im))), reverse=True)
            ds.append(ev[0]-ev[1])
        ds = np.array(ds)
        # interior local minima
        for i in range(1, len(ds)-1):
            if ds[i] < ds[i-1] and ds[i] <= ds[i+1] and ds[i] < 2e-3:
                best.append((round(re,3), round(ims[i],4), float(ds[i])))
    print('k', k, 'near-equimodular interior points (Re, Im, gap):', best[:12], '... total', len(best))
