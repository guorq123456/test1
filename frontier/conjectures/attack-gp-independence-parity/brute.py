# Independent brute-force: independence polynomial via bitmask recursion I(G)=I(G-v)+x I(G-N[v])
import sys
from functools import lru_cache
import sympy as sp

def gp_adj(n, k):
    N = 2*n
    adj = [0]*N
    def add(a, b):
        adj[a] |= 1 << b; adj[b] |= 1 << a
    for i in range(n):
        add(i, (i+1) % n)          # u_i u_{i+1}
        add(n+i, n+(i+k) % n)      # v_i v_{i+k}
        add(i, n+i)                # spoke
    return adj

def indep_poly(adj):
    N = len(adj)
    @lru_cache(maxsize=None)
    def rec(mask):
        if mask == 0:
            return (1,)
        v = (mask & -mask).bit_length() - 1
        # choose v with max degree in mask for better branching
        best, bd = v, -1
        m = mask
        while m:
            w = (m & -m).bit_length() - 1
            m &= m - 1
            d = bin(adj[w] & mask).count('1')
            if d > bd:
                best, bd = w, d
        v = best
        if bd == 0:
            c = bin(mask).count('1')
            # (1+x)^c
            from math import comb
            return tuple(comb(c, j) for j in range(c+1))
        a = rec(mask & ~(1 << v))
        b = rec(mask & ~(1 << v) & ~adj[v])
        L = max(len(a), len(b)+1)
        res = [0]*L
        for i, c in enumerate(a): res[i] += c
        for i, c in enumerate(b): res[i+1] += c
        return tuple(res)
    return list(rec((1 << N) - 1))

def nreal(coeffs):
    x = sp.symbols('x')
    p = sp.Poly(list(reversed(coeffs)), x)
    return sp.count_roots(p), p.degree()

if __name__ == '__main__':
    nmax = int(sys.argv[1]) if len(sys.argv) > 1 else 14
    for n in range(3, nmax+1):
        for k in range(1, (n+1)//2):
            if 2*k >= n: continue
            c = indep_poly(gp_adj(n, k))
            r, d = nreal(c)
            print(n, k, 'deg', d, 'real', r, 'REALROOTED' if r == d else 'not', c)
