# Core exact routines (big ints). Fit box: r<=30, k<=40 (60 if equal), a_i<=100.
def in_box(r,a):
    k=len(a)
    if r>30 or max(a)>100: return False
    if len(set(a))==1: return k<=60
    return k<=40
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
def gseq(A,r,L):
    """g = A/[r]_q as power series, coefficients 0..L-1: g_i = A_i - A_{i-1} + g_{i-r}"""
    g=[0]*L; D=len(A)-1
    for i in range(L):
        v=(A[i] if i<=D else 0)-(A[i-1] if 1<=i<=D+1 else 0)
        if i>=r: v+=g[i-r]
        g[i]=v
    return g
def unimodal_g(g,r,D,b):
    N=D+r*(b-1)
    for i in range(N//2+1):
        if g[i] < (g[i-r*b] if i>=r*b else 0): return False
    return True
def U_set(r,a,bmax=None):
    assert in_box(r,a)
    A=poly_a(a); D=len(A)-1
    F=sum(x//r for x in a)
    if bmax is None:
        bmax = 1+(D+1)//r + 3   # T6 <= 1+floor((D+1)/r)
    L=(D+r*(bmax-1))//2+2
    g=gseq(A,r,L)
    return [b for b in range(1,bmax+1) if unimodal_g(g,r,D,b)]
