# Residue-level certificate of R2E2 Theorem R (TP, E, O), own implementation.
from lib4 import polyA, in_box
def tau_of(c,r):
    e=[0]*(len(c)+1)
    for i,v in enumerate(c): e[i]+=v; e[i+1]-=v
    t=[0]*r
    for i,v in enumerate(e): t[i%r]+=v
    return t
def dseries(c,r,L):
    e=[0]*(len(c)+1)
    for i,v in enumerate(c): e[i]+=v; e[i+1]-=v
    d=[0]*L
    for i in range(L): d[i]=(e[i] if i<len(e) else 0)+(d[i-r] if i>=r else 0)
    return d
def fseries(k,r,L):
    # 1/((1-q)^{k-1}(1-q^r))
    f=[1 if i%r==0 else 0 for i in range(L)]
    for _ in range(k-1):
        for i in range(1,L): f[i]+=f[i-1]
    return f
class Inst:
    def __init__(s,r,rho,k=None):
        assert in_box(r,rho)
        s.r=r; s.rho=rho; s.c=polyA(rho); s.sig=len(s.c)-1
        s.tau=tau_of(s.c,r); L=s.sig+3*r+5; s.L=L
        s.d=dseries(s.c,r,L)
        s.k=len(rho) if k is None else k
    def D(s,x): return s.d[x] if x>=0 else 0
    def Q(s,u): return s.D(u)-s.tau[u%s.r]
    def bad(s):
        return [z for z in range(-s.r,s.sig+2) if s.Q(z)<0]
    def TP(s):
        return all(((s.sig+1-2*z)//s.r)%2==0 for z in s.bad())
    def ND(s,K):
        r=s.r
        for x in range(-10*r,K):
            if K-r<=2*x<K and s.Q(K-x)<s.D(x): return False
        return True
    def mu_inf(s,k=None):
        k=s.k if k is None else k; r=s.r
        f=fseries(k,r,s.sig+2*r)
        m=None
        for u in range(-r,s.sig+2*r):
            fu=f[u] if u>=0 else 0
            if fu<s.tau[u%r]: m=u
        return m
    def mu_lim(s):
        r=s.r
        m=max(u for u in range(-r,0) if s.tau[u%r]>0)
        if s.tau[0]>1: m=max(m,0)
        return m
    def EO(s,mu):
        r=s.r; sig=s.sig; fails=[]
        for K in range(2*mu-2*r-2, sig+2-2*r):
            if K>sig+1-2*r: break
            if (K-(sig+1))%(2*r)==0 and K>=2*mu:
                if not s.ND(K): fails.append(('E',K))
            if (K-(sig+1+r))%(2*r)==0 and K>=2*mu+3*r:
                if not s.ND(K): fails.append(('O',K))
        return fails
