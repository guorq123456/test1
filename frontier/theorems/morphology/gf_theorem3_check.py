"""
Sanity checks for Theorem 3 (proof.md Section 5); the theorem itself is proved by hand.
 (1) the block-decomposition recursion  E_{-1}=1, F_k = E_{k-1}/(1-x E_{k-1}), E_k = F_k - x
     reproduces B(M,k) (computed from the definition by dp.B_all_fast), k<=25, M<100;
 (2) the polynomial identities b_{k+1} = b_k + y B_k,  B_{k+1} = B_k + b_{k+1}, k<=60;
 (3) the closed form b_k/(b_k - x B_k) reproduces A(N,k), k<=40, N<120;
 (4) the recurrence coefficients (-1)^(j+1) C(k+1+floor((j-1)/2), j) coincide with the
     'Empirical' recurrences of A200886 columns k=1..7 (parsed from the entry).
"""
import re
import sympy as sp
from math import comb
from dp import A_all_fast, B_all_fast

L = 100
def mul(a, b):
    r = [0]*L
    for i, ai in enumerate(a):
        if ai:
            for j in range(L-i):
                r[i+j] += ai*b[j]
    return r
def inv(a):  # a[0] == 1
    r = [0]*L; r[0] = 1
    for n in range(1, L):
        r[n] = -sum(a[i]*r[n-i] for i in range(1, n+1))
    return r
X = [0, 1] + [0]*(L-2)
E = [1] + [0]*(L-1)
ok1 = True
for k in range(0, 26):
    xE = mul(X, E)
    F = mul(E, inv([1 - xE[0]] + [-t for t in xE[1:]]))
    ok1 &= F == B_all_fast(L-1, k)
    E = F[:]; E[1] -= 1
print('(1) block recursion = B(M,k) from definition, k<=25, M<100:', ok1)

y = sp.symbols('y')
b = lambda n: sum(comb(n+j, 2*j)*y**j for j in range(n+1))
B = lambda n: sum(comb(n+1+j, 2*j+1)*y**j for j in range(n+1))
ok2 = all(sp.expand(b(n+1) - b(n) - y*B(n)) == 0 and sp.expand(B(n+1) - B(n) - b(n+1)) == 0 for n in range(0, 61))
print('(2) Morgan-Voyce identities k<=60:', ok2)

def series_div(p, q, n):
    out = []
    for i in range(n):
        s = (p[i] if i < len(p) else 0) - sum(q[j]*out[i-j] for j in range(1, min(i, len(q)-1)+1))
        out.append(s // q[0])
    return out
ok3 = True
for k in range(0, 41):
    num = [0]*(2*k+3); den = [0]*(2*k+3)
    for j in range(k+1):
        num[2*j] += comb(k+j, 2*j); den[2*j] += comb(k+j, 2*j); den[2*j+1] -= comb(k+1+j, 2*j+1)
    ok3 &= series_div(num, den, 120) == A_all_fast(119, k)
print('(3) closed form = A(N,k), k<=40, N<120:', ok3)

txt = open('/tmp/claude-0/deep/morphology/entries/A200886.seq').read()
ok4 = True
for k, rec in re.findall(r'k=(\d+): a\(n\) = ([^\n]*)', txt):
    k = int(k)
    co = {}
    for sign, c, i in re.findall(r'([+-]?)(\d*)\*?a\(n-(\d+)\)', rec.replace(' ', '')):
        co[int(i)] = (-1 if sign == '-' else 1)*(int(c) if c else 1)
    mine = {j: (-1)**(j+1)*comb(k+1+(j-1)//2, j) for j in range(1, 2*k+2)}
    ok4 &= co == mine
    print('   k=%d' % k, co == mine)
print('(4) general recurrence = empirical recurrences of A200886 k=1..7:', ok4)
