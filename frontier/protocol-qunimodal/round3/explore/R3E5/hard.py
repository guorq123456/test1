# at jumps: binding pairs with u>=1 and tau_u > crude bound (n-2 for n>=3; for n<=2 everything)
from base import *
from collections import Counter
import sys
R=int(sys.argv[1]); N=int(sys.argv[2])
c=Counter(); ex={}
for r in range(4,R+1):
  for m1 in range(2,r-1):
    for m2 in range(m1,r-1):
      for m3 in range(m2,r-1):
        ms=[m1,m2,m3]; prev=1
        for n in range(1,N+1):
          D,tau,mu,T6,s,fire,Bs=params(ms,n,r)
          if Bs>prev:
            K=D+1-r*Bs
            assert K<=r-3 and not fire
            for (phi,m,u,tm) in window(ms,n,r,Bs-1):
              if not (0<K-2*m<r) or u<1: continue
              tu=-tm
              if n>=3 and tu<=n-2: continue
              key=(n if n<=3 else 'n>=4', 'm<0' if m<0 else 'm>=0', 'tau<=u+1' if tu<=u+1 else 'tau>u+1')
              c[key]+=1
          prev=max(prev,Bs)
for k,v in sorted(c.items(),key=str): print(k,v)
