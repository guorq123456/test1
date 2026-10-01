from math import comb
from fractions import Fraction
import itertools
def readb(fn):
    d={}
    for line in open(fn):
        line=line.strip()
        if not line or line[0]=='#': continue
        k,v=line.split()[:2]; d[int(k)]=int(v)
    return d
a = {int(l.split()[0]):int(l.split()[1]) for l in open('a_dp.txt')}
N = max(a)
# R = sqrt((1+x)/(1-3x)) as exact integer series: R^2 = (1+x)*sum 3^k x^k
M = N+2
P = [0]*(M+1)
for k in range(M+1):
    P[k] = 3**k + (3**(k-1) if k>=1 else 0)
# sqrt with R0=1: 2 R_n = P_n - sum_{i=1}^{n-1} R_i R_{n-i}
R=[1]+[0]*M
for n in range(1,M+1):
    s = P[n]-sum(R[i]*R[n-i] for i in range(1,n))
    assert s%2==0
    R[n]=s//2
D = [1]+[R[n]//2 if R[n]%2==0 else None for n in range(1,M+1)]
assert all(d is not None for d in D)
bD = readb('b005773.txt')
assert all(D[k]==v for k,v in bD.items()); print("D from (1+R)/2 matches A005773 b-file n<=",max(bD))
# Somos recurrence n D(n) = 2n D(n-1) + 3(n-2) D(n-2)
for n in range(2,M+1):
    assert n*D[n]==2*n*D[n-1]+3*(n-2)*D[n-2]
print("Somos recurrence for D ok")
assert a[0]==D[1]
for n in range(1,N+1):
    assert a[n]==D[n]+D[n+1], n
print("(3) a(n)=D(n)+D(n+1) n=1..",N, "; a(0)=D(1); D(0)+D(1)=",D[0]+D[1])
# (2) 2x A = (1+x)(R-1)
for n in range(0,N+1):
    lhs = 2*a[n]  # coefficient of x^{n+1} in 2xA
    rhs = R[n+1] + R[n] - (1 if n==0 else 0)  # [x^{n+1}] (1+x)(R-1): (R-1)_{n+1} + (R-1)_n
    assert lhs==rhs, n
print("(2) 2xA=(1+x)(R-1) ok to x^",N+1)
# (5) recurrence
for n in range(2,N+1):
    assert (n+1)*a[n]-(2*n+3)*a[n-1]-3*(n-2)*a[n-2]==0, n
print("(5) recurrence ok n=2..",N, "; 2a1-5a0 =",2*a[1]-5*a[0], "; n=1 recurrence lhs:", 2*a[1]-5*a[0])
# (4) A048775 brute force from the definition
def b_brute(n):
    tot=0
    for i in range(1,n+1):
        for j in range(i,n+1):
            s=j-i+1
            # nondecreasing maps from s-chain to 1..n
            tot += sum(1 for f in itertools.product(range(1,n+1),repeat=s) if all(f[t]<=f[t+1] for t in range(s-1)))
    return tot
bb = [None]+[b_brute(n) for n in range(1,8)]
print("A048775 brute:",bb[1:])
bf48 = readb('b048775.txt')
for n in range(1,8): assert bb[n]==bf48[n]
for n in range(1,1001): assert bf48[n]==comb(2*n+1,n+1)-(n+1)
print("A048775 b-file = C(2n+1,n+1)-(n+1) for n<=1000")
b = lambda n: comb(2*n+1,n+1)-(n+1)
# A163765 from its definition: inverse binomial transform with offset zero in both
c = {}
for m in range(0,N):
    c[m+1] = sum((-1)**(m-k)*comb(m,k)*b(k+1) for k in range(m+1))
bc = readb('b163765.txt')
assert all(c[k]==v for k,v in bc.items()); print("A163765 def reproduces stored terms n<=",max(bc))
# check example
assert -1*1+3*7-3*31+121==48==c[4]
for n in range(1,N+1):
    assert c[n]==a[n]-2*(n==1)-(n==2), n
print("(4) c(n)=a(n)-2[n=1]-[n=2] n<=",N, " c1,c2=",c[1],c[2])
# using bfile values of A048775 directly (no formula) for n<=1000
c2={}
for m in range(0,1000):
    c2[m+1]=sum((-1)**(m-k)*comb(m,k)*bf48[k+1] for k in range(m+1))
    assert c2[m+1]==a[m+1]-2*(m==0)-(m==1)
print("(4') using A048775 bfile directly, ok n<=1000")
