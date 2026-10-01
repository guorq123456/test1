# Independent generic check: frontier (pathwidth-style) DP on an arbitrary networkx graph.
import sys, networkx as nx, sympy as sp
from crt import parse_line
def gp_graph(n, k):
    G = nx.Graph()
    for i in range(n):
        G.add_edge(('u', i), ('u', (i+1) % n)); G.add_edge(('v', i), ('v', (i+k) % n)); G.add_edge(('u', i), ('v', i))
    return G
def ip_frontier(G, order):
    pos = {v: i for i, v in enumerate(order)}
    last = {v: max([pos[w] for w in G[v]] + [pos[v]]) for v in order}
    states = {frozenset(): [1]}
    for i, v in enumerate(order):
        new = {}
        def add(key, poly, shift):
            p = new.setdefault(key, [])
            if len(p) < len(poly)+shift: p.extend([0]*(len(poly)+shift-len(p)))
            for j, c in enumerate(poly): p[j+shift] += c
        for S, poly in states.items():
            # exclude v
            add(frozenset(w for w in S if last[w] > i), poly, 0)
            # include v if no neighbor in S
            if not any(w in S for w in G[v]):
                S2 = set(w for w in S if last[w] > i)
                if last[v] > i: S2.add(v)
                add(frozenset(S2), poly, 1)
        states = new
    assert list(states.keys()) == [frozenset()]
    p = states[frozenset()]
    while p and p[-1] == 0: p.pop()
    return p
if __name__ == '__main__':
    tmfile = {k: {} for k in (1, 2, 3, 4)}
    for k in (1, 2, 3, 4):
        for line in open('tm_k%d.txt' % k):
            kk, m, c = parse_line(line)
            if m <= 60: tmfile[k][m] = c
    x = sp.symbols('x')
    cases = [(n, k) for k in (1, 2, 3, 4) for n in range(2*k+1, int(sys.argv[1])+1)]
    mism = 0
    for n, k in cases:
        G = gp_graph(n, k)
        order = [z for i in range(n) for z in (('u', i), ('v', i))]
        c = ip_frontier(G, order)
        if c != tmfile[k][n]: mism += 1; print('MISMATCH', n, k)
    print('checked', len(cases), 'cases, mismatches', mism)
    for n, k in [(25, 2), (20, 4), (30, 2), (30, 4)]:
        G = gp_graph(n, k); order = [z for i in range(n) for z in (('u', i), ('v', i))]
        c = ip_frontier(G, order)
        p = sp.Poly(list(reversed(c)), x)
        nr = len(sp.real_roots(p))
        nonreal = [complex(z) for z in p.nroots(n=40, maxsteps=500) if abs(complex(z).imag) > 1e-20]
        print((n, k), 'deg', p.degree(), 'real roots (sympy)', nr, 'non-real roots:', [ '%.6f%+.6fi' % (z.real, z.imag) for z in nonreal])
        print('   coeffs', c)
