"""Independent verification for the A225034 / A163765 / A048775 / A005773 identities.

All arithmetic is exact (Python integers / Fractions).  Run:  python3 verify.py [N]
Checks (each prints OK or raises AssertionError):
  1. a(n) := A225034 computed from its DEFINITION by a 3-state automaton DP over
     (#1's, #0's)   [independent of the brute-force enumeration in enum101.c].
  2. a(n) = [y^n] G(y) phi(y)^n  (Lemma 1 / gap formula)  -- polynomial arithmetic.
  3. a(n) = sum_k (-1)^(n-1-k) C(n-1,k) C(2k+3,k+1), n>=1           (Lemma 2)
  4. a(n) = D(n)+D(n+1), n>=1, D = coefficients of 1/2+1/2*sqrt((1+x)/(1-3x))  (Thm 1)
  5. Berselli recurrence (n+1)a(n)-(2n+3)a(n-1)-3(n-2)a(n-2)=0, 2<=n<=N     (Thm 3)
  6. series of the 'Theorem' g.f. printed in A225034 equals a(n)
  7. A048775 from its DEFINITION (brute force, small n) and = C(2n+1,n+1)-(n+1)
  8. A163765 := inverse binomial transform of A048775 (offset 0) equals a(n) for n>=3,
     a(1)-2, a(2)-1 for n=1,2                                          (Thm 2)
  9. comparison with stored OEIS data / b-files.
"""
import sys
from math import comb
from fractions import Fraction

N = int(sys.argv[1]) if len(sys.argv) > 1 else 1200

# ---------- 1. automaton DP from the definition ----------
# states: 0 = (empty or last letter 0 not preceded by '1' i.e. no dangerous suffix),
#         1 = last letter 1, 2 = last two letters '10'.  Appending '1' in state 2 creates 101.
def a_by_automaton(N):
    # T[s][m] for current number of ones n, m zeros, built row by row in n.
    # We do a DP over words: process by (ones, zeros) lattice.
    # cnt[n][m][s]
    import array
    a = []
    # row-by-row: words with n ones and m zeros; recurrence on last letter.
    prev = None  # cnt for n-1 ones: list over m of [c0,c1,c2]
    for n in range(N + 1):
        cur = [[0, 0, 0] for _ in range(N + 1)]
        for m in range(N + 1):
            if n == 0 and m == 0:
                cur[0][0] = 1  # empty word in state 0
                continue
            c0 = c1 = c2 = 0
            if m > 0:  # last letter 0
                l = cur[m - 1]
                c0 += l[0] + l[2]   # from state 0 or '10' -> state 0
                c2 += l[1]          # from state '1'  -> '10'
            if n > 0:  # last letter 1
                l = prev[m]
                c1 += l[0] + l[1]   # from state 0 or '1'; state '10' forbidden
            cur[m] = [c0, c1, c2]
        a.append(sum(sum(cur[m]) for m in range(n + 1)))
        prev = cur
    return a

a = a_by_automaton(N)
print("automaton a(0..12):", a[:13])
with open("a225034_dp.txt","w") as f:
    for k,v in enumerate(a): f.write("%d\n"%v)

# ---------- 2. coefficient formula a(n) = [y^n] (1-y+y^2)^(n-1)/(1-y)^(n+2) ----------
def coef_formula(n):
    if n == 0:
        return 1
    # gap formula: sum over m<=n of [y^m] (1-y)^-2 * (1/(1-y) - y)^(n-1)
    # computed by truncated power series multiplication
    M = n + 1
    inv1 = [1] * M                       # 1/(1-y)
    P = [1] * M; P[1] -= 1               # 1/(1-y) - y
    S = [k + 1 for k in range(M)]        # 1/(1-y)^2
    for _ in range(n - 1):
        S = [sum(S[i] * P[k - i] for i in range(k + 1)) for k in range(M)]
    return sum(S)

for n in range(0, 61):
    assert coef_formula(n) == a[n], n
print("2. gap/coefficient formula (Lemma 1) OK for n<=60")

# ---------- 3. inverse binomial transform formula ----------
for n in range(1, N + 1):
    s = sum((-1) ** (n - 1 - k) * comb(n - 1, k) * comb(2 * k + 3, k + 1) for k in range(n))
    assert s == a[n], n
# also the binomial double sum of Lemma 1'
for n in range(1, 301):
    assert sum(comb(n - 1, j) * comb(j + 3, n - j) for j in range(n)) == a[n]
print("3. a(n)=sum (-1)^(n-1-k)C(n-1,k)C(2k+3,k+1) OK for 1<=n<=%d" % N)

# ---------- 4. D(n) from g.f. 1/2+1/2*sqrt((1+x)/(1-3x)) via its own ODE-free series ----------
# compute R = sqrt((1+x)/(1-3x)) by the Newton/convolution square root of Q=(1+x)/(1-3x)
Q = [1] + [4 * 3 ** (k - 1) for k in range(1, N + 3)]   # (1+x)/(1-3x) = 1 + sum 4*3^(k-1) x^k
R = [1] + [0] * (N + 2)
for k in range(1, N + 3):
    # (R^2)_k = Q_k  =>  2 R_0 R_k = Q_k - sum_{i=1}^{k-1} R_i R_{k-i}
    t = Q[k] - sum(R[i] * R[k - i] for i in range(1, k))
    assert t % 2 == 0
    R[k] = t // 2
