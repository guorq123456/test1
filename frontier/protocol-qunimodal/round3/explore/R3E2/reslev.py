# Residue-level quantities for the TP/E/O certificate (T10 / R2E2), exact integers.
import itertools
def inbox(r,a):
    """fit box check for an instance (r, a) (a = list of parts)."""
    if r>=1000: return True
    if r>120 or len(a)>140 or max(a)>400: return False
    k=len(a); res=[x%r for x in a]
    mid=[t for t in res if 2<=t<=r-2]
    if k>=20 and len(mid) in (4,5) and all(t in (1,r-1) for t in res if not (2<=t<=r-2)): return False
    if k>=55 and sum(1 for t in res if t==r-1)>50: return False
    if k>=60 and len(set(a))==2 and all(2<=x%r<=r-2 for x in set(a)): return False
    return True

def polyA(a):
    c=[1]
    for A in a:
        if A<=1: continue
        n=[0]*(len(c)+A-1)
        # prefix sums
        s=0; pre=[0]
        for v in c: s+=v; pre.append(s)
        L=len(c)
        for j in range(len(n)):
            hi=min(j,L-1); lo=max(0,j-A+1)
            n[j]=pre[hi+1]-pre[lo] if hi>=lo else 0
        c=n
    return c

class Res:
    def __init__(self,r,a):
        self.r=r; self.a=sorted(a); self.k=len(a)
        A=polyA(a); self.A=A; D=len(A)-1; self.D=D
        e=[0]*(D+2)
        for y in range(D+2):
            e[y]=(A[y] if y<=D else 0)-(A[y-1] if y>=1 else 0)
        self.e=e
        tau=[0]*r
        for y,v in enumerate(e): tau[y%r]+=v
        self.tau=tau
        self.F=sum(x//r for x in a)
    def dd(self,y):
        # d_y = sum_{m>=0} e_{y-rm}
        if y<0: return 0
        r=self.r; e=self.e
        if y>=len(e):
            return self.tau[y%r]
        s=0
        while y>=0:
            s+=e[y]; y-=r
        return s
    def Q(self,u):
        return self.dd(u)-self.tau[u%self.r]
    def ND(self,K):
        r=self.r
        lo=-((r-K)//2)  # ceil((K-r)/2)
        x=lo
        while 2*x<K:
            if self.Q(K-x)<self.dd(x): return False
            x+=1
        return True
    def unimodal(self,b):
        # Lemma 4 / Thm A: d_n >= d_{n-rb} for 1<=n<=floor(N/2), N=D+r(b-1)
        r=self.r; N=self.D+r*(b-1)
        for n in range(1,N//2+1):
            if self.dd(n)<self.dd(n-r*b): return False
        return True

def fcoef(r,k,umax):
    # coefficients of 1/((1-q)^{k-1}(1-q^r)) for u in [0,umax]
    f=[1 if u%r==0 else 0 for u in range(umax+1)]
    for _ in range(k-1):
        s=0
        for u in range(umax+1):
            s+=f[u]; f[u]=s
    return f

def mustar_inf(r,k,tau):
    T=max(tau)
    if k==1:
        # f_u in {0,1}; Bad_inf within [-r,-1] unless tau_u>1 somewhere at u>=0 (then infinite)
        cand=[u for u in range(-r,0) if tau[u%r]>0]
        if T>1: raise ValueError('k=1 with tau>1')
        return max(cand)
    umax=r
    while True:
        f=fcoef(r,k,umax)
        if f[umax]>T and f[umax-r]>T: break
        umax*=2
    best=None
    for u in range(-r,umax+1):
        fu=f[u] if u>=0 else 0
        if fu<tau[u%r]: best=u
    return best

def mu_neg(r,tau):
    return max(u for u in range(-r,0) if tau[u%r]>0)

def certificate(r,rho,strong=False):
    """rho: residue multiset (parts in [1,r-1]); returns dict with TP,E,O flags."""
    R=Res(r,rho); sigma=R.D; k=len(rho)
    mi = mu_neg(r,R.tau) if strong else mustar_inf(r,k,R.tau)
    # TP
    TP=True
    for z in range(-r,sigma+2):
        if R.Q(z)<0 and ((sigma+1-2*z)//r)%2!=0: TP=False;break
    E=True;O=True;Efail=[];Ofail=[]
    for j in range(0,10**9):
        K=sigma+1-r*(j+2)
        if K<2*mi: break
        if j%2==0:
            if not R.ND(K): E=False;Efail.append(j)
        else:
            if K>=2*mi+3*r and not R.ND(K): O=False;Ofail.append(j)
    return dict(TP=TP,E=E,O=O,mu=mi,sigma=sigma,Efail=Efail,Ofail=Ofail)
