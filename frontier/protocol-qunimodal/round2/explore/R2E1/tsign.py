# Check conjecture TS: T = (-1)^{e+[low]+1} tau_rho >= 0 for every thread; and sign stats of a_n by parity.
import sys, itertools, random
from collections import Counter
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E1')
from thr2 import Thr
C=Counter(); ex={}
def Gseq(T,rho,sig):
    zs=[];m=0
    while m<T.c0:
        if m%T.r in (rho,sig): zs.append(m)
        m+=1
    return [0,0]+[T.g[z] for z in zs]   # G_{-1},G_0,G_1,...  index shift by 1
def run(r,a):
    T=Thr(r,a)
    for (rho,sig,low) in T.threads:
        pi=(T.e+(1 if low else 0))%2
        Tn=(-1)**(pi+1)*T.tau[rho]
        C['thr']+=1
        if Tn<0: C['TS_fail']+=1; ex.setdefault('TS',(r,a,rho,sig,low,T.tau))
        G=Gseq(T,rho,sig)  # G[j+1] = G_j
        I=len(G)-2
        for n in range(1,I+1):
            an=G[n+1]-G[n]
            if an<0:
                C['neg_a_par'+str((n-pi)%2)]+=1
                ex.setdefault('neg_a_par'+str((n-pi)%2),(r,a,rho,sig,low,n,G))
for r in range(3,10):
    vals=[x for x in range(2,2*r+3) if x%r]
    for k in range(1,6):
        for a in itertools.combinations_with_replacement(vals,k):
            run(r,list(a))
print(C)
for k,v in ex.items(): print(k,v)
