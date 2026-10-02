# at jump points n (B*(n)>B*(n-1), or n=0), record K, mu, fire, max binding u, and whether all binding indices < r-1
from base import *
from collections import Counter
import sys
R=int(sys.argv[1]); N=int(sys.argv[2])
c=Counter(); ex={}
for r in range(4,R+1):
  for m1 in range(2,r-1):
    for m2 in range(m1,r-1):
      for m3 in range(m2,r-1):
        ms=[m1,m2,m3]; prev=None
        for n in range(0,N+1):
          D,tau,mu,T6,s,fire,Bs=params(ms,n,r)
          if n==0:
              c[('n0 B*',Bs,fire)]+=1
          if prev is not None:
              c[('dB',Bs-prev)]+=1
          if prev is not None and Bs>prev:
              b0=Bs-1; K=D+1-r*(b0+1)
              bind=[m for m in range(-2*r,2*r) if 0<K-2*m<r]
              umax=max(K-m for m in bind)
              key=('jump',fire, 'umax<r-1' if umax<r-1 else 'umax>=r-1', 'K<0' if K<0 else 'K>=0')
              c[key]+=1
              if key not in ex: ex[key]=(r,ms,n,K,mu,umax)
          prev=Bs
for k,v in sorted(c.items(),key=str): print(k,v)
for k,v in ex.items(): print(k,v)
