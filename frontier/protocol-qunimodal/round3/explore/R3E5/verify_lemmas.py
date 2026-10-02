# Numerical sanity checks of every lemma of proof_T15_all.txt (fit box: r<=30 all triples, n<=50 => k<=53)
from base import *
from collections import Counter
import sys
R=int(sys.argv[1]); N=int(sys.argv[2])
c=Counter()
def R3coef(ms):
    R=[1]
    for A in ms:
        d=[0]*(len(R)+A-1)
        for i,v in enumerate(R):
            for j in range(A): d[i+j]+=v
        R=d
    return R
for r in range(4,R+1):
  for m1 in range(2,r-1):
    for m2 in range(m1,r-1):
      for m3 in range(m2,r-1):
        ms=[m1,m2,m3]; R3=R3coef(ms); M3=len(R3)-1
        t3=tau_of(ms,0,r)
        c['L3 |tau3|<=m1 fail']+= max(abs(x) for x in t3)>m1
        c['L4 R3_j>=3 fail']+= any(R3[j]<3 for j in range(1,M3))
        prevB=None
        for n in range(0,N+1):
          D,tau,mu,T6,s,fire,Bs=params(ms,n,r)
          c['L1 tau shift fail']+= any(tau[t]!=(-1)**n*t3[(t+n)%r] for t in range(r))
          c['L2 lipschitz fail']+= any(abs(tau[t]-tau[t-1])>2 for t in range(r))
          c['B* odd fail']+= (Bs%2==0)
          if n==0:
              c['n0 B*!=1']+= Bs!=1
              if M3+1>=2*r: c['n0 case3 mu<r-2']+= mu<r-2
          else:
            if Bs>prevB:
              K=D+1-r*Bs
              c['jump fire']+=fire
              c['jump K>r-3']+= K>r-3
              if n==1: c['n1 jump B!=3 or K']+= (Bs!=3 or K!=M3-2*r-1)
              if n==2: c['n2 K>M3-r-3']+= K>M3-r-3
              A=series_A(ms,n,r,r)
              e=[A[j]-(A[j-1] if j else 0) for j in range(r)]
              E=lambda j: 0 if j<0 else e[j]
              for m in range(-2*r,2*r):
                if not (K-r<2*m<K): continue
                u=K-m
                c['u>r-2']+= u>r-2
                phi=tau[m%r]+E(u)-E(m)
                c['Phi<0 at jump']+= phi<0
                if u<=-1: c['(a) tau_u>0']+= tau[u%r]>0
                elif u==0: c['(b) tau_K<-1']+= tau[K%r]<-1
                else:
                    L=min(2*u-K,2*u+1); tu=tau[u%r]
                    c['(c) tau_u>L']+= tu>L
                    c['(c) ediff<min(L,m1)']+= (E(u)-E(m))<min(L,m1)
                    c['(c) checked']+=1
            c['B* decrease']+= Bs<prevB
          prevB=Bs
          c['instances']+=1
for k,v in sorted(c.items()): print(k,v)
