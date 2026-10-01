#!/usr/bin/env python3
"""Reproduce stored OEIS data for A112046, A112049, A112051, A112052, A216244
directly from the definitions, using a self-written Jacobi symbol
(cross-checked against sympy.jacobi_symbol on a range)."""
import sys, gzip
from sympy import jacobi_symbol, prime, isprime, primepi

def jacobi(a, m):
    """Jacobi symbol (a/m) for odd m >= 1 (textbook binary algorithm)."""
    assert m > 0 and m % 2 == 1
    a %= m
    s = 1
    while a:
        while a % 2 == 0:
            a //= 2
            if m % 8 in (3, 5):
                s = -s
        a, m = m, a
        if a % 4 == 3 and m % 4 == 3:
            s = -s
        a %= m
    return s if m == 1 else 0

# cross-check jacobi against sympy
for m in range(1, 2000, 2):
    for a in range(0, 300):
        assert jacobi(a, m) == jacobi_symbol(a, m), (a, m)
print("jacobi() agrees with sympy for odd m<2000, 0<=a<300")

def A112046(n):
    m = 2*n + 1
    k = 1
    while jacobi(k, m) == 1:
        k += 1
    return k

def read_b(fn):
    d = {}
    for line in open(fn):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        i, v = line.split()[:2]
        d[int(i)] = int(v)
    return d

def oeis_data(anum):
    with gzip.open('/tmp/claude-0/oeis/stripped.gz', 'rt') as f:
        for line in f:
            if line.startswith(anum + ' '):
                return [int(x) for x in line.split(' ', 1)[1].strip().strip(',').split(',')]

NMAX = 40000
a46 = [None] + [A112046(n) for n in range(1, NMAX + 1)]

b46 = read_b('/tmp/claude-0/deep/nonresidue/b112046.txt')
assert all(a46[i] == v for i, v in b46.items()), "A112046 b-file mismatch"
print("A112046: b-file n=1..%d reproduced" % max(b46))

b49 = read_b('/tmp/claude-0/deep/nonresidue/b112049.txt')
assert all(isprime(a46[i]) for i in range(1, NMAX + 1))
assert all(primepi(a46[i]) == v for i, v in b49.items()), "A112049 b-file mismatch"
print("A112049: b-file n=1..%d reproduced; all A112046(n), n<=%d, are prime" % (max(b49), NMAX))

# A112051 literally from its definition
def A112051_list(seq, nmax_index):
    out = [1]
    while True:
        prev = out[-1]
        seen = set(seq[1:prev + 1])
        i = prev + 1
        while i <= nmax_index and seq[i] in seen:
            i += 1
        if i > nmax_index:
            return out
        out.append(i)

a51 = A112051_list(a46, NMAX)
d51 = oeis_data('A112051')
assert a51[:len(d51)] == d51, "A112051 data mismatch"
print("A112051: stored %d terms reproduced; computed %d terms (indices <= %d)" % (len(d51), len(a51), NMAX))
d52 = oeis_data('A112052')
assert [2*x + 1 for x in a51[:len(d52)]] == d52
print("A112052: stored %d terms reproduced" % len(d52))

# compare with A216244 = (prime(n)^2-1)/2, n>=2
b244 = read_b('/tmp/claude-0/deep/nonresidue/b216244.txt')
assert all(v == (prime(n)**2 - 1)//2 for n, v in b244.items())
print("A216244: b-file n=2..%d equals (prime(n)^2-1)/2" % max(b244))
for n, v in enumerate(a51, start=1):
    if n >= 4:
        assert v == (prime(n)**2 - 1)//2 == b244[n], n
print("A112051(n) = A216244(n) = (prime(n)^2-1)/2 for 4 <= n <= %d (all A112051 terms with index <= %d)" % (len(a51), NMAX))
print("A112051(1..3) =", a51[:3], " A216244(2..3) =", [b244[2], b244[3]])
