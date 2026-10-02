# Random search for (C)-critical configurations in real threads; report n distribution and min slack.
import sys, random
from collections import Counter
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E1')
from thr2 import Thr
from critC import thread_G
random.seed(int(sys.argv[1])); N=int(sys.argv[2])
ns=Counter(); worst=None; TSfail=0; viol=0
for it in range(N):
    r=random.randint(3,16); k=random.randint(2,14)
    mode=random.random()
    amax = r+3 if mode<0.4 else (3*r if mode<0.8 else 60)
    a=[]
    while len(a)<k:
        x=random.randint(2,amax)
        if x%r: a.append(x)
    a.sort()
    T=Thr(r,a)
    for (rho,sig,low) in T.threads:
        pi=(T.e+(1 if low else 0))%2
        Tv=(-1)**(pi+1)*T.tau[rho]
        if Tv<0: TSfail+=1
        z,G=thread_G(T,rho,sig); I=len(z)
        Gf=lambda j: G[j+1] if j>=-1 else 0
        for n in range(0,I-3):
            if (n-pi)%2==0: continue
            a1=Gf(n+1)-Gf(n); c=Gf(n+1)-(Gf(n-2) if n>=1 else 0)
            a3=Gf(n+3)-Gf(n+2)
            if c>=Tv and a1<Tv:
                ns[n]+=1
                sl=a3-Tv
                if sl<0: viol+=1; print("VIOL",r,a,rho,sig,n)
                if worst is None or sl<worst[0]: worst=(sl,r,a,(rho,sig),n,Tv)
print("TSfail",TSfail,"viol",viol,"n-dist",dict(ns),"worst",worst)
