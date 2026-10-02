# Check simplified per-thread criterion: with bottom positions z_1=rho<z_2=sigma<z_3=rho+r<... (<c0),
# G_n=g_{z_n} (G_0=0), a_n=G_n-G_{n-1}, pi=(e+[low])%2, T=(-1)^{pi+1} tau_rho,  n=e+[low]-beta:
#   thread OK  <=>  a_n >= (-1)^{n-pi} T     (for n>=1);  n<=0 handled by original interval.
import sys, random
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E1')
from thr2 import Thr
from core import U_set
def zs(T,rho,sig):
    out=[];m=0
    while m<T.c0:
        if m%T.r in (rho,sig): out.append(m)
        m+=1
    return out
random.seed(3); bad=0; cnt=0; Tneg=0
for it in range(4000):
    r=random.randint(3,12);k=random.randint(1,9)
    a=sorted(random.choice([x for x in range(2,40) if x%r]) for _ in range(k))
    T=Thr(r,a)
    bmax=(T.D+1)//r+3
    for th in T.threads:
        rho,sig,low=th
        pi=(T.e+(1 if low else 0))%2
        Tv=(-1)**(pi+1)*T.tau[rho]
        if Tv<0: Tneg+=1
        z=zs(T,rho,sig); G=[0]+[T.g[x] for x in z]
        for b in range(1,bmax+1):
            n=T.e+(1 if low else 0)-(b-T.F)
            if n<1: continue
            an=G[n]-G[n-1]
            pred = an >= (-1)**((n-pi)%2)*Tv
            cnt+=1
            if pred!=T.ok_thread(th,b-T.F): bad+=1; print(r,a,th,b,n) if bad<5 else None
print("checked",cnt,"mismatch",bad,"T<0 threads",Tneg)
