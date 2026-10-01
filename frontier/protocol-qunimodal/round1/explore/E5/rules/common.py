# shared helpers (cheap: O(k r^2), independent of b and of the size of a_i)
def gamma(r, a):
    """Gamma_s = number of (x_1..x_k), 0<=x_i<a_i, with sum x_i = s (mod r); s=0..r-1.
    Computed by cyclic convolution of the indicator of {0..a_i-1} reduced mod r."""
    G = [0]*r; G[0] = 1
    for x in a:
        v = [0]*r
        for t in range(r):
            v[t] = x//r + (1 if t < x % r else 0)
        G = [sum(G[u]*v[(s-u) % r] for u in range(r)) for s in range(r)]
    return G
def low_f(r, a, n):
    """f_j = A_j - A_{j-1} for j=0..n-1, A(q)=prod [a_i]_q (computed mod q^n)."""
    A = [1] + [0]*n
    for x in a:
        B = [0]*(n+1)
        s = 0
        for t in range(n+1):
            s += A[t]
            if t-x >= 0: s -= A[t-x]
            B[t] = s
        A = B
    return [A[j] - (A[j-1] if j else 0) for j in range(n)]
