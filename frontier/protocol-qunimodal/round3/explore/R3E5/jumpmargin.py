# at jump points: binding pairs (u,m), margin = e_u - e_m - tau_u. Group min margin by (n<=6, u<=6, m<0?)
from base import *
from collections import defaultdict
import sys
R=int(sys.argv[1]); N=int(sys.argv[2])
best=defaultdict(lambda:None)
for r in range(4,R+1):
  for m1 in range(2,r-1):
    for m2 in range(m1,r-1):
      for m3 in range(m2,r-1):
        ms=[m1,m2,m3]; prev=1
        for n in range(1,N+1):
          D,tau,mu,T6,s,fire,Bs=params(ms,n,r)
          if Bs>prev:
            w=window(ms,n,r,Bs-1); K=D+1-r*Bs
            for (phi,m,u,tm) in w:
              if not (0<K-2*m<r): continue
              key=(min(n,6),min(u,6) if u>=0 else u,'m<0' if m<0 else 'm>=0')
              val=(phi,-tm,r,ms,n,u,m)
              if best[key] is None or val<best[key]: best[key]=val
          prev=max(prev,Bs)
for k in sorted(best,key=str): print(k,best[k])
