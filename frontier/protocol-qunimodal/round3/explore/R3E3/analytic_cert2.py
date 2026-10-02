# Certificate C1'(r): analytic coverage using
#   rho_j <= min(1, j/(k'-j+1))  (Lemma B),  rho_j >= j/(j+k'-1)  (Lemma B'),
#   alpha_x >= C(k',x) (domination),
#   D2 alpha_j >= alpha_j * kappa_j, kappa_j = D2 C(k',j)/C(k',j), valid for 1<=j<=(k'+3)/2  (Lemma S, beta convex)
# x is COVERED if x-g-r<0, or Elb>=Rub (L' holds), or Tlb>=V (x cannot be x_{n*+1}).
# V(r,k') from vbound.vmax, or for r=4 the exact 2^floor((k'-1)/2).
import sys
from fractions import Fraction as Fr
from math import comb
from vbound import vmax
def Vbound(r,k):
    return 2**((k-1)//2) if r==4 else vmax(r,k)
def make(k):
    def C(j): return comb(k,j) if 0<=j<=k else 0
    def rhi(j):
        if j<=0: return Fr(0)
        return min(Fr(1),Fr(j,k-j+1)) if j<=k else Fr(1)
    def rlo(j):
        if j<=0: return Fr(0)
        return Fr(j,j+k-1)
    def pihi(x,g):
        p=Fr(1)
        for i in range(g):
            if x-i<=0: return Fr(0)
            p*=rhi(x-i)
        return p
    def pilo(x,g):
        p=Fr(1)
        for i in range(g):
            if x-i<=0: return Fr(0)
            p*=rlo(x-i)
        return p
    def kappa_ok(j): return 1<=j<=k and 2*j<=k+3
    def kappa(j): return Fr(C(j)-2*C(j-1)+(C(j-2) if j>=2 else 0),C(j))
    def Elb(x,g):
        # bound 1: first-order
        if x-g<0: e1=1-rhi(x)
        else: e1=1-rhi(x)-pihi(x,g)*(1-rlo(x-g))
        # bound 2: sum of second differences D2 alpha_{x-i}, i<g  (only if all positions valid)
        e2=None
        if x-g>=0 and all(kappa_ok(x-i) for i in range(g) if x-i>=1):
            s=Fr(0)
            for i in range(g):
                j=x-i
                assert j>=1
                kp=kappa(j)
                s+= kp*(pilo(x,i) if kp>=0 else pihi(x,i))
            e2=s
        # note: for j==0 term: D2 alpha_0 = 1 = alpha_0 ; alpha_0/alpha_x >= pilo(x,x) handled by i loop (pilo(x,i) with i=x)
        return e1 if e2 is None else max(e1,e2)
    def Rub(x,g,r):
        j=x-g-r
        if j<0: return Fr(0)
        return pihi(x,g+r)*(1-rlo(j))
    return Elb,Rub
def check(r,k,xmax=None):
    Elb,Rub=make(k); V=Vbound(r,k); xmax=xmax or k+3*r+8; bad=[]
    for g in range(1,r):
        T=[Fr(0)]*(xmax+1)
        for x in range(0,xmax+1):
            e=Elb(x,g); term=comb(k,x)*e if (e>0 and x<=k) else 0
            T[x]=term+(T[x-r] if x>=r else 0)
        for x in range(g+r,xmax+1):
            if Elb(x,g)>=Rub(x,g,r): continue
            if T[x]>=V: continue
            bad.append((g,x))
        for x in range(xmax-r+1,xmax+1):
            if T[x]<V: bad.append(('tail',g,x))
    return bad
if __name__=='__main__':
    r,lo,hi=int(sys.argv[1]),int(sys.argv[2]),int(sys.argv[3])
    allbad={}
    for k in range(lo,hi+1):
        b=check(r,k)
        if b: allbad[k]=b
    print("r",r,"k' range",lo,hi,"uncovered k':",sorted(allbad))
    for k in sorted(allbad)[:8]: print(k,allbad[k][:10])
