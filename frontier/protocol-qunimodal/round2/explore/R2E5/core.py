# Core exact computations for the all-equal family [a]_q^k [b]_{q^r}.
# Uses Thm A criterion (g = coeffs of A(q)/[r]_q, unimodal iff g_i >= g_{i-rb} for 0<=i<=floor(N/2)),
# validated against /tmp/claude-0/qu/tools/gt_big.py in validate.py.
import sys
sys.path.insert(0,'/tmp/claude-0/qu/tools')
from gt_big import poly_a

def fitbox(r,a):
    k=len(a)
    if r>30 or max(a)>100: return False
    if all(x==a[0] for x in a): return k<=60
    return k<=40

def gseries(A,r,L):
    # g = A(q)*(1-q)/(1-q^r) up to index L (inclusive)
    D=len(A)-1
    g=[0]*(L+1)
    for i in range(L+1):
        v=(A[i] if i<=D else 0)-(A[i-1] if 1<=i<=D+1 else 0)
        if i>=r: v+=g[i-r]
        g[i]=v
    return g

def mu_of(A,r):
    G=[0]*r
    for j,c in enumerate(A): G[j%r]+=c
    for t in range(r):
        if all(G[u]>=G[u+1] for u in range(t,r-1)): return t
    return r-1

def Uset(r,a,extra=3):
    """returns (U as sorted list within [1,T6+extra], F, T6)"""
    assert fitbox(r,a)
    A=poly_a(a); D=len(A)-1
    F=sum(x//r for x in a)
    mu=mu_of(A,r)
    T6=1+(D+1-2*mu)//r
    bmax=T6+extra
    Nmax=D+r*(bmax-1)
    g=gseries(A,r,Nmax//2+1)
    U=[]
    for b in range(1,bmax+1):
        N=D+r*(b-1); ok=True
        rb=r*b
        for i in range(0,N//2+1):
            gi=g[i]; gj=g[i-rb] if i>=rb else 0
            if gi<gj: ok=False;break
        if ok: U.append(b)
    return U,F,T6

def is_uni(r,a,b):
    A=poly_a(a); D=len(A)-1; N=D+r*(b-1)
    g=gseries(A,r,N//2+1); rb=r*b
    for i in range(N//2+1):
        if g[i] < (g[i-rb] if i>=rb else 0): return False
    return True

def Uset_fast(r,a,extra=2):
    """Like Uset but uses T1 (b<=1+F unimodal, established) and tests only b in [F+2, T6+extra]."""
    assert fitbox(r,a)
    A=poly_a(a); D=len(A)-1
    F=sum(x//r for x in a)
    mu=mu_of(A,r)
    T6=1+(D+1-2*mu)//r
    bmax=T6+extra
    Nmax=D+r*(bmax-1)
    g=gseries(A,r,Nmax//2+1)
    U=list(range(1,min(F+1,bmax)+1))
    for b in range(F+2,bmax+1):
        N=D+r*(b-1); ok=True
        rb=r*b
        for i in range(N//2,-1,-1):
            gi=g[i]; gj=g[i-rb] if i>=rb else 0
            if gi<gj: ok=False;break
        if ok: U.append(b)
    return U,F,T6
