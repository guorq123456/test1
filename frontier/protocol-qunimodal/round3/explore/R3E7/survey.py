# exhaustive survey of sharp L0 over residue multisets; checks up-ray property; writes data file
import sys, itertools
from core import *
rmax=int(sys.argv[1]); kmax=int(sys.argv[2]); out=open(sys.argv[3],'w')
nonmono=0; cnt=0
for r in range(3,rmax+1):
  for k in range(1,kmax+1):
    for s in itertools.combinations_with_replacement(range(1,r),k):
      R=Res(r,s); top=max(2,R.L0_R2E7())
      if not in_box(r,R.aL(top)): continue
      st=[R.stable(R.aL(L)) for L in range(2,top+1)]
      # up-ray check
      first=st.index(True)
      if not all(st[first:]): nonmono+=1
      L0=first+2; cnt+=1
      out.write(f"{r} {k} {' '.join(map(str,s))} | L0={L0} R2E7={R.L0_R2E7()} K0={R.K0} T={R.T} mu={R.mu} Uinf={R.Uinf}\n")
print("count",cnt,"non-up-ray",nonmono)
