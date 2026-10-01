import sys
sys.path.insert(0,'.')
from fast import A_seq, B_seq
from mine import b_ok
from itertools import product
from math import comb
def series_div(p, q, n):  # p/q power series, q[0]=1
    r=[0]*n
    for i in range(n):
        s = p[i] if i < len(p) else 0
        for j in range(1, min(i, len(q)-1)+1):
            s -= q[j]*r[i-j]
        assert q[0]==1
        r[i]=s
    return r
def bk(k):  # coefficients in x of b_k(x^2)
    c=[0]*(2*k+1)
    for j in range(k+1): c[2*j]=comb(k+j,2*j)
    return c
def Bk(k):
    c=[0]*(2*k+2)
    for j in range(k+1): c[2*j]=comb(k+1+j,2*j+1)
    return c
bad=0
for k in range(0,61):
    n=150
    p=bk(k); BB=Bk(k)
    q=[0]*(2*k+3)
    for i,v in enumerate(p): q[i]+=v
    for i,v in enumerate(BB): q[i+1]-=v
    q=q[:2*k+2]
    q2=[(-1)**j*comb(k+1+(j-1)//2, j) for j in range(2*k+2)]
    if q!=q2: bad+=1; print('Q mismatch',k)
    G=series_div(p,q,n)
    A=A_seq(n-1,k)
    if G!=A: bad+=1; print('G mismatch',k)
print('closed form checks bad=',bad)
# Steps 1-2 brute force: E_k = F_k - x ; F_k = E_{k-1}/(1-xE_{k-1})
def every_ok(y):
    n=len(y)
    return all(any(y[i]<=y[j] for j in (i-1,i+1) if 0<=j<n) for i in range(n))
for k in range(0,4):
    L=9 if k<=2 else 8
    F=[sum(1 for y in product(range(k+1),repeat=m) if b_ok(y)) for m in range(L)]
    E=[sum(1 for y in product(range(k+1),repeat=m) if every_ok(y)) for m in range(L)]
    Em1=[sum(1 for y in product(range(k),repeat=m) if every_ok(y)) for m in range(L)] if k>=1 else [1]+[0]*(L-1)
    assert E==[F[m]-(1 if m==1 else 0) for m in range(L)], (k,E,F)
    # F = Em1/(1 - x Em1)
    den=[1]+[-v for v in Em1[:L-1]]
    assert series_div(Em1,den,L)==F,(k,)
print('steps 1-2 ok')
