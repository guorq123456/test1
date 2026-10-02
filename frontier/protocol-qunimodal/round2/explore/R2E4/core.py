# Core: compute U = {b : P unimodal} via d-criterion, plus S2 test and near-miss margins.
# P_i - P_{i-1} = d_i - d_{i-rb}, d = coeffs of A(q)(1-q)/(1-q^r); P symmetric =>
# unimodal iff d_i >= d_{i-rb} for rb <= i <= floor(N/2), N = D + r(b-1).
import numpy as np
from math import prod

def in_box(r,a):
    k=len(a)
    if r<2 or r>30 or any(x<1 or x>100 for x in a): return False
    if k>40 and not (k<=60 and len(set(a))==1): return False
    return True

def poly_a(a):
    c=[1]
    for A in a:
        n=len(c)+A-1; d=[0]*n; s=0; L=len(c)
        for t in range(n):
            if t<L: s+=c[t]
            if 0<=t-A<L: s-=c[t-A]
            d[t]=s
        c=d
    return c

def dseq(A,r,length):
    D=len(A)-1
    d=[0]*length
    for i in range(length):
        Ai = A[i] if i<=D else 0
        Aim = A[i-1] if 1<=i<=D+1 else 0
        d[i]=(d[i-r] if i>=r else 0)+Ai-Aim
    return d

def F_D(r,a): return sum(x//r for x in a), sum(x-1 for x in a)

def T6(r,a,A=None):
    if A is None: A=poly_a(a)
    D=len(A)-1
    G=[0]*r
    for i,v in enumerate(A): G[i%r]+=v
    mu=r-1
    for t in range(r-1,-1,-1):
        if all(G[j]>=G[j+1] for j in range(t,r-1)): mu=t
        else: break
    return 1+(D+1-2*mu)//r

def margins(r,a,bmax,A=None,big=None):
    """return dict b-> (ok, margin) for b=1..bmax; margin = min_i (d_i-d_{i-rb}) / maxd (float)."""
    assert in_box(r,a)
    if A is None: A=poly_a(a)
    D=len(A)-1
    Nmax=D+r*(bmax-1)
    L=Nmax//2+1
    d=dseq(A,r,L)
    mx=max(abs(x) for x in d) or 1
    useint = mx < 2**62
    darr=np.array(d,dtype=np.int64 if useint else object)
    out={}
    for b in range(1,bmax+1):
        N=D+r*(b-1); h=N//2
        lo=r*b
        m1=darr[1:min(lo,h+1)].min() if min(lo,h+1)>1 else 0
        if lo<=h:
            diff=darr[lo:h+1]-darr[0:h+1-lo]
            mn=min(diff.min(),m1)
        else: mn=m1
        if h==0: mn=0
        out[b]=(bool(mn>=0), float(mn)/float(mx))
    return out

def Uset(r,a,extra=2):
    A=poly_a(a); t6=T6(r,a,A)
    bmax=max(t6+extra,1)
    m=margins(r,a,bmax,A)
    return sorted(b for b,(ok,_) in m.items() if ok), t6, m

def s2_check(r,a,extra=2):
    """returns (holds, U, info). Only for r dividing no a_i."""
    U,t6,m=Uset(r,a,extra)
    F,D=F_D(r,a)
    Bs=max(U)
    Us=set(U)
    full=set(range(1,Bs+1))
    if Us==full: shape='interval'
    elif Us==full-{Bs-1}: shape='gap'
    else: shape='bad'
    parity_ok = ((Bs-1-F)%2==0)
    holds = shape!='bad' and parity_ok
    return holds, U, dict(F=F,D=D,T6=t6,Bstar=Bs,shape=shape,parity_ok=parity_ok,beyond_T6=any(b>t6 for b in U),m=m)

def closeness(m,F):
    """max over potential violations of min(margin(b in U), -margin(b' not in U)); >0 means violation."""
    bs=sorted(m)
    mg={b:m[b][1] for b in bs}
    best=-float('inf'); arg=None
    for b in bs:
        # (ii): b in U, b'<=b-2 not in U
        for bp in bs:
            if bp<=b-2:
                v=min(mg[b],-mg[bp])
                if v>best: best,arg=v,('ii',b,bp)
        # (i): b in U, b-1-F odd, b+1 not in U
        if (b-1-F)%2==1 and b+1 in mg:
            v=min(mg[b],-mg[b+1])
            if v>best: best,arg=v,('i',b,b+1)
    return best,arg

def nmiddle(r,a): return sum(1 for x in a if 2<=x%r<=r-2)

def margins_range(r,A,blo,bhi):
    D=len(A)-1
    Nmax=D+r*(bhi-1); L=Nmax//2+1
    d=dseq(A,r,L)
    mx=max(abs(x) for x in d) or 1
    useint = mx < 2**62
    darr=np.array(d,dtype=np.int64 if useint else object)
    out={}
    for b in range(blo,bhi+1):
        N=D+r*(b-1); h=N//2; lo=r*b
        m1=darr[1:min(lo,h+1)].min() if min(lo,h+1)>1 else 0
        if lo<=h:
            diff=darr[lo:h+1]-darr[0:h+1-lo]
            mn=min(diff.min(),m1)
        else: mn=m1
        if h==0: mn=0
        out[b]=(bool(mn>=0), float(mn)/float(mx))
    return out

def analyze(r,a,A=None,extra=2):
    """Full S2 analysis for r dividing no a_i. b<=1+F taken as unimodal (Thm T1)."""
    assert in_box(r,a) and all(x%r for x in a)
    if A is None: A=poly_a(a)
    F,D=F_D(r,a); t6=T6(r,a,A)
    blo=max(1,F); bhi=max(t6+extra,F+2)
    m=margins_range(r,A,blo,bhi)
    for b in range(1,blo): m[b]=(True,float('inf'))
    U=sorted(b for b in m if m[b][0])
    Bs=max(U); Us=set(U); full=set(range(1,Bs+1))
    shape='interval' if Us==full else ('gap' if Us==full-{Bs-1} else 'bad')
    par=((Bs-1-F)%2==0)
    cl,arg=closeness({b:m[b] for b in m if b>=blo},F)
    return dict(holds=(shape!='bad' and par),shape=shape,parity_ok=par,U_hi=[b for b in U if b>=blo],
                F=F,D=D,T6=t6,Bstar=Bs,beyondT6=Bs>t6,close=cl,closearg=arg)
