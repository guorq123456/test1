# cross-check TM output vs generic frontier DP for larger k, and recheck real-rootedness with sympy for selected cases
import sys, sympy as sp
from crt import parse_line
from frontier import gp_graph, ip_frontier
x = sp.symbols('x')
for k, nmax in [(5, 22), (6, 22), (7, 19), (8, 20)]:
    tm = {}
    for line in open('tm_k%d.txt' % k):
        kk, m, c = parse_line(line)
        if m <= nmax: tm[m] = c
    bad = 0
    for n in range(2*k+1, nmax+1):
        G = gp_graph(n, k); order = [z for i in range(n) for z in (('u', i), ('v', i))]
        c = ip_frontier(G, order)
        if c != tm[n]: bad += 1; print('MISMATCH', n, k)
    print('k=%d: checked n=%d..%d, mismatches %d' % (k, 2*k+1, nmax, bad), flush=True)
for n, k in [(15, 4), (18, 6), (13, 6), (12, 4), (10, 4)]:
    G = gp_graph(n, k); order = [z for i in range(n) for z in (('u', i), ('v', i))]
    c = ip_frontier(G, order); p = sp.Poly(list(reversed(c)), x)
    print((n, k), 'deg', p.degree(), 'sympy real roots', len(sp.real_roots(p)), 'squarefree', sp.gcd(p, p.diff(x)).degree() == 0, c)
