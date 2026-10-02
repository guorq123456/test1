# binding positions in v-form at b0=B*-1: v in (K'/2-r/2,K'/2), w=K'-r-v, need g_v-g_w>=tau_v
from base import *
from collections import defaultdict
import sys
R=int(sys.argv[1]); N=int(sys.argv[2])
best=defaultdict(lambda: None)
for r in range(4,R+1):
  for m1 in range(2,r-1):
    for m2 in range(m1,r-1):
      for m3 in range(m2,r-1):
        for n in range(0,N+1):
          ms=[m1,m2,m3]
          D,tau,mu,T6,s,fire,Bs=params(ms,n,r)
          if Bs<2: continue
          b0=Bs-1; Kp=D+1-b0*r
          J=Kp+2
          A=series_A(ms,n,r,J)
          dl=[A[j]-(A[j-1] if j else 0) for j in range(J+1)]
          g=[0]*(J+1)
          for j in range(J+1): g[j]=dl[j]+(g[j-r] if j>=r else 0)
          G=lambda j: 0 if j<0 else g[j]
          for v in range(-r,Kp):
            if Kp-r<2*v<Kp:
              w=Kp-r-v; t=tau[v%r]
              if t<=0: continue
              mar=G(v)-G(w)-t
              key=(n if n<6 else 6, min(v,4), 'w<0' if w<0 else ('w=0' if w==0 else 'w>0'),fire)
              if best[key] is None or mar<best[key][0]: best[key]=(mar,r,ms,n,v,w,t,G(v),G(w))
for k in sorted(best,key=str): print(k,best[k])
