# Certificate C1-6' (r=6), restricted to k <= 140.  Same as analytic_cert6.py, but the domination term B_{p,s}(x) is
# replaced by the lower bound  Bm(x) = max_{x1} C(p,x1) * Tri_s(x-x1)  (one term of the convolution), so only the
# single-value polynomials (1+q)^p and (1+q+q^2)^s with p,s <= 140 are ever expanded.
import sys
from math import comb
from analytic_cert2 import make
from analytic_cert6 import V6, SC
r=6
def tri_rows(K,X):
    rows=[[1]+[0]*X]
    for s in range(1,K+1):
        c=rows[-1]; rows.append([c[x]+(c[x-1] if x>=1 else 0)+(c[x-2] if x>=2 else 0) for x in range(X+1)])
    return rows
def check(k,TR):
    assert k<=140
    Elb,Rub=make(k); xmax=k+3*r+8
    Lfail={}; Ei={}
    for g in range(1,r):
        E=[Elb(x,g) for x in range(xmax+1)]
        Lfail[g]=[x for x in range(g+r,xmax+1) if not (E[x]>=Rub(x,g,r))]
        assert Lfail[g]
        Ei[g]=[(int(e*SC) if e>0 else 0) for e in E]
    bad=[]
    for p in range(0,k+1):
        s=k-p; T3=TR[s]
        Bm=[max(comb(p,x1)*T3[x-x1] for x1 in range(0,min(p,x)+1)) for x in range(xmax+1)]
        V=V6(p,s)
        for g in range(1,r):
            xs=Lfail[g][0]
            for x0 in range(xs,xs+r):
                if x0>xmax: bad.append((p,s,g,x0,'range')); continue
                T=0; t=x0
                while t>=0: T+=Bm[t]*Ei[g][t]; t-=r
                if T<V*SC: bad.append((p,s,g,x0))
    return bad
if __name__=='__main__':
    lo,hi=int(sys.argv[1]),int(sys.argv[2])
    TR=tri_rows(hi,hi+3*r+8)
    allbad={}
    for k in range(lo,hi+1):
        b=check(k,TR)
        if b: allbad[k]=b
    print("r 6 (max-term) k range",lo,hi,"uncovered k:",sorted(allbad))
