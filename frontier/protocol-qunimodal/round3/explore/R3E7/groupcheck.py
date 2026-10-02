# Is sharp L0 a function of (r,k,S,tau) (the data determining U_inf)? Exhaustive r<=rmax,k<=kmax in box.
import sys, itertools
from rules_lib import *
rmax,kmax=int(sys.argv[1]),int(sys.argv[2])
G={}
for r in range(3,rmax+1):
  for k in range(2,kmax+1):
    for s in itertools.combinations_with_replacement(range(1,r),k):
      R=Res(r,s)
      if not in_box(r,R.aL(max(2,R.L0_R2E7()))): continue
      key=(r,k,R.S,tuple(R.tau)); G.setdefault(key,{}).setdefault(L0_sharp_true(R),[]).append(s)
amb=[(k,v) for k,v in G.items() if len(v)>1]
print("groups",len(G),"ambiguous",len(amb))
for k,v in amb[:5]: print(k, {L:ss[:2] for L,ss in v.items()})
