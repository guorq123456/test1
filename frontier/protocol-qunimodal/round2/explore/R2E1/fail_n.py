# Distribution of first failing n (off parity: a_n<T at n=pi; main: c_n<T) per thread, and of B*-F-e.
import sys, random
from collections import Counter
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E1')
from thr2 import Thr
from core import U_set
def thread_G(T,rho,sig):
    z=[];m=0
    while m<T.c0:
        if m%T.r in (rho,sig): z.append(m)
        m+=1
    return z,[0,0]+[T.g[x] for x in z]
random.seed(int(sys.argv[1])); N=int(sys.argv[2])
offn=Counter(); mainn=Counter(); Bd=Counter()
for it in range(N):
    r=random.randint(3,16); k=random.randint(2,16)
    mode=random.random()
    amax = r+3 if mode<0.4 else (3*r if mode<0.8 else 60)
    a=[]
    while len(a)<k:
        x=random.randint(2,amax)
        if x%r: a.append(x)
    a.sort()
    T=Thr(r,a)
    U=U_set(r,a); Bd[max(U)-T.F-T.e]+=1
    for (rho,sig,low) in T.threads:
        pi=(T.e+(1 if low else 0))%2
        Tv=(-1)**(pi+1)*T.tau[rho]
        z,G=thread_G(T,rho,sig); I=len(z)
        Gf=lambda j: G[j+1] if j>=-1 else 0
        # largest failing n (top-most failure), per parity
        fo=[n for n in range(-1,I) if (n-pi)%2==0 and Gf(n)-Gf(n-1)<Tv]
        fm=[n for n in range(-1,I) if (n-pi)%2==1 and Gf(n+1)-Gf(n-2)<Tv]
        offn[max(fo) if fo else None]+=1; mainn[max(fm) if fm else None]+=1
print("max failing n off:",sorted(offn.items(),key=lambda x:(x[0] is None,x[0])))
print("max failing n main:",sorted(mainn.items(),key=lambda x:(x[0] is None,x[0])))
print("B*-F-e:",sorted(Bd.items()))
