# Core utilities for path R2E8 (exactly three middle residues).
# All computations exact (Python ints).
from functools import lru_cache

def poly_a(a):
    c=[1]
    for A in a:
        n=len(c)+A-1; d=[0]*n; s=0
        for t in range(n):
            if t<len(c): s+=c[t]
            if 0<=t-A<len(c): s-=c[t-A]
            d[t]=s
        c=d
    return c

def gseq(a, r, L):
    """coefficients g_0..g_{L-1} of A(q)(1-q)/(1-q^r) as power series"""
    A=poly_a(a)
    d=[0]*(len(A)+1)
    for i,v in enumerate(A):
        d[i]+=v; d[i+1]-=v
    g=[0]*L
    for i in range(L):
        g[i]=(d[i] if i<len(d) else 0)+(g[i-r] if i>=r else 0)
    return g

def stats(r,a):
    D=sum(x-1 for x in a); F=sum(x//r for x in a)
    A=poly_a(a)
    Gam=[sum(A[t::r]) for t in range(r)]
    mu=next(t for t in range(r) if all(Gam[j]>=Gam[j+1] for j in range(t,r-1)))
    T6=1+(D+1-2*mu)//r
    return D,F,tuple(Gam),mu,T6

def Uset(r,a,bmax=None):
    """set of b in [1,bmax] with P unimodal; default bmax = T6+3 (T6 is proved bound)"""
    D,F,Gam,mu,T6=stats(r,a)
    if bmax is None: bmax=max(T6+3, F+3)
    Nmax=D+r*(bmax-1)
    g=gseq(a,r,Nmax//2+2)
    U=[]
    for b in range(1,bmax+1):
        N=D+r*(b-1); rb=r*b; ok=True
        for i in range(1,N//2+1):
            if g[i] < (g[i-rb] if i>=rb else 0): ok=False;break
        if ok: U.append(b)
    return U

def middle(r,a):
    return [x%r for x in a if 2<=x%r<=r-2]
