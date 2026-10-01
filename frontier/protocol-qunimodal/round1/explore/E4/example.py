#!/usr/bin/env python3
"""Print the Lemma-4 decomposition A = U + V (proof.txt) for a few fit-box tuples, symbolically.
Usage: python3 example.py"""
import sympy as sp
q = sp.symbols('q')
def br(n): return sum(q**i for i in range(n))

def decompose(r, a):
    D, M = 0, 0
    U = []          # list of (mult, e, c, [H factors])
    V = {0: 1}      # j -> mult
    for ap in a:
        mp, spp = divmod(ap, r)
        U = [(mu, e, c, H + [ap]) for (mu, e, c, H) in U]
        V2 = {}
        for j, mu in V.items():
            L = D + 1 - 2*j; e = L - r*M - 1
            delta = spp if spp <= e + 1 else e + 1
            d0 = min(delta, min(L, ap))
            for d in range(d0):
                V2[j + d] = V2.get(j + d, 0) + mu
            if d0 < min(L, ap):
                c1, c2 = L - d0, ap - d0
                c, h = (c1, c2) if c1 % r == 0 else (c2, c1)
                U.append((mu, j + d0, c, [h]))
        V = V2; D += ap - 1; M += mp
    return D, M, U, V

for r, a in [(3, [4, 5]), (3, [2, 2, 2, 2, 2, 2]), (4, [5, 6, 7]), (5, [3, 4, 7, 9])]:
    D, M, U, V = decompose(r, a)
    A = sp.expand(sp.Mul(*[br(x) for x in a]))
    Upoly = sum(mu * q**e * br(c) * sp.Mul(*[br(h) for h in H]) for (mu, e, c, H) in U)
    Vpoly = sum(mu * q**j * br(D + 1 - 2*j) for j, mu in V.items())
    ok = sp.expand(Upoly + Vpoly - A) == 0
    print('r=%d a=%s D=%d M=%d  identity_ok=%s' % (r, a, D, M, ok))
    print('   U terms (mult, q^e, [c], H):', [(mu, e, c, H) for (mu, e, c, H) in U])
    print('   V chains (mult, q^j, [L]):', [(mu, j, D + 1 - 2*j) for j, mu in sorted(V.items())],
          ' min L =', min([D + 1 - 2*j for j in V], default=None), '>= rM+1 =', r*M + 1)
