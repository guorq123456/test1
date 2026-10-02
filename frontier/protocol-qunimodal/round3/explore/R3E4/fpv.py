# Vectorized float search engine for the class-pair criterion. SEARCH ONLY (float); verify exactly elsewhere.
import numpy as np
from fpair import delta_float, tau_float
def fast(r,a,detail=False):
    a=sorted(a)
    if any(x%r==0 for x in a): return None
    D=sum(x-1 for x in a); F=sum(x//r for x in a); X=(D+1)//2
    d,ls=delta_float(a,X)
    tau=tau_float(r,a,ls)
    tmax=np.abs(tau).max(); tau[np.abs(tau)<1e-9*tmax]=0.0
    Cs=np.arange(1,r); Cs=Cs[(Cs-(D+1))%2==0]
    Lmax=(D+1)//r+3
    kk=np.arange(2*Lmax+2)
    Z=(kk//2)[None,:]*2*r+np.where(kk%2==0,Cs[:,None],2*r-Cs[:,None])
    valid=Z<=D+1
    xs=np.where(valid,(D+1-Z)//2,0)
    y=np.where(valid,d[xs],0.0)
    Lc=y.shape[1]
    sgn=np.where(kk%2==0,1.0,-1.0)
    S=y*sgn[None,:]
    R=np.cumsum(S[:,::-1],axis=1)[:,::-1]
    T=R*sgn[None,:]                       # T[:,j]
    T=np.concatenate([T,np.zeros((len(Cs),2))],axis=1)
    y2=np.concatenate([y,np.zeros((len(Cs),2))],axis=1)
    u=((D+1-Cs)//2)%r
    A=np.abs(tau[u])
    par=(F+1)%2
    n0=1 if par==1 else 0
    ns_idx=np.arange(n0,Lc-1,2)            # dangerous n with T[n+1] available
    # tail max for tolerance
    tailmax=np.maximum.accumulate(np.abs(y2)[:,::-1],axis=1)[:,::-1]
    Tn=T[:,ns_idx+1]
    tol=1e-9*np.maximum(np.maximum(A[:,None],np.abs(Tn)),tailmax[:,ns_idx+1])
    neg=(Tn-A[:,None])< -tol
    has=neg.any(axis=1)&(A>0)
    first=np.argmax(neg,axis=1)
    nstar=np.where(has,ns_idx[first],10**9)
    # G_b for b = n+2 over dangerous lattice: G_b = T[b-1]+y[b]-A
    bs=ns_idx+2
    bs_ok=bs<T.shape[1]
    bsv=bs[bs_ok]
    Gv=T[:,bsv-1]+y2[:,np.minimum(bsv,y2.shape[1]-1)]-A[:,None]
    tolG=1e-9*np.maximum(A[:,None],tailmax[:,np.minimum(bsv-1,tailmax.shape[1]-1)])
    gneg=Gv< -tolG
    # only b >= nstar+2 matter (before that G>=0 automatically per Lemma 4.1(d)); compute first negative overall
    gneg_any=gneg.any(axis=1)
    gfirst=np.argmax(gneg,axis=1)
    betaC=np.where(gneg_any, bsv[gfirst]-2, 10**9)
    betaC=np.where(has,betaC,10**9)
    Nst=int(nstar.min()); beta=int(betaC.min())
    out=dict(r=r,k=len(a),D=D,F=F,Nstar=Nst,beta=beta,S2=beta<=Nst+2)
    # continuous levels
    with np.errstate(divide='ignore',invalid='ignore'):
        lA=np.log(A)
        fT=np.log(np.where(Tn>0,Tn,np.nan))-lA[:,None]
        gG=np.log(np.where(Gv+A[:,None]>0,Gv+A[:,None],np.nan))-lA[:,None]
    rows=np.where(has)[0]
    fi=first[rows]
    f1=fT[rows,fi]; f0=np.where(fi>0,fT[rows,np.maximum(fi-1,0)],np.nan)
    v=np.where(fi>0, ns_idx[np.maximum(fi-1,0)]+2*f0/(f0-f1), ns_idx[fi])
    v=np.where(np.isfinite(v),v,ns_idx[fi])
    gi=gfirst[rows]   # first negative G index (b=bsv[gi]); last nonneg is gi-1
    gl=np.where(gi>0,gG[rows,np.maximum(gi-1,0)],np.nan); gn=gG[rows,gi]
    uu=np.where(gi>0, bsv[np.maximum(gi-1,0)]+2*gl/(gl-gn), bsv[gi]-2)
    uu=np.where(np.isfinite(uu),uu,betaC[rows])
    i=int(np.nanargmin(v)); j=int(np.nanargmin(uu))
    out.update(vmin=float(v[i]),umin=float(uu[j]),gap=float(uu[j]-v[i]),Cv=int(Cs[rows[i]]),Cu=int(Cs[rows[j]]))
    rb=rows[i]; n=nstar[rb]
    if n+2<y.shape[1] and y[rb,n]>0 and y[rb,n+2]>0: out['kappa']=float(np.log(y[rb,n]/y[rb,n+2]))
    if detail: out['pairs']=(Cs[rows],nstar[rows],betaC[rows],v,uu)
    return out

def margin(r,a):
    """Exact-in-spirit failure margin: S2 fails iff min over pairs C (A_C>0) of
    min(T_{N*+1}+y_{N*+2}, T_{N*+3}+y_{N*+4}) / |A_C|  >= 1.  Returns (log of that min ratio, info dict)."""
    a=sorted(a)
    x=fast(r,a)
    if x is None or x['Nstar']>=10**8: return None,x
    D=x['D']; F=x['F']; N=x['Nstar']; X=(D+1)//2
    d,ls=delta_float(a,X); tau=tau_float(r,a,ls)
    tmax=np.abs(tau).max(); tau[np.abs(tau)<1e-9*tmax]=0.0
    Cs=np.arange(1,r); Cs=Cs[(Cs-(D+1))%2==0]
    Lmax=(D+1)//r+3; kk=np.arange(2*Lmax+N+10)
    Z=(kk//2)[None,:]*2*r+np.where(kk%2==0,Cs[:,None],2*r-Cs[:,None])
    valid=Z<=D+1
    y=np.where(valid,d[np.where(valid,(D+1-Z)//2,0)],0.0)
    sgn=np.where(kk%2==0,1.0,-1.0)
    T=np.cumsum((y*sgn)[:,::-1],axis=1)[:,::-1]*sgn[None,:]
    A=np.abs(tau[((D+1-Cs)//2)%r])
    m=A>0
    H2=T[:,N+1]+y[:,N+2]; H4=T[:,N+3]+y[:,N+4]
    H=np.minimum(H2,H4)
    with np.errstate(divide='ignore',invalid='ignore'):
        lr=np.where(H>0,np.log(np.maximum(H,1e-300)/np.where(m,A,1)),-50.0)
    lr=np.where(m,np.maximum(lr,-50.0),np.inf)
    i=int(np.argmin(lr))
    x['margin']=float(lr[i]); x['Cworst']=int(Cs[i])
    return float(lr[i]),x
