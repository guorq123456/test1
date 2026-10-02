from base import *
from collections import Counter
import sys
R=int(sys.argv[1]); N=int(sys.argv[2])
c=Counter()
for r in range(4,R+1):
  for m1 in range(2,r-1):
    for m2 in range(m1,r-1):
      for m3 in range(m2,r-1):
        for n in range(0,N+1):
          ms=[m1,m2,m3]
          D,tau,mu,T6,s,fire,Bs=params(ms,n,r)
          if Bs<2: continue
          w=window(ms,n,r,Bs-1)
          mn=min(w)
          if mn[0]<=2: c[(mn[0],mn[1]<0,mn[2],mn[3],fire)]+=1
for k,v in sorted(c.items()): print(k,v)
