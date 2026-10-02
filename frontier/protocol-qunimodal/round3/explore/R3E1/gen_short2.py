"""Like gen_short.py but more factors (k up to 40), r up to 60, and factor shapes incl. near-flat with bumps,
geometric-sided, and degree up to r-2.  Exact.  Reports S2 failures."""
import sys, random, math
from geo3 import mul
from geo_test import U_of, s2shape
from geo_check import checks
def rand_lc_pal(rng,deg):
    h=deg/2; kind=rng.choice(["gauss","lap","flat","tent"])
    for _ in range(50):
        if kind=="gauss": curv=rng.choice([0.01,0.05,0.2,0.5,1.0,2.0]); c=[1000*math.exp(-curv*(j-h)**2) for j in range(deg+1)]
        elif kind=="lap": s=rng.choice([0.05,0.1,0.3,0.7,1.5]); c=[1000*math.exp(-s*abs(j-h)) for j in range(deg+1)]
        elif kind=="flat": c=[1000.0]*(deg+1)
        else: c=[1000*(1+min(j,deg-j)) for j in range(deg+1)]
        c=[max(1,int(round(x))) for x in c]; c=[min(c[j],c[deg-j]) for j in range(deg+1)]
        if all(c[j]**2>=c[j-1]*c[j+1] for j in range(1,deg)): return c
    return [1]*(deg+1)
if __name__=="__main__":
    rng=random.Random(int(sys.argv[1])); tot=bad=0
    for it in range(int(sys.argv[2])):
        r=rng.randint(4,60); k=rng.randint(2,40)
        A=[1]; facs=[]
        for _ in range(k):
            f=rand_lc_pal(rng,rng.randint(1,r-2)); facs.append(f); A=mul(A,f)
        U=U_of(A,r,2*len(A)//r+6); tot+=1
        if not s2shape(U):
            bad+=1
            N=max(b for b in range(1,len(U)+2) if all(c in U for c in range(1,b+1)))
            ch=checks(A,r,(N+1)%2)
            if bad<=10: print("NOT S2 r",r,"factors",facs,"U",U[:10],{kk:v for kk,v in ch.items() if kk not in('tau','Gamma')},flush=True)
    print("tested",tot,"non-S2",bad)
