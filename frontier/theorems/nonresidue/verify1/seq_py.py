# Independent implementation directly from OEIS definitions (Python, small range)
import gzip, sys
from sympy import jacobi_symbol, prime, primerange, isprime

def jac(a, n):
    # own Jacobi symbol (n odd positive)
    assert n > 0 and n % 2 == 1
    a %= n
    res = 1
    while a:
        while a % 2 == 0:
            a //= 2
            if n % 8 in (3, 5):
                res = -res
        a, n = n, a
        if a % 4 == 3 and n % 4 == 3:
            res = -res
        a %= n
    return res if n == 1 else 0

# cross-check own jacobi vs sympy
for n in range(1, 600, 2):
    for a in range(0, 200):
        assert jac(a, n) == jacobi_symbol(a, n), (a, n)
print("own jacobi == sympy on odd n<600, a<200")

def A112046(i):
    m = 2*i + 1
    k = 1
    while jac(k, m) == 1:
        k += 1
    return k

IMAX = 2_000_000
vals = [None] + [A112046(i) for i in range(1, IMAX+1)]

# Literal A112051 definition
a = [1]
S = set(vals[1:2])  # values A112046(1..a(1))
last = 1
while True:
    i = last + 1
    while i <= IMAX and vals[i] in S:
        i += 1
    if i > IMAX:
        break
    # a(n) = i ; update S to values A112046(1..i)
    for j in range(last+1, i+1):
        S.add(vals[j])
    a.append(i)
    last = i
print("A112051 terms computed:", len(a))
# stored terms
def oeis_terms(A):
    with gzip.open('/tmp/claude-0/oeis/stripped.gz', 'rt') as f:
        for line in f:
            if line.startswith(A + ' '):
                return [int(x) for x in line.split()[1].strip(',').split(',')]
st = oeis_terms('A112051')
print("stored A112051 len", len(st), "match:", a[:len(st)] == st)
st46 = oeis_terms('A112046')
print("stored A112046 match:", vals[1:len(st46)+1] == st46)
st52 = oeis_terms('A112052')
print("stored A112052 match:", [2*x+1 for x in a[:len(st52)]] == st52)
st244 = oeis_terms('A216244')  # offset 2
A216244 = {n: (prime(n)**2 - 1)//2 for n in range(2, len(a)+5)}
print("stored A216244 match formula:", all(st244[k] == A216244[k+2] for k in range(len(st244))))
bad = [n for n in range(1, len(a)+1) if n >= 2 and a[n-1] != A216244[n]]
print("n where A112051(n) != A216244(n):", bad)
print("first terms", a[:6])
# all values prime?
print("all values prime:", all(isprime(v) for v in vals[1:]))
# f(m)^2 > m cases
print("f(m)^2>m:", [2*i+1 for i in range(1, IMAX+1) if vals[i]**2 > 2*i+1])
