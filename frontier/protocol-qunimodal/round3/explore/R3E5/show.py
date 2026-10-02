from base import *
import sys
r=int(sys.argv[1]); ms=list(map(int,sys.argv[2].split(','))); 
for n in range(int(sys.argv[3]),int(sys.argv[4])):
    D,tau,mu,T6,s,fire,Bs=params(ms,n,r)
    b0=Bs-1
    print(f"n={n} D={D} D%r={D%r} mu={mu} T6={T6} fire={fire} B*={Bs} tau={tau}")
    if b0<1: continue
    w=window(ms,n,r,b0)
    K=D+1-r*(b0+1)
    print("   K=",K," binding (Phi,m,u,tau):",[x for x in w if 0<K-2*x[1]<r])
