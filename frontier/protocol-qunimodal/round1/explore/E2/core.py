# Core Fourier/residue objects for P = prod[a_i]_q * [b]_{q^r}
# Box guard: r in 2..6, k<=8, a_i<=12, b<=60
import cmath, itertools
def inbox(r,a,b=1):
    return 2<=r<=6 and 1<=len(a)<=8 and all(1<=x<=12 for x in a) and 1<=b<=60
def polymul(p,q):
    n=[0]*(len(p)+len(q)-1)
    for i,x in enumerate(p):
        if x:
            for j,y in enumerate(q): n[i+j]+=x*y
    return n
def qint(n): return [1]*n
def pcoef(a):
    p=[1]
    for x in a: p=polymul(p,qint(x))
    return p
def Pcoef(r,a,b):
    assert inbox(r,a,b)
    p=pcoef(a); n=[0]*(len(p)+r*(b-1))
    for i,v in enumerate(p):
        for y in range(b): n[i+r*y]+=v
    return n
def unimodal(c):
    i=0;N=len(c)-1
    while i<N and c[i]<=c[i+1]: i+=1
    while i<N and c[i]>=c[i+1]: i+=1
    return i==N
def truth(r,a,b): return unimodal(Pcoef(r,a,b))
# tau: periodic part of p(q)/[r]_q ; depends only on t_i=a_i mod r
def tau(r,a):
    t=[x%r for x in a]
    pi=pcoef([x for x in t]) if all(x>0 for x in t) else None
    if pi is None: return [0]*r
    f=[0]*r
    for m,v in enumerate(pi): f[m%r]+=v
    return [f[m]-f[(m-1)%r] for m in range(r)]
def tau_fourier(r,a):
    # tau_m = (1/r) sum_{j=1}^{r-1} zeta^{-jm} (1-zeta^j) p(zeta^j)
    z=cmath.exp(2j*cmath.pi/r); out=[]
    def pz(w):
        v=1
        for x in a: v*=sum(w**i for i in range(x))
        return v
    vals=[pz(z**j) for j in range(r)]
    for m in range(r):
        s=sum(z**(-j*m)*(1-z**j)*vals[j] for j in range(1,r))/r
        out.append(round(s.real))
    return out
def dseq(r,a,L):
    # coefficients d_0..d_{L-1} of p(q)(1-q)/(1-q^r)
    p=pcoef(a); dp=[0]*(len(p)+1)
    for i,v in enumerate(p): dp[i]+=v; dp[i+1]-=v
    d=[0]*L
    for n in range(L):
        s=0; m=n
        while m>=0:
            if m<len(dp): s+=dp[m]
            m-=r
        d[n]=s
    return d
def criterion(r,a,b):
    # Unimodal iff for all u with K/2<u<=D+1-r : E_u >= d_{K-u}
    D=sum(x-1 for x in a); K=D+1-r*(b+1)
    tt=tau(r,a); L=D+2+r
    d=dseq(r,a,L)
    def dd(v): return d[v] if 0<=v<L else (0 if v<0 else tt[v%r])
    def E(u): return dd(u)-tt[u%r]
    u=K//2+1
    while u<=D+1-r:
        if E(u) < dd(K-u): return False
        u+=1
    return True
