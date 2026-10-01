import sys, types
sys.modules['matplotlib'] = types.ModuleType('matplotlib'); m = types.ModuleType('matplotlib.pyplot'); m.rcParams = {}; sys.modules['matplotlib.pyplot'] = m
sys.path.insert(0, 'author_repo/new')
import transfer_matrix_solver as A
import sympy as sp, numpy as np
from sympy.abc import x
mine = {}
for fn in ['polys_k1.txt','polys_k2.txt','polys_k3.txt','polys_k4.txt']:
    for line in open(fn):
        k,n,cs = line.split(); mine[(int(k),int(n))] = list(map(int, cs.split(',')))
for (n,k) in [(30,1),(25,2),(20,3),(20,4),(9,2)]:
    T = A.build_transfer_matrix(k)
    poly = (T**n).trace()
    c = [int(v) for v in reversed(sp.Poly(poly, x).all_coeffs())]
    r = np.roots([float(v) for v in reversed(c)])
    print(n, k, 'author poly == mine:', c == mine[(k,n)], ' np.roots max|Im| =', round(max(abs(r.imag)),4), ' #|Im|>1e-10:', int(sum(abs(r.imag)>1e-10)), ' deg', len(c)-1)
