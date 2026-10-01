"""Optimal colourings with imposed symmetries (sigma=w=2, odd k'). Which symmetry classes are feasible?"""
import sys, time, numpy as np
from pysat.solvers import Cadical153
from w2 import build, charged_count, bound_charged

def rev(v, n): return int(format(v, f'0{n}b')[::-1], 2)
def NOT(v, n): return (~v) & ((1 << n) - 1)

def solve_sym(kp, syms, restricted=False):
    n = kp + 1
    pool, clauses = build(kp, restricted)
    cid = lambda v: pool.id(('c', (v >> 1) if restricted else v))
    for v in range(1 << n):
        a = cid(v)
        if 'rev' in syms:      # c(rev W) = c(W)
            b = cid(rev(v, n)); clauses += [[-a, b], [a, -b]]
        if 'revflip' in syms:  # c(rev W) = 1 - c(W)
            b = cid(rev(v, n)); clauses += [[a, b], [-a, -b]]
        if 'not' in syms:      # c(NOT W) = c(W)
            b = cid(NOT(v, n)); clauses += [[-a, b], [a, -b]]
        if 'notflip' in syms:  # c(NOT W) = 1 - c(W)
            b = cid(NOT(v, n)); clauses += [[a, b], [-a, -b]]
    s = Cadical153(bootstrap_with=clauses)
    ok = s.solve()
    c = None
    if ok:
        model = set(l for l in s.get_model() if l > 0)
        c = np.array([1 if cid(v) in model else 0 for v in range(1 << n)])
    s.delete()
    return c

if __name__ == '__main__':
    for syms in [('rev',), ('revflip',), ('not',), ('notflip',), ('rev', 'notflip'), ('revflip', 'notflip'), ('rev', 'not'), ('revflip','not')]:
        for restricted in (False, True):
            res = []
            for kp in [1, 3, 5, 7, 9, 11]:
                c = solve_sym(kp, syms, restricted)
                res.append('Y' if c is not None and charged_count(c, kp + 1) == bound_charged(kp + 1) else '.')
            print(f"syms={'+'.join(syms):14s} restricted={restricted!s:5s} k'=1,3,5,7,9,11: {' '.join(res)}")
