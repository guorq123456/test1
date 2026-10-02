"""Abstract LP with the sign lemma imposed (Wintner arcs for tau, for each F parity), see lp_abstract.py.
Searches small (r, X, n0, peak, bad window); prints first feasible and verifies exactly by rounding to integers."""
import numpy as np, itertools, sys
from fractions import Fraction
from lp_abstract import solve
from absprof import profile, alpha_from_delta
def pattern(r,X,Fpar,D=None):
    if D is None: D=2*X
    sigma=D%r + (r if ((D//r)%2)!=Fpar else 0)  # sigma == D mod r, F=(D-sigma)/r has parity Fpar
    F=(D-sigma)//r; assert F%2==Fpar
    c0=Fraction(sigma,2)%r; pat=[]
    for t in range(r):
        u=(Fraction(2*t-1,2)-c0)%r
        if 0<u<Fraction(r,2): pat.append((t,-1))
        elif Fraction(r,2)<u<r: pat.append((t,1))
    return pat
def tau(dl,r):
    al=alpha_from_delta(dl); D=len(al)-1
    d=[al[x]-(al[x-1] if x else 0) for x in range(D+1)]+[-al[D]]
    return [sum(d[x] for x in range(len(d)) if x%r==t) for t in range(r)]
if __name__=="__main__":
    for r in [6,8,10,12]:
      for Fpar in (0,1):
        for X in [2*r,3*r,4*r,6*r]:
          pat=pattern(r,X,Fpar)
          for n0 in [1,2,3,4,5,6,7]:
            if (n0-(Fpar+1))%2: continue      # N* == F+1 mod 2
            for p in range(0,X+1,max(1,X//10)):
              for bad_n in range(0,(2*X+r*n0)//2+1,max(1,r//4)):
                sol=solve(X,r,n0,p,bad_n,sign_pattern=pat)
                if sol is None: continue
                # exact verification after scaling/rounding
                for sc in [10**3,10**4,10**6]:
                    dl=[int(round(v/ max(sol)*sc)) for v in sol]
                    U=profile(dl,r,n0+8)
                    ok_sign=all(s*tv>=0 for (t,s),tv in zip(pat,[tau(dl,r)[t] for t,_ in pat]))
                    if ok_sign and (n0+1) not in U and (n0+4) in U and all(b in U for b in range(1,n0+1)):
                        print("ABSTRACT S2 COUNTEREXAMPLE r",r,"Fpar",Fpar,"X",X,"n0",n0,"U<=n0+8:",U); print("delta",dl); sys.exit(0)
    print("none found")
