# Certificate C1(r=6), refined: as analytic_cert6.py, but for (p,s) not covered with the k-only bounds,
# recompute with the refined ratio upper bound from Lemma 9 (operator M>=0):
#   (j+1) >= rho_{j+1} * [ (k-2j) + c1*rho_j + c2*rho_j*rho_{j-1} ],  c1=p+3s+2-2j, c2=p+2s+2-j
# so rho_{j+1} <= (j+1)/den_lb whenever den_lb>0 (den_lb uses rlo for positive coefficients and rhi for negative).
import sys
from fractions import Fraction as Fr
from analytic_cert6 import V6, tri, SC
from analytic_cert2 import make
from math import comb
r=6
def make_ps(k,p,s,xmax):
    base_rhi=[Fr(0)]+[ (min(Fr(1),Fr(j,k-j+1)) if j<=k else Fr(1)) for j in range(1,xmax+2)]
    rlo=[Fr(0)]+[Fr(j,j+k-1) for j in range(1,xmax+2)]
    rhi=base_rhi[:]
    for j in range(1,xmax+1):   # bound rho_{j+1}
        c0=k-2*j; c1=p+3*s+2-2*j; c2=p+2*s+2-j
        t1 = c1*(rlo[j] if c1>=0 else rhi[j])
        pr_lo=rlo[j]*rlo[j-1]; pr_hi=rhi[j]*rhi[j-1]
        t2 = c2*(pr_lo if c2>=0 else pr_hi)
        den=c0+t1+t2
        if den>0:
            b=Fr(j+1)/den
            if b<rhi[j+1]: rhi[j+1]=b
    def RHI(j): return rhi[j] if j>=1 else Fr(0)
    def RLO(j): return rlo[j] if j>=1 else Fr(0)
    def C(j): return comb(k,j) if 0<=j<=k else 0
    def pihi(x,g):
        q=Fr(1)
        for i in range(g):
            if x-i<=0: return Fr(0)
            q*=RHI(x-i)
        return q
    def pilo(x,g):
        q=Fr(1)
        for i in range(g):
            if x-i<=0: return Fr(0)
            q*=RLO(x-i)
        return q
    def kappa_ok(j): return 1<=j<=k and 2*j<=k+3
    def kappa(j): return Fr(C(j)-2*C(j-1)+(C(j-2) if j>=2 else 0),C(j))
    def Elb(x,g):
        if x-g<0: e1=1-RHI(x)
        else: e1=1-RHI(x)-pihi(x,g)*(1-RLO(x-g))
        e2=None
        if x-g>=0 and all(kappa_ok(x-i) for i in range(g)):
            sm=Fr(0)
            for i in range(g):
                kp=kappa(x-i); sm+=kp*(pilo(x,i) if kp>=0 else pihi(x,i))
            e2=sm
        return e1 if e2 is None else max(e1,e2)
    def Rub(x,g):
        j=x-g-r
        if j<0: return Fr(0)
        return pihi(x,g+r)*(1-RLO(j))
    return Elb,Rub
def Bps(p,s,X):
    c=tri(s,X)
    for _ in range(p):
        c=[c[x]+(c[x-1] if x>=1 else 0) for x in range(X+1)]
    return c
def covered(k,p,s,Elb,Rub,xmax,B):
    V=V6(p,s)
    for g in range(1,r):
        E=[Elb(x,g) for x in range(xmax+1)]
        fails=[x for x in range(g+r,xmax+1) if not (E[x]>=Rub(x,g))]
        if not fails: continue
        xs=fails[0]
        for x0 in range(xs,xs+r):
            if x0>xmax: return False
            T=Fr(0); t=x0
            while t>=0:
                if E[t]>0: T+=B[t]*E[t]
                t-=r
            if T<V: return False
    return True
if __name__=='__main__':
    from analytic_cert6 import check
    lo,hi=int(sys.argv[1]),int(sys.argv[2])
    res={}
    for k in range(lo,hi+1):
        bad=check(k); xmax=k+3*r+8
        still=[]
        for (p,s) in sorted(set((b[0],b[1]) for b in bad)):
            Elb,Rub=make_ps(k,p,s,xmax)
            if not covered(k,p,s,Elb,Rub,xmax,Bps(p,s,xmax)): still.append((p,s))
        res[k]=(len(set((b[0],b[1]) for b in bad)),still)
        print(k,"k-only-uncovered pairs",res[k][0],"still uncovered",still[:12],flush=True)
