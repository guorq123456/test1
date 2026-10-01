# Stage-2 feature library: statistics of the residue part only (nontrivial factors a_i>1),
# including features of the residue polynomial C(q)=prod_{a_i>1, r∤a_i} [a_i mod r]_q.
from fractions import Fraction
def _res(r,a): return [x%r for x in a if x>1 and x%r]
def _C(r,a):
    c=[1]
    for t in _res(r,a):
        n=[0]*(len(c)+t-1)
        for i,v in enumerate(c):
            for j in range(t): n[i+j]+=v
        c=n
    return c
def _fold(r,a):
    c=_C(r,a); f=[0]*r
    for i,v in enumerate(c): f[i%r]+=v
    return f
FEATS2={
 'sum4res':   lambda r,a: sum(t**4 for t in _res(r,a)),
 'Cdeg':      lambda r,a: sum(t-1 for t in _res(r,a)),
 'ntop':      lambda r,a: sum(1 for t in _res(r,a) if t==r-1),
 'ntop2':     lambda r,a: sum(1 for t in _res(r,a) if t==r-2),
 'Cfold':     lambda r,a: tuple(_fold(r,a)),
 'Cfold_shape':lambda r,a: (lambda f: tuple(x-min(f) for x in f))(_fold(r,a)),
 'Cfold_spread':lambda r,a: (lambda f: max(f)-min(f))(_fold(r,a)),
 'Cfold_ratio':lambda r,a: (lambda f: Fraction(max(f),min(f)) if min(f) else -1)(_fold(r,a)),
}
