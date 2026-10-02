from base import *
from collections import Counter
import sys
R=int(sys.argv[1]); N=int(sys.argv[2])
stat=Counter(); worst=[]
for r in range(4,R+1):
  for m1 in range(2,r-1):
    for m2 in range(m1,r-1):
      for m3 in range(m2,r-1):
        for n in range(0,N+1):
          ms=[m1,m2,m3]
          D,tau,mu,T6,s,fire,Bs=params(ms,n,r)
          if Bs<2: stat['Bs<2']+=1; continue
          w=window(ms,n,r,Bs-1)
          mn=min(w)
          if mn[0]<0: stat['FAIL']+=1; print("FAIL",r,ms,n,mn)
          # binding: positions with tau<0
          neg=[x for x in w if x[3]<0]
          for x in neg:
            stat[('negtau K-m',min(x[2],3) if x[2]>=0 else x[2], 'm<0' if x[1]<0 else 'm>=0')]+=1
          stat['tot']+=1
for k,v in sorted(stat.items(),key=str): print(k,v)
