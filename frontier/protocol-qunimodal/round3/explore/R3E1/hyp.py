"""Hypotheses of the conditional cross-pair theorem (proof_crosspair.txt, Theorem 3):
 (H1) sine-comparability of psi, certified by the spectral ratio eps = sum_{2<=j<=r/2} j|beta_j| / beta_1,
      beta_j = (4/r)|R_j| sin(pi j/r), R_j = prod_i sin(pi j a_i/r)/sin(pi j/r);  c = (1-eps)/(1+eps)  (needs eps<1)
 (H2') uniform decay: kappa = r * min_{z >= L-r/2, e(z)>0} ln(e(z)/e(z+1)),  L=(N*+2)r/2
 (K)  c cos(pi/r) (1-e^{-kappa})^2 >= pi e^{-kappa(3/4-1/(2r))}
Also verifies the Fourier formula psi(t) = sum_j beta_j' sin(2 pi j t/r) against exact psi (function fourier_check)."""
import math, mpmath
from fractions import Fraction
from survey2 import psi_of
mpmath.mp.dps=60
def logR(r,a,j):
    s=mpmath.sin(mpmath.pi*j/r); tot=mpmath.mpf(0)
    for x in a:
        v=mpmath.sin(mpmath.pi*j*x/r)
        if abs(v)<mpmath.mpf(10)**-50: return None
        tot+=mpmath.log(abs(v))-mpmath.log(s)
    return tot
def spectral_eps_fast(r,a):
    """double-precision version (used for r>=1000); same quantity as spectral_eps."""
    import numpy as np
    j=np.arange(1,r//2+1)[:,None]; A=np.array(a,dtype=np.float64)[None,:]
    S=np.abs(np.sin(np.pi*((j*A)%(2*r))/r))
    with np.errstate(divide='ignore'):
        lR=np.log(S).sum(axis=1)-len(a)*np.log(np.sin(np.pi*j[:,0]/r))
    if not np.isfinite(lR[0]): return float('inf')
    jj=j[:,0]; m=np.isfinite(lR); m[0]=False
    E=(jj[m]*np.exp(lR[m]-lR[0])*np.sin(np.pi*jj[m]/r)).sum()
    return float(E/np.sin(np.pi/r))
def spectral_eps(r,a):
    if r>=1000: return spectral_eps_fast(r,a)
    l1=logR(r,a,1)
    if l1 is None: return float('inf')
    b1=mpmath.exp(0)*mpmath.sin(mpmath.pi/r)
    E=mpmath.mpf(0)
    for j in range(2,r//2+1):
        lj=logR(r,a,j)
        if lj is None: continue
        E+=j*mpmath.exp(lj-l1)*mpmath.sin(mpmath.pi*j/r)
    return float(E/b1)
def kappa_eff(I,N):
    r=I.r; L2=(N+2)*r  # 2L
    xR=math.floor(((I.D+1)-L2+r)/2)   # z>=L-r/2  <=> x <= (D+1)/2-L+r/2
    xR=min(xR,I.X)
    best=float('inf')
    for x in range(1,xR+1):
        dx,dm=I.delta[x],I.delta[x-1]
        if dx<=0:
            if dm>0: return 0.0     # e(z)=0 < e(z+1): (H2) violated
            continue
        if dm<=0: continue          # e(z+1)=0: ratio 0, fine
        if dm>=dx: return 0.0
        v=math.log(dx)-math.log(dm)
        if v<best: best=v
    return r*best
def K_ok(c,kap,r):
    if c<=0: return False
    if kap==float('inf'): return True
    return c*math.cos(math.pi/r)*(1-math.exp(-kap))**2 >= math.pi*math.exp(-kap*(0.75-1/(2*r)))
def check(I):
    G,ns,N=I.analyze()
    eps=spectral_eps(I.r,I.a); c=(1-eps)/(1+eps) if eps<1 else -1
    kap=kappa_eff(I,N)
    return dict(N=N,eps=eps,c=c,kappa=kap,K=K_ok(c,kap,I.r))
def fourier_check(I):
    """max relative deviation between exact psi(t) and sum_j beta'_j sin(2 pi j t/r) with signed beta'_j."""
    r=I.r; G=I.gaps(2 if I.F%2==0 else 1)
    ps={g:psi_of(I,g) for g in G}; mx=max(abs(v) for v in ps.values()) or 1
    worst=0
    for g in G:
        t=mpmath.mpf(g)/2
        s=mpmath.mpf(0)
        for j in range(1,(r+1)//2+ (1 if r%2==0 else 0)):
            Rj=mpmath.mpf(1)
            for x in I.a: Rj*=mpmath.sin(mpmath.pi*j*x/r)/mpmath.sin(mpmath.pi*j/r)
            w=mpmath.mpf(4)/r if 2*j<r else mpmath.mpf(2)/r
            epsj=(-1)**j if I.F%2==0 else 1
            s+= -w*Rj*mpmath.sin(mpmath.pi*j/r)*epsj*mpmath.sin(2*mpmath.pi*j*t/r)
        worst=max(worst,abs(float(s-ps[g]))/mx)
    return worst
if __name__=="__main__":
    import random
    from winx import InstX
    from box import in_box
    rng=random.Random(5); w=0
    for it in range(60):
        r=rng.randint(3,40); k=rng.randint(2,8); a=sorted(rng.randint(1,200) for _ in range(k))
        if any(x%r==0 for x in a) or not in_box(r,a): continue
        I=InstX(r,a); d=fourier_check(I); w=max(w,d)
    print("max relative deviation of Fourier formula for psi over random small instances:",w)

def check_star(I):
    """Theorem B* (shape-ratio version, no H1): lambda = max_{t in T} psi(t)/t, kappa from (H2);
    (K*) holds iff exists t1 in T: 2 psi(t1) (1-e^{-kappa})^2 >= lambda r e^{-kappa(1-t1/r)}.  Returns (lambda_rel, Kstar)."""
    from fractions import Fraction
    G,ns,N=I.G,I.nstar,I.N; r=I.r
    ps={g:psi_of(I,g) for g in G}
    mx=max(ps.values())
    if mx<=0: return False
    # returns the gap g1=2*t1 of a witness pair, or False
    rel={g:float(Fraction(ps[g],mx)) for g in G}
    lam=max(rel[g]/(g/2) for g in G)
    kap=kappa_eff(I,N)
    if kap==0: return False
    fac=(1-math.exp(-kap))**2 if kap!=float('inf') else 1.0
    for g in G:
        t1=g/2
        rhs=lam*r*(math.exp(-kap*(1-t1/r)) if kap!=float('inf') else 0.0)
        if 2*rel[g]*fac>=rhs and rel[g]>0: return g
    return False
