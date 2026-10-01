import numpy as np
from pysat.solvers import Cadical153
from w2 import build
def rc(u, nu): return int(format((~u) & ((1 << nu) - 1), f'0{nu}b')[::-1], 2)
def rev(u, nu): return int(format(u, f'0{nu}b')[::-1], 2)
def NOT(u, nu): return (~u) & ((1 << nu) - 1)
def feas(nu, f, mode):
    pool, clauses = build(nu, True)   # P(nu): h(u) = c(u<<1)
    hid = lambda u: pool.id(('c', u))
    for u in range(1 << nu):
        a, b = hid(u), hid(f(u, nu))
        clauses += ([[-a, b], [a, -b]] if mode == 'inv' else [[a, b], [-a, -b]])
    s = Cadical153(bootstrap_with=clauses); ok = s.solve(); s.delete(); return ok
for name, f in [('rc', rc), ('rev', rev), ('NOT', NOT)]:
    for mode in ('inv', 'anti'):
        print(f"P(nu) with h o {name} = {'h' if mode=='inv' else '1-h'}: ", [(nu, feas(nu, f, mode)) for nu in [1, 3, 5, 7, 9, 11]])
