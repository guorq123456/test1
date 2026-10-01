"""Enumerate complement-invariant optimal colourings: c(W)=h(Delta W), Delta W = transitions (length nu=n-1 odd)."""
import sys, numpy as np
from pysat.solvers import Cadical153
from w2 import build, charged_count, bound_charged
def NOT(v, n): return (~v) & ((1 << n) - 1)
def delta(v, n):
    b = format(v, f'0{n}b'); return int(''.join(str(int(b[i]) ^ int(b[i+1])) for i in range(n - 1)), 2)
kp = int(sys.argv[1]); n = kp + 1; nu = n - 1; cap = int(sys.argv[2]) if len(sys.argv) > 2 else 50
pool, clauses = build(kp, False)
cid = lambda v: pool.id(('c', v))
for v in range(1 << n):
    a, b = cid(v), cid(NOT(v, n)); clauses += [[-a, b], [a, -b]]
s = Cadical153(bootstrap_with=clauses)
sols = []
hs = set()
while s.solve() and len(sols) < cap:
    model = set(l for l in s.get_model() if l > 0)
    c = np.array([1 if cid(v) in model else 0 for v in range(1 << n)])
    assert charged_count(c, n) == bound_charged(n)
    h = tuple(int(c[int('0' + ''.join(str(int(''.join(format(d, f'0{nu}b'))[i]) ^ (int(('0' + ''.join(format(d, f'0{nu}b')))[i])) ) for i in range(nu)), 2)]) for d in range(1 << nu))
    # simpler: compute h directly by integrating delta word d from start bit 0
    hh = []
    for d in range(1 << nu):
        bits = [0]
        for t in format(d, f'0{nu}b'): bits.append(bits[-1] ^ int(t))
        hh.append(int(c[int(''.join(map(str, bits)), 2)]))
    hs.add(tuple(hh)); sols.append(c)
    ids = [cid(v) for v in range(1 << n)]
    s.add_clause([-i if i in model else i for i in ids])
print(f"k'={kp}: {len(hs)} complement-invariant optimal colourings (cap {cap}); h over {nu}-bit transition words, h=1 set:")
for hh in sorted(hs):
    print("  ", ' '.join(format(d, f'0{nu}b') for d in range(1 << nu) if hh[d]))
