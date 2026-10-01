# Independent brute-force independence polynomial of GP(n,k) from Definition 2.1
import sys
from functools import lru_cache

def gp_adj(n, k):
    # vertices: u_i -> i, v_i -> n+i
    N = 2*n
    adj = [0]*N
    def add(a, b):
        assert a != b
        adj[a] |= 1 << b; adj[b] |= 1 << a
    for i in range(n):
        add(i, (i+1) % n)          # u_i u_{i+1}
        add(n+i, n+(i+k) % n)      # v_i v_{i+k}
        add(i, n+i)                # spoke
    return N, adj

def indep_poly_backtrack(n, k):
    N, adj = gp_adj(n, k)
    counts = [0]*(N+1)
    # plain backtracking: decide each vertex in order
    sys.setrecursionlimit(10000)
    def rec(i, chosen_mask, size):
        if i == N:
            counts[size] += 1
            return
        rec(i+1, chosen_mask, size)
        if not (adj[i] & chosen_mask):
            rec(i+1, chosen_mask | (1 << i), size+1)
    rec(0, 0, 0)
    while counts and counts[-1] == 0:
        counts.pop()
    return counts

def indep_poly_subsets(n, k):
    # literal enumeration of all 2^(2n) subsets
    N, adj = gp_adj(n, k)
    edges = [(a, b) for a in range(N) for b in range(a+1, N) if adj[a] >> b & 1]
    counts = [0]*(N+1)
    for S in range(1 << N):
        ok = True
        for a, b in edges:
            if (S >> a) & 1 and (S >> b) & 1:
                ok = False; break
        if ok:
            counts[bin(S).count('1')] += 1
    while counts[-1] == 0: counts.pop()
    return counts

if __name__ == '__main__':
    for (n, k) in [(3,1), (5,2), (7,2), (7,3), (9,2), (9,4)]:
        print(n, k, indep_poly_backtrack(n, k))