D = [1] + [R[k] // 2 for k in range(1, N + 3)]
assert all(R[k] % 2 == 0 for k in range(1, N + 3))
print("D(0..12):", D[:13])
for n in range(1, N + 1):
    assert a[n] == D[n] + D[n + 1], n
assert a[0] == D[1]
print("4. a(n)=D(n)+D(n+1) OK for 1<=n<=%d, and a(0)=D(1)" % N)
# D also satisfies Somos' recurrence (sanity)
for n in range(2, N + 2):
    assert n * D[n] == 2 * n * D[n - 1] + 3 * (n - 2) * D[n - 2]

# ---------- 5. Berselli recurrence ----------
for n in range(2, N + 1):
    assert (n + 1) * a[n] - (2 * n + 3) * a[n - 1] - 3 * (n - 2) * a[n - 2] == 0, n
assert 2 * a[1] - 5 * a[0] == 1
print("5. Berselli recurrence OK for 2<=n<=%d" % N)

# ---------- 6. 'Theorem' g.f. of A225034 entry, expanded with sympy ----------
import sympy as sp
x = sp.symbols('x')
K = 60
gf = 2 * (1 - x**2) / (3 * x**2 - 4 * x + 1 + sp.sqrt((1 - x**2)**2 - 4 * (x - x**2) * (1 - x**2)))
ser = sp.series(gf, x, 0, K).removeO()
assert [ser.coeff(x, k) for k in range(K)] == a[:K]
gf2 = (1 + x) * (sp.sqrt((1 + x) / (1 - 3 * x)) - 1) / (2 * x)
ser2 = sp.series(gf2, x, 0, K).removeO()
assert [ser2.coeff(x, k) for k in range(K)] == a[:K]
print("6. entry's 'Theorem' g.f. and (1+x)(R-1)/(2x) both expand to a(n), n<%d" % K)

# ---------- 7. A048775 from its definition ----------
def a048775_brute(n):
    # pick interval [i..j] of 1..n (nonempty) and a nondecreasing map of it into 1..n
    from itertools import combinations_with_replacement
    cnt = 0
    for i in range(1, n + 1):
        for j in range(i, n + 1):
            s = j - i + 1
            cnt += sum(1 for _ in combinations_with_replacement(range(1, n + 1), s))
    return cnt
for n in range(1, 10):
    assert a048775_brute(n) == comb(2 * n + 1, n + 1) - (n + 1), n
for n in range(1, N + 2):
    assert sum((n + 1 - s) * comb(n + s - 1, s) for s in range(1, n + 1)) == comb(2 * n + 1, n + 1) - (n + 1)
print("7. A048775 definition (brute force n<=9) and Sloane sum (n<=%d) = C(2n+1,n+1)-(n+1)" % (N + 1))

A048775 = {n: comb(2 * n + 1, n + 1) - (n + 1) for n in range(1, N + 2)}

# ---------- 8. A163765 ----------
def A163765(n):  # offset 1; inverse binomial transform with both sequences re-indexed from 0
    m = n - 1
    return sum((-1) ** (m - k) * comb(m, k) * A048775[k + 1] for k in range(m + 1))
for n in range(1, N + 1):
    expect = a[n] - (2 if n == 1 else 0) - (1 if n == 2 else 0)
    assert A163765(n) == expect, n
print("8. A163765(n)=A225034(n) for 3<=n<=%d; A163765(1)=a(1)-2, A163765(2)=a(2)-1" % N)

# ---------- 9. stored data ----------
def read_b(fn):
    d = {}
    for line in open(fn):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        k, v = line.split()[:2]
        d[int(k)] = int(v)
    return d
b225 = read_b('b225034.txt'); b005 = read_b('b005773.txt'); b048 = read_b('b048775.txt'); b163 = read_b('b163765.txt')
for k, v in b225.items():
    if k <= N: assert a[k] == v, k
for k, v in b005.items():
    if k <= N + 1: assert D[k] == v, k
for k, v in b048.items():
    if k <= N + 1: assert A048775[k] == v, k
for k, v in b163.items():
    if k <= N: assert A163765(k) == v, k
print("9. b-files: A225034 n<=%d, A005773 n<=%d, A048775 n<=%d, A163765 n<=%d all agree"
      % (max(k for k in b225 if k <= N), max(b005), max(b048), max(b163)))

# compare with brute-force enumeration output of enum101.c
for fn in ('enum101.out', 'enum101_17.out'):
    try:
        for line in open(fn):
            k, v = map(int, line.split())
            assert a[k] == v, (fn, k)
        print("   brute-force enumeration file %s agrees" % fn)
    except FileNotFoundError:
        pass
print("ALL CHECKS PASSED")
