# Simplest possible check: enumerate all 2^(2n) vertex subsets of GP(n,k) (via networkx edge list), count independent ones by size.
import itertools, networkx as nx, sympy as sp, mpmath as mp
def gp_graph(n, k):
    G = nx.Graph()
    for i in range(n):
        G.add_edge(('u', i), ('u', (i+1) % n)); G.add_edge(('v', i), ('v', (i+k) % n)); G.add_edge(('u', i), ('v', i))
    return G
def naive_ip(G):
    V = list(G.nodes()); idx = {v: i for i, v in enumerate(V)}; N = len(V)
    emasks = [(1 << idx[a]) | (1 << idx[b]) for a, b in G.edges()]
    cnt = [0]*(N+1)
    for S in range(1 << N):
        ok = True
        for e in emasks:
            if S & e == e: ok = False; break
        if ok: cnt[bin(S).count('1')] += 1
    while cnt[-1] == 0: cnt.pop()
    return cnt
x = sp.symbols('x')
for (n, k) in [(9, 2), (9, 4), (7, 3), (3, 1)]:
    G = gp_graph(n, k)
    assert G.number_of_nodes() == 2*n and G.number_of_edges() == 3*n and all(d == 3 for _, d in G.degree())
    c = naive_ip(G)
    p = sp.Poly(list(reversed(c)), x)
    rr = sp.real_roots(p)
    print((n, k), 'coeffs', c, 'deg', p.degree(), '#real roots (sympy real_roots, with mult.)', len(rr))
    print('   numeric roots:', [complex(z) for z in sp.Poly(p).nroots(n=30)])
    # Newton inequalities
    d = len(c)-1
    bad = [j for j in range(1, d) if sp.Rational(c[j]**2) < sp.Rational(c[j-1]*c[j+1])*(1+sp.Rational(1, j))*(1+sp.Rational(1, d-j))]
    print('   Newton inequality failures at j =', bad)
