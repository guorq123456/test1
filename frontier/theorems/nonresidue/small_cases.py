#!/usr/bin/env python3
"""Finite checks used in proof.md.

(1) For every odd prime q < 529 compute n(q) (least quadratic non-residue) by brute
    force (Euler's criterion) and list the q with n(q)^2 > q.  Expected: 3, 7, 23.
(2) The hand check of Step 4: primes q == 7 (mod 8) in the open intervals
    (n(n-1), n^2) for n in {7,11,13,17,19,23}, with their n(q).
(3) Exhaustive sanity check of the arithmetic Lemma C (the (s-t)(s+t) construction):
    for every odd n with 29 <= n <= NMAX and every odd integer q with
    n(n-1) < q < n^2, the explicit a=s-t, b=s+t satisfy 1<=a<=b<=n-1 and
    q-n+2 <= 2ab <= q-1.  (Primality of q, n is irrelevant for the lemma.)
    Also report, for odd n < 29, the cases where the construction fails
    (showing the threshold 29 is not an artifact).
(4) Exact verification of the two numerical inequalities at n = 29.
"""
from math import isqrt
from fractions import Fraction
from sympy import primerange, isprime

def n_of(q):
    """least quadratic non-residue mod odd prime q, via Euler's criterion"""
    for k in range(2, q):
        if pow(k, (q - 1)//2, q) == q - 1:
            return k
    raise ValueError

# (1)
exc = []
print("q : n(q) for odd primes q < 529")
row = []
for q in primerange(3, 529):
    nq = n_of(q)
    row.append("%d:%d" % (q, nq))
    if nq*nq > q:
        exc.append((q, nq))
for i in range(0, len(row), 12):
    print("  " + "  ".join(row[i:i+12]))
print("odd primes q < 529 with n(q)^2 > q:", exc)
assert exc == [(3, 2), (7, 3), (23, 5)]

# (2)
print("\nStep 4 hand check: primes q = 7 mod 8 in (n(n-1), n^2):")
for n in [7, 11, 13, 17, 19, 23]:
    lst = [(q, n_of(q)) for q in primerange(n*(n-1) + 1, n*n) if q % 8 == 7]
    allp = list(primerange(n*(n-1) + 1, n*n))
    print("  n=%2d interval (%d,%d): primes %s ; those = 7 mod 8 with n(q): %s" % (n, n*(n-1), n*n, allp, lst))
    assert all(nq != n for q, nq in lst)

# (3)
def construct(n, q):
    Np = (q - n + 2)//2          # integer since q, n odd
    s = isqrt(Np)
    if s*s < Np:
        s += 1                    # s = ceil(sqrt(N'))
    D = s*s - Np
    t = isqrt(D)                  # t = floor(sqrt(D))
    return s - t, s + t

NMAX = 4001
cnt = 0
for n in range(29, NMAX + 1, 2):
    for q in range(n*(n-1) + 1, n*n, 2):
        a, b = construct(n, q)
        assert 1 <= a <= b <= n - 1 and q - n + 2 <= 2*a*b <= q - 1, (n, q, a, b)
        cnt += 1
print("\nLemma C construction verified for all %d pairs (odd n in [29,%d], odd q in (n(n-1),n^2))" % (cnt, NMAX))
for n in range(3, 29, 2):
    bad = [q for q in range(n*(n-1) + 1, n*n, 2)
           if not (lambda ab: 1 <= ab[0] <= ab[1] <= n-1 and q-n+2 <= 2*ab[0]*ab[1] <= q-1)(construct(n, q))]
    if bad:
        print("  n=%d: construction fails for odd q in %s" % (n, bad))

# (4) exact check of the inequalities at n = 29 (and monotonicity is proved in the text)
# (i)  4*2^(1/4)*sqrt(n) + 3 <= n   <=>  (n-3)^4 >= 512 n^2      (both sides >= 0, n >= 3)
# (ii) n/sqrt2 + 1 + 2^(1/4) sqrt(n) <= n - 1  <=> (1-1/sqrt2) n - 2 >= 2^(1/4) sqrt n
n = 29
assert (n - 3)**4 >= 512 * n * n
print("\n(i) at n=29: (n-3)^4 = %d >= 512 n^2 = %d" % ((n-3)**4, 512*n*n))
import mpmath
mpmath.mp.dps = 50
lhs = (1 - 1/mpmath.sqrt(2))*n - 2
rhs = mpmath.root(2, 4)*mpmath.sqrt(n)
print("(ii) at n=29: (1-1/sqrt2)n-2 = %s  >  2^(1/4)sqrt(n) = %s" % (mpmath.nstr(lhs, 12), mpmath.nstr(rhs, 12)))
assert lhs > rhs
