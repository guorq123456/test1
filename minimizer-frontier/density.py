"""Exact density of (w,k)-forward/local sampling schemes over alphabet sigma.

A scheme is f: window(length w+k-1) -> offset in [0,w).  A context is a string of
length L=w+k; it is charged iff f(suffix)+1 != f(prefix), i.e. the window
starting one position later selects a *new* absolute position.
density = #charged / sigma^L   (exact expectation over uniform random strings)
"""
import numpy as np
from math import gcd
from functools import lru_cache

def mobius(n):
    res, m, p = 1, n, 2
    while p * p <= m:
        if m % p == 0:
            m //= p
            if m % p == 0:
                return 0
            res = -res
        p += 1
    if m > 1:
        res = -res
    return res

def aperiodic_necklaces(sigma, p):
    """M_sigma(p): number of aperiodic necklaces (Lyndon words) of length p."""
    return sum(mobius(d) * sigma ** (p // d) for d in range(1, p + 1) if p % d == 0) // p

def g_sigma(sigma, w, k):
    L = w + k
    tot = sum(aperiodic_necklaces(sigma, p) * (-(-p // w)) for p in range(1, L + 1) if L % p == 0)
    return tot / sigma ** L

def g_prime(sigma, w, k):
    kp = k
    while kp % w != 1 % w:
        kp += 1
    return max(g_sigma(sigma, w, k), g_sigma(sigma, w, kp))

def contexts(sigma, L):
    return np.arange(sigma ** L, dtype=np.int64)

def density_of(f, sigma, w, k):
    """f: int array over sigma^(w+k-1) windows, values in [0,w). Returns (density, charged, forward_ok)."""
    L = w + k
    C = contexts(sigma, L)
    pre = C // sigma
    suf = C % (sigma ** (L - 1))
    fp, fs = f[pre], f[suf]
    forward_ok = bool(np.all(fp - fs <= 1))
    charged = int(np.count_nonzero(fs + 1 != fp))
    return charged / sigma ** L, charged, forward_ok

def kmers_of_window(W, sigma, w, k):
    """k-mer codes of the w k-mers in window code W (length w+k-1)."""
    n = w + k - 1
    digits = [(W // sigma ** (n - 1 - i)) % sigma for i in range(n)]
    out = []
    for i in range(w):
        v = 0
        for j in range(k):
            v = v * sigma + digits[i + j]
        out.append(v)
    return out

def minimizer_scheme(order, sigma, w, k):
    """order: array rank[kmer]. Leftmost smallest-rank k-mer in window."""
    n = w + k - 1
    f = np.zeros(sigma ** n, dtype=np.int64)
    for W in range(sigma ** n):
        ks = kmers_of_window(W, sigma, w, k)
        ranks = [order[x] for x in ks]
        f[W] = int(np.argmin(ranks))
    return f

if __name__ == '__main__':
    rng = np.random.default_rng(0)
    for sigma, w, k in [(2, 2, 3), (2, 3, 2), (4, 3, 3), (2, 4, 5)]:
        order = rng.permutation(sigma ** k)
        f = minimizer_scheme(order, sigma, w, k)
        d, c, ok = density_of(f, sigma, w, k)
        print(f"sigma={sigma} w={w} k={k} random-minimizer density={d:.4f} (2/(w+1)={2/(w+1):.4f}) forward={ok}  g={g_sigma(sigma,w,k):.4f} g'={g_prime(sigma,w,k):.4f}")
