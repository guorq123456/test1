# Float (search-only) implementation of the class-pair criterion (synthesis r2, Thm 3.1/4.2).
# analyze(r,a) -> dict with N*, beta, per-pair continuous levels, gap metric.
import numpy as np
def delta_float(a, X):
    """delta = (1-q)prod[a_i], coefficients 0..X, as (float array, log scale) with true = arr*exp(ls)."""
    a=sorted(a); a1=a[-1]; rest=a[:-1]
    B=np.zeros(X+1); B[0]=1.0; ls=0.0; L=1
    for ai in rest:
        if ai<=1: continue
        nL=min(L+ai-1, X+1)
        S=np.concatenate(([0.0],np.cumsum(B[:nL])))
        idx=np.arange(nL)
        lo=np.maximum(idx-ai+1,0)
        B=np.zeros(X+1); B[:nL]=S[idx+1]-S[lo]
        L=nL
        m=B[:L].max(); B/=m; ls+=np.log(m)
    d=B.copy()
    if a1<=X: d[a1:]-=B[:X+1-a1]
    return d, ls
def tau_float(r,a,ls):
    j=np.arange(r); z=np.exp(2j*np.pi*j/r)
    logW=np.zeros(r); ph=np.ones(r,dtype=complex)
    for ai in a:
        num=1-z**ai; den=1-z
        q=np.ones(r,dtype=complex)*ai
        q[1:]=num[1:]/den[1:]
        logW+=np.log(np.abs(q)+1e-300); ph*=q/np.maximum(np.abs(q),1e-300)
    W=np.zeros(r,dtype=complex)
    W[1:]=np.exp(logW[1:]-ls)*ph[1:]*(1-z[1:])
    return np.fft.fft(W).real/r
def analyze(r,a,want_pairs=False):
    a=sorted(a); k=len(a)
    if any(x%r==0 for x in a): return None
    D=sum(x-1 for x in a); F=sum(x//r for x in a)
    X=(D+1)//2
    d,ls=delta_float(a,X)
    tau=tau_float(r,a,ls)
    tmax=np.abs(tau).max(); tau[np.abs(tau)<1e-9*tmax]=0.0
    par=(F+1)%2   # dangerous parity
    Nst=10**9; beta=10**9; res=[]
    for C in range(1,r):
        if (C-(D+1))%2: continue
        Zs=[]; kk=0
        while True:
            Z=(kk//2)*2*r+(C if kk%2==0 else 2*r-C)
            if Z>D+1: break
            Zs.append(Z); kk+=1
        Ln=len(Zs)
        xs=[(D+1-Z)//2 for Z in Zs]
        y=np.array([d[x] for x in xs]+[0.0]*8)
        L=len(y)
        u=((D+1-C)//2)%r
        Ainf=abs(tau[u])
        # tails T_j = sum_{t>=0} (-1)^t y_{j+t}
        T=np.zeros(L+2)
        for j in range(L-1,-1,-1): T[j]=y[j]-T[j+1]
        # dangerous n: n%2==par, n>=-1 ; a_n = T_{n+1}-Ainf
        ns=None
        n=1 if par==1 else 0
        while n+1<L:
            if T[n+1]-Ainf< -1e-9*max(Ainf,abs(T[n+1]),np.abs(y[n+1:]).max(),1e-300): ns=n; break
            n+=2
        if ns is None: continue
        # beta_C
        b=ns+2
        while b<L:
            G=T[b-1]-Ainf+y[b]
            if G< -1e-9*max(Ainf,np.abs(y[b-1:]).max(),1e-300): break
            b+=2
        bC=b-2
        Nst=min(Nst,ns); beta=min(beta,bC)
        if want_pairs:
            # continuous crossing levels
            def lev(seq_fn, nfirst):
                # find index where log(seq) crosses log(Ainf), seq evaluated on same-parity indices
                pass
            res.append((C,ns,bC,Ainf,y[:Ln].copy(),T[:L].copy()))
    out=dict(r=r,k=k,D=D,F=F,Nstar=Nst,beta=beta,S2=(beta<=Nst+2))
    if want_pairs: out['pairs']=res
    return out

def levels(r,a):
    """Per-pair continuous crossing levels. Returns summary dict with
    Nstar, beta, vmin (continuous n*), umin (continuous beta), gap=umin-vmin, kappa at binding pair."""
    res=analyze(r,a,want_pairs=True)
    if res is None: return None
    vs=[];us=[];info=[]
    par=(res['F']+1)%2
    for (C,ns,bC,Ainf,y,T) in res['pairs']:
        if Ainf<=0: continue
        lA=np.log(Ainf)
        def f(n):
            t=T[n+1] if n+1<len(T) else 0.0
            return np.log(t)-lA if t>0 else -np.inf
        n0=1 if par==1 else 0
        if ns-2>=n0:
            f0=f(ns-2); f1=f(ns)
            v=ns-2+2*f0/(f0-f1) if np.isfinite(f1) else ns-2+2*0.999
        else: v=float(ns)
        def g(b):
            t=(T[b-1] if b-1<len(T) else 0.0)+(y[b] if b<len(y) else 0.0)
            return np.log(t)-lA if t>0 else -np.inf
        g0=g(bC); g1=g(bC+2)
        if np.isfinite(g0) and np.isfinite(g1) and g0>g1: u=bC+2*g0/(g0-g1)
        else: u=float(bC)
        vs.append(v);us.append(u);info.append((C,ns,bC,v,u))
    i=int(np.argmin(vs)); j=int(np.argmin(us))
    res['vmin']=vs[i]; res['umin']=us[j]; res['gap']=us[j]-vs[i]
    res['argv']=info[i]; res['argu']=info[j]
    # kappa near binding pair crossing
    for (C,ns,bC,Ainf,y,T) in res['pairs']:
        if C==info[i][0]:
            n=ns
            if n+2<len(y) and y[n]>0 and y[n+2]>0: res['kappa']=float(np.log(y[n]/y[n+2]))
    res['info']=info
    del res['pairs']
    return res
