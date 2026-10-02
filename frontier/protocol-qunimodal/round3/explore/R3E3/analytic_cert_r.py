# Certificate C1(r): analytic coverage for general r (exact rationals), conservative over all gaps g in [1,r-1]
# and all classes. V = vmax(r,k') = rigorous upper bound on |tau| over all residue configurations with
# k' parts >= 2 (computed by vbound.py).  Window argument: scan x <= k'+3r+8, require T on the last r scanned x.
import sys
from fractions import Fraction as Fr
from math import comb
from vbound import vmax
def make(k):
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
    def Elb(x,g):
        if x-g<0: return 1-rhi(x)
        return 1-rhi(x)-pihi(x,g)*(1-rlo(x-g))
    return rhi,rlo,pihi,Elb
def check(r,k):
    rhi,rlo,pihi,Elb=make(k); V=vmax(r,k); xmax=k+3*r+8; bad=[]
    for g in range(1,r):
        T=[Fr(0)]*(xmax+1)
        for x in range(0,xmax+1):
            e=Elb(x,g); term=comb(k,x)*e if (e>0 and x<=k) else 0
            T[x]=term+(T[x-r] if x>=r else 0)
        for x in range(g+r,xmax+1):
            j=x-g-r
            R=pihi(x,g+r)*(1-rlo(j))
            if Elb(x,g)>=R: continue
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
