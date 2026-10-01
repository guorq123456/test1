"""sigma=2, w=2 specialised model.

Odd k:  n=k+1 window bits, L=n+1 odd. Optimal <=> colouring c:{0,1}^n->{0,1} with exactly one
monochromatic edge on every rotation-cycle of (n+1)-bit strings. (uncharged edge: c[pre]=1,c[suf]=0)
Even k: the (2,k+1)-problem restricted to colourings that ignore the last window bit.
"""
import sys, time, itertools
import numpy as np
from pysat.solvers import Cadical153
from pysat.card import CardEnc, EncType
from pysat.formula import IDPool

def cycles(m):
    """rotation orbits of m-bit strings as lists of edge codes."""
    seen = bytearray(1 << m); out = []
    for e in range(1 << m):
        if seen[e]: continue
        cyc = []; x = e
        while not seen[x]:
            seen[x] = 1; cyc.append(x)
            x = ((x << 1) | (x >> (m - 1))) & ((1 << m) - 1)
        out.append(cyc)
    return out

def charged_count(c, n):
    """c: array over 2^n windows (values 0/1). returns #charged (n+1)-contexts."""
    E = np.arange(1 << (n + 1), dtype=np.int64)
    pre, suf = E >> 1, E & ((1 << n) - 1)
    return int(np.count_nonzero(~((c[pre] == 1) & (c[suf] == 0))))

def bound_charged(n):
    from density import g_sigma
    return round(g_sigma(2, 2, n - 1) * (1 << (n + 1)))

def build(kprime, restricted=False):
    n = kprime + 1
    m = n + 1
    pool = IDPool()
    nv = n - 1 if restricted else n
    cv = lambda v: pool.id(('c', (v >> 1) if restricted else v))
    clauses = []
    for cyc in cycles(m):
        if len(cyc) == 1:  # self loop 0^m / 1^m : always monochromatic, ok
            continue
        mono = []
        for e in cyc:
            pre, suf = e >> 1, e & ((1 << n) - 1)
            a, b = cv(pre), cv(suf)
            if a == b:
                mono.append(None); continue
            t = pool.id(('m', e))  # t <-> (a == b)
            clauses += [[-t, -a, b], [-t, a, -b], [t, a, b], [t, -a, -b]]
            mono.append(t)
        fixed = mono.count(None)
        lits = [t for t in mono if t is not None]
        if fixed > 1:
            return None, None  # impossible
        if fixed == 1:
            clauses += [[-t] for t in lits]
        else:
            clauses += CardEnc.equals(lits=lits, bound=1, vpool=pool, encoding=EncType.seqcounter).clauses
    return pool, clauses

def solve(kprime, restricted=False, enumerate_all=False, cap=10**6):
    n = kprime + 1
    pool, clauses = build(kprime, restricted)
    if pool is None:
        return []
    s = Cadical153(bootstrap_with=clauses)
    sols = []
    while s.solve():
        model = set(l for l in s.get_model() if l > 0)
        c = np.zeros(1 << n, dtype=np.int64)
        keyvars = []
        for v in range(1 << n):
            vid = pool.id(('c', (v >> 1) if restricted else v))
            c[v] = 1 if vid in model else 0
        sols.append(c)
        if not enumerate_all or len(sols) >= cap:
            break
        ids = sorted({pool.id(('c', (v >> 1) if restricted else v)) for v in range(1 << n)})
        s.add_clause([-i if i in model else i for i in ids])
    s.delete()
    return sols

if __name__ == '__main__':
    kp = int(sys.argv[1]); restricted = '--even' in sys.argv; enum = '--all' in sys.argv
    t = time.time()
    sols = solve(kp, restricted, enum)
    n = kp + 1
    print(f"k'={kp} (window bits n={n}) restricted={restricted}: {len(sols)} solution(s) in {time.time()-t:.1f}s; bound charged={bound_charged(n)} / {1<<(n+1)}")
    for c in sols[:1]:
        print(" charged =", charged_count(c, n))
