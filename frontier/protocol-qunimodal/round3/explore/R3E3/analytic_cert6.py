# Certificate C1(r=6): two-parameter analytic coverage.  p = #parts equal to 2, s = #parts >= 3, k = p+s.
#   ratio / second-order bounds: binomial-based with k (Lemma 5), as in analytic_cert2.make
#   domination: alpha >= B_{p,s} = (1+q)^p (1+q+q^2)^s  (coefficientwise)
#   V6(p,s) = floor( 3^{p/2} 2^s / 3 + (1+sqrt3)/3 )  (Lemma 4, r=6)
# Coverage of x (gap g): x-g-6<0, or Elb>=Rub, or T(x) = sum_t B(x-6t)*max(0,Elb(x-6t)) >= V6.
# Since T is nondecreasing along x -> x+6, it suffices: let x* = least x>=g+6 not L-covered; for x>=x*,
# the first element of each class mod 6 must be T-covered (then all later elements of the class are).
import sys
from fractions import Fraction as Fr
from math import isqrt
import mpmath as mp
from analytic_cert2 import make
mp.mp.dps=50
SC=2**30
def V6(p,s):
    v=mp.mpf(3)**(mp.mpf(p)/2)*mp.mpf(2)**s/3+(1+mp.sqrt(3))/3
    return int(mp.floor(v*(1+mp.mpf(10)**-35)))
def tri(s,X):
    c=[1]+[0]*X
    for _ in range(s):
        n=[0]*(X+1)
        for x in range(X+1):
            n[x]=c[x]+(c[x-1] if x>=1 else 0)+(c[x-2] if x>=2 else 0)
        c=n
    return c
def check(k,r=6):
    Elb,Rub=make(k)
    xmax=k+3*r+8
    E={}; Lfail={}
    for g in range(1,r):
        E[g]=[ (Elb(x,g)) for x in range(xmax+1)]
        # integer lower bound of Elb*SC (floor) where positive
        Lfail[g]=[x for x in range(g+r,xmax+1) if not (E[g][x]>=Rub(x,g,r))]
    Ei={g:[ (int(e*SC) if e>0 else 0) for e in E[g]] for g in E}   # floor for positive Fractions
    B=tri(k,xmax)   # p=0
    bad=[]
    for p in range(0,k+1):
        s=k-p
        if p>0:
            # B <- B*(1+q)/(1+q+q^2)
            m=[B[x]+(B[x-1] if x>=1 else 0) for x in range(xmax+1)]
            nb=[0]*(xmax+1)
            for x in range(xmax+1):
                nb[x]=m[x]-(nb[x-1] if x>=1 else 0)-(nb[x-2] if x>=2 else 0)
            B=nb
        V=V6(p,s)
        for g in range(1,r):
            if not Lfail[g]: continue
            xs=Lfail[g][0]
            for x0 in range(xs,xs+r):
                if x0>xmax: bad.append((p,s,g,x0,'range')); continue
                T=0; t=x0
                while t>=0:
                    T+=B[t]*Ei[g][t]; t-=r
                if T< V*SC: bad.append((p,s,g,x0))
    return bad
if __name__=='__main__':
    lo,hi=int(sys.argv[1]),int(sys.argv[2])
    allbad={}
    for k in range(lo,hi+1):
        b=check(k)
        if b: allbad[k]=b
    print("r 6 k range",lo,hi,"uncovered k:",sorted(allbad))
    for k in sorted(allbad)[:6]: print(k,len(allbad[k]),allbad[k][:8])
