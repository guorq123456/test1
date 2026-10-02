# Variants of the asymptotic model for chain tops (e_odd, e_even) given residues s (k=len(s)).
#  A: linearised closed form (rule_asym.asym_tops)
#  B: same dominant-mode tau, but ln B_m via exact lgamma (no Taylor linearisation), geometric w-ratio rho=e^lambda
#  C: semi-exact: exact w (big ints), tau replaced by its dominant Fourier mode (float);  chain tops by direct scan
import math, gmpy2
from rule_asym import asym_tops, modes, _Hinv
from uinf import Wn, window
def _dom(r,s):
    ms=modes(r,s); Lk=max(v for v,j,sg in ms)
    return Lk,[(v,j,sg) for v,j,sg in ms if v>Lk-1e-9]
def gdom(r,dom,par,u):
    g=0.0
    for v,j,sg in dom:
        g+=(2.0/r)*math.sin(math.pi*j/r)*sg*(-((-1)**(j*(par+1))))*math.sin(2*math.pi*j*u/r)
    return g
def lnB(x,k): return math.lgamma(x+k-1)-math.lgamma(k-1)-math.lgamma(x+1)
def tops_B(r,s):
    k=len(s); S1=sum(x-1 for x in s); Lk,dom=_dom(r,s)
    theta=_Hinv(Lk/k); lam=math.log(1+1/theta)
    X={}
    for par in (1,0):
        Dpar=(S1+1-r*(par+1))%2
        us=[u-0.5 for u in range(1,r+1)] if Dpar else [float(u) for u in range(1,r+1)]
        nu=-1e18
        for u in us:
            g=gdom(r,dom,par,u)
            if g<=1e-15: continue
            rhs=Lk+math.log(g)
            def Fn(n):
                if n+u<=-1+1e-12: return -1e18
                return lnB(n+u,k)+math.log((1-math.exp(-2*lam*u))/(1-math.exp(-lam*r)))-rhs
            lo,hi=-u-1+1e-9,theta*k+10
            while Fn(hi)<0: hi*=2
            if Fn(lo)>=0: nn=lo
            else:
                for _ in range(100):
                    mid=(lo+hi)/2
                    if Fn(mid)>=0: hi=mid
                    else: lo=mid
                nn=hi
            nu=max(nu,nn)
        X[par]=(S1+1-r-2*nu)/r if nu>-1e17 else float('inf')
    Xo,Xe=X[1],X[0]
    return Xo,Xe,max(1,2*math.floor((Xo-1)/2)+1),max(0,2*math.floor(Xe/2))
def tops_C(r,s):
    k=len(s); S1=sum(x-1 for x in s); K0=S1+1; Lk,dom=_dom(r,s)
    amp=math.exp(Lk)
    T=1+(K0)//r+2
    res={}
    for par in (1,0):
        e=T if T%2==par else T-1
        top=par if par==1 else 0
        while e>=2:
            D=K0-r*(e+1); ok=True
            for m in window(D,r):
                u=m-D/2
                t=amp*gdom(r,dom,par,u)
                if t<=0: continue
                d=Wn(m,r,k)-Wn(D-m,r,k)
                if d<=0 or float(gmpy2.log(gmpy2.mpfr(d,100)))<math.log(t): ok=False;break
            if ok: top=e;break
            e-=2
        res[par]=top
    return None,None,max(1,res[1]),res[0]
