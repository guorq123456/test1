# test Lipschitz bound tau_u <= L(u,K) and cover: ediff >= min(L, Tmax) ; report uncovered binding pairs at jumps
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
        t3=tau_of(ms,0,r); Tm=max(t3)
        hmin=min(min(x,r-x) for x in ms)
        assert Tm<=hmin
        for n in range(1,N+1):
          D,tau,mu,T6,s,fire,Bs=params(ms,n,r)
          # Lipschitz check on all t: |tau_t - tau_{t-1}|<=2
          assert all(abs(tau[t]-tau[t-1])<=2 for t in range(r))
          if Bs>prev:
            K=D+1-r*Bs
            for (phi,m,u,tm) in window(ms,n,r,Bs-1):
              if not (0<K-2*m<r) or u<1: continue
              tu=-tm; L=(1+2*u) if K<0 else 2*u-K
              if tu>L: c['LIPFAIL']+=1
              ed=phi-tm  # e_u - e_m
              if ed>=min(L,Tm): c[('cov',min(n,4))]+=1
              else:
                c[('unc',min(n,4))]+=1
                if ('unc',min(n,4)) not in ex: ex[('unc',min(n,4))]=(r,ms,n,u,m,K,tu,ed,L,Tm)
          prev=max(prev,Bs)
for k,v in sorted(c.items(),key=str): print(k,v)
for k,v in ex.items(): print(k,v)
