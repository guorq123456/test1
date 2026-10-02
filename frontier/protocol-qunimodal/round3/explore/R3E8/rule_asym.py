# Zero-parameter asymptotic closed form for U in the large-part regime (path R3E8).
# predict(r,a,b) -> bool ; domain(r,a) -> bool.  See description in candidates / final report.
import math
def _H(t): return (1+t)*math.log(1+t)-t*math.log(t)
def _Hinv(L):
    lo,hi=1e-300,1.0
    while _H(hi)<L: hi*=2
    for _ in range(200):
        mid=(lo+hi)/2
        if _H(mid)<L: lo=mid
        else: hi=mid
    return (lo+hi)/2
def modes(r,s):
    out=[]
    for j in range(1,r):
        v=0.0; sg=1; ok=True
        den=math.sin(math.pi*j/r)
        for x in s:
            q=math.sin(math.pi*j*x/r)/den
            if abs(q)<1e-12: ok=False;break
            v+=math.log(abs(q)); sg*= (1 if q>0 else -1)
        if ok: out.append((v,j,sg))
    return out
def asym_tops(r,s,variant=0):
    """returns (X_odd, X_even, e_odd, e_even) from the closed form."""
    k=len(s); S1=sum(x-1 for x in s)
    ms=modes(r,s)
    Lk=max(v for v,j,sg in ms)
    dom=[(v,j,sg) for v,j,sg in ms if v>Lk-1e-9]
    theta=_Hinv(Lk/k); lam=math.log(1+1/theta)
    c0=-1.5*math.log(1+theta)-0.5*math.log(theta)-0.5*math.log(2*math.pi)
    res={}
    for par in (1,0):
        Dpar=(S1+1-r*(par+1))%2       # parity of Delta_e for e of this parity
        us=[u+(0.5 if Dpar else 0.0) for u in range(1,r+1)] if not Dpar else [u-0.5 for u in range(1,r+1)]
        best=None
        for u in us:
            # normalised dominant-mode tau at window offset u:  sum over dominant j of (2/r) sin(pi j/r) * sg * (-(-1)^{j(e+1)}) sin(2 pi j u/r)
            g=0.0
            for v,j,sg in dom:
                g+= (2.0/r)*math.sin(math.pi*j/r)*sg*(-((-1)**(j*(par+1))))*math.sin(2*math.pi*j*u/r)
            if g<=1e-15: continue
            val=math.log(g)-lam*u-math.log((1-math.exp(-2*lam*u))/(1-math.exp(-lam*r)))
            if best is None or val>best: best=val
        if best is None:
            res[par]=float('inf'); continue
        nu=theta*k+math.log(k)/(2*lam)+(best-c0)/lam
        res[par]=(S1+1-r-2*nu)/r
    Xo,Xe=res[1],res[0]
    eo=max(1, 2*math.floor((Xo-1)/2)+1)
    ee=max(0, 2*math.floor(Xe/2))
    return Xo,Xe,eo,ee
def domain(r,a):
    s=[x%r for x in a]
    if any(x==0 for x in s): return False
    k=len(a)
    if k<3: return False
    if not any(2<=x<=r-2 for x in s): return False
    S=sum(s); L0=max(1,(S-k+3-r)//2)
    return min(a)>=L0
def predict(r,a,b):
    s=[x%r for x in a]
    if any(x==0 for x in s): return True
    F=sum(x//r for x in a)
    if b<=F+1: return True
    Xo,Xe,eo,ee=asym_tops(r,s)
    e=b-F
    if e%2==1: return e<=eo
    return e<=ee
