# Certificate C1 (exact rational arithmetic) for the r=4 proof, part "moderate k'".
# For each k' in the list and g in {1,2,3}: every integer x >= g+4 is COVERED, i.e.
#   (L) Elb(x,g) >= Rub(x,g)            [then L' holds at x], or
#   (T) Tlb(x,g) >= V(k') = 2^floor((k'-1)/2)   [then x cannot be x_{n*+1}].
# Tlb is nondecreasing along x -> x+4, and for x > k'+5 (L) can no longer hold,
# so it suffices to scan x <= k'+12 and require (T) on the last 4 scanned x.
import sys
from fractions import Fraction as Fr
from math import comb
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
    def Rub(x,g):
        j=x-g-4
        if j<0: return Fr(0)
        return pihi(x,g+4)*(1-rlo(j))
    return Elb,Rub
def check(k):
    Elb,Rub=make(k); V=2**((k-1)//2); xmax=k+12; bad=[]
    for g in (1,2,3):
        T=[Fr(0)]*(xmax+1)
        for x in range(0,xmax+1):
            e=Elb(x,g); term=comb(k,x)*e if (e>0 and x<=k) else 0
            T[x]=term+(T[x-4] if x>=4 else 0)
        for x in range(g+4,xmax+1):
            if Elb(x,g)>=Rub(x,g): continue
            if T[x]>=V: continue
            bad.append((g,x))
        for x in range(xmax-3,xmax+1):
            if T[x]<V: bad.append(('tail',g,x))
    return bad
if __name__=='__main__':
    lo,hi=int(sys.argv[1]),int(sys.argv[2])
    allbad={}
    for k in range(lo,hi+1):
        b=check(k)
        if b: allbad[k]=b
    print("k' range",lo,hi,"uncovered k':",sorted(allbad), {k:allbad[k][:6] for k in sorted(allbad)[:20]})
