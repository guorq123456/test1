# Verify identity Delta c_n = e(n-r(b-1)) - e(D+1-n) for all n, with
# e(y) = Gamma_{y mod r} - H(y-r), H(n)=[q^n] A(q)/[r]_q (0 for n<0), Gamma_s = class sums of A mod r.
# Also verify symmetry e(y) = e(D+1+r-y).
import random
from scond import Apoly
from load import load
def Hser(A,r,nmax):
    # A(q)*(1-q)/(1-q^r)
    f=[(A[j] if j<len(A) else 0)-(A[j-1] if 0<=j-1<len(A) else 0) for j in range(nmax+1)]
    H=[0]*(nmax+1)
    for n in range(nmax+1): H[n]=f[n]+(H[n-r] if n>=r else 0)
    return H
def make_e(a,r,ymax):
    A=Apoly(a); G=[sum(A[s::r]) for s in range(r)]
    H=Hser(A,r,ymax+r+5)
    return (lambda y: G[y%r]-(H[y-r] if y-r>=0 else 0)), A
random.seed(5); bad=0; badsym=0; tot=0
for r in range(2,7):
    D_=load(r)
    for a,mask in random.sample(D_,60):
        D=sum(x-1 for x in a)
        e,A=make_e(a,r,D+r*62+10)
        for y in range(-3*r,D+2*r): 
            if e(y)!=e(D+1+r-y): badsym+=1
        for b in range(1,25):
            P=[0]*(D+r*(b-1)+1)
            for i,v in enumerate(A):
                for t in range(b): P[i+r*t]+=v
            N=len(P)-1
            for n in range(-2,N+3):
                dc=(P[n] if 0<=n<=N else 0)-(P[n-1] if 0<=n-1<=N else 0)
                tot+=1
                if dc!=e(n-r*(b-1))-e(D+1-n): bad+=1
print("identity checks",tot,"failures",bad,"symmetry failures",badsym)
