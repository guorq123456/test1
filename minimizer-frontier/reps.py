"""Test: pick one representative edge per rotation class of (n+1)-bit strings (D);
is B(2,n) minus D bipartite?  If yes -> optimal sigma=w=2 scheme for odd k'=n-1."""
import sys, numpy as np
from collections import deque
from w2 import cycles, charged_count, bound_charged

def rotations(e, m):
    out = []
    x = e
    for _ in range(m):
        out.append(x); x = ((x << 1) | (x >> (m - 1))) & ((1 << m) - 1)
    return out

def bits(e, m): return format(e, f'0{m}b')

RULES = {
  'min_rot'      : lambda rots, m: min(rots),
  'max_rot'      : lambda rots, m: max(rots),
  'min_rot_shift1': lambda rots, m: rotations(min(rots), m)[1],
  'max_rot_shift1': lambda rots, m: rotations(max(rots), m)[1],
  'min_rot_shift-1': lambda rots, m: rotations(min(rots), m)[-1],
  'max_rot_shift-1': lambda rots, m: rotations(max(rots), m)[-1],
  'min_colex'    : lambda rots, m: min(rots, key=lambda r: bits(r, m)[::-1]),
  'max_colex'    : lambda rots, m: max(rots, key=lambda r: bits(r, m)[::-1]),
  'min_altlex'   : lambda rots, m: min(rots, key=lambda r: [int(b) ^ (i & 1) for i, b in enumerate(bits(r, m))]),
  'max_altlex'   : lambda rots, m: max(rots, key=lambda r: [int(b) ^ (i & 1) for i, b in enumerate(bits(r, m))]),
}

def bipartite_colouring(n, D):
    """2-colour B(2,n) minus edge set D. returns c or None."""
    N = 1 << n; mask = N - 1
    adj = [[] for _ in range(N)]
    for e in range(1 << (n + 1)):
        if e in D: continue
        u, v = e >> 1, e & mask
        if u == v: continue
        adj[u].append(v); adj[v].append(u)
    c = -np.ones(N, dtype=np.int64)
    for s0 in range(N):
        if c[s0] >= 0: continue
        c[s0] = 0; dq = deque([s0])
        while dq:
            u = dq.popleft()
            for v in adj[u]:
                if c[v] < 0: c[v] = 1 - c[u]; dq.append(v)
                elif c[v] == c[u]: return None
    return c

def test_rule(rule, n):
    m = n + 1
    D = set()
    for cyc in cycles(m):
        D.add(RULES[rule](cyc, m))
    c = bipartite_colouring(n, D)
    if c is None: return False, None
    ch = charged_count(c, n)
    return ch == bound_charged(n), c

if __name__ == '__main__':
    ns = [int(a) for a in sys.argv[1].split(',')] if len(sys.argv) > 1 else [2, 4, 6, 8, 10, 12]
    for rule in RULES:
        res = []
        for n in ns:
            ok, c = test_rule(rule, n)
            res.append('Y' if ok else '.')
        print(f"{rule:16s} n={ns}: {' '.join(res)}")
