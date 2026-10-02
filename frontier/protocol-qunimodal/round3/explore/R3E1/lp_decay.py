"""Abstract LP: S2 counterexample with FAST tail decay imposed: delta_{x-r} <= theta*delta_x for all x <= x1, where
x1 = (D+1)/2 - z1, z1 = L - r, L = (n0+2)r/2 (binding level, z-coords); plus sign lemma, unimodal e.
If feasible: decay at the crossing alone cannot force S2 (class-sum profile psi must enter).  r<=120 only."""
import numpy as np, sys, math
from lp_abstract import solve
from lp_sign import pattern
from absprof import profile
from geo_check import checks
from absprof import alpha_from_delta
def decay_rows(theta,r,x1):
    def f(X):
        rows=[]
        for x in range(r,min(x1,X)+1): rows.append(({x-r:1.0,x:-theta},0.0))
        return rows
    return f
if __name__=="__main__":
    theta=math.exp(-float(sys.argv[1])); found=0
    for r in [8,12,16,24,32,48]:
      for Fpar in (0,1):
        for X in [3*r,5*r,8*r]:
          pat=pattern(r,X,Fpar)
          for n0 in range(1,9):
            if (n0-(Fpar+1))%2: continue
            L2=(n0+2)*r  # 2L
            x1=int(math.floor((2*X+1)/2-(L2/2-r)))
            if x1<r: continue
            for p in range(0,X+1,max(1,X//8)):
              for bad_n in range(0,(2*X+r*n0)//2+1,max(1,r//6)):
                sol=solve(X,r,n0,p,bad_n,sign_pattern=pat,extra=decay_rows(theta,r,x1))
                if sol is None: continue
                for sc in [10**6,10**9,10**12]:
                    dl=[int(round(v/max(sol)*sc)) for v in sol]
                    if not all(dl[x-r]<=theta*dl[x]*1.0000001 for x in range(r,min(x1,X)+1)): continue
                    try: U=profile(dl,r,n0+8)
                    except AssertionError: continue
                    al=alpha_from_delta(dl); ch=checks(al,r,Fpar)
                    if ch['sign_lemma'] and (n0+1) not in U and (n0+4) in U and all(b in U for b in range(1,n0+1)):
                        print("FAST-DECAY ABSTRACT S2 COUNTEREXAMPLE ln(1/theta)=",sys.argv[1],"r",r,"X",X,"n0",n0,"U",U,
                              {k:v for k,v in ch.items() if k not in('tau','Gamma')}); print("delta",dl); found=1; break
                if found: break
              if found: break
            if found: break
          if found: break
        if found: break
      if found: break
    if not found: print("none found for ln(1/theta)=",sys.argv[1])
