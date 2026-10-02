# For real threads, find critical configurations for (C): n != pi, c_n >= T, a_{n+1} < T; report a_{n+3}-T and d-values.
import sys, itertools, random
from collections import Counter
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E1')
from thr2 import Thr
def thread_G(T,rho,sig):
    z=[];m=0
    while m<T.c0:
        if m%T.r in (rho,sig): z.append(m)
        m+=1
    return z,[0,0]+[T.g[x] for x in z]   # index: G_j at [j+1], G_{-1}=G_0=0
stats=Counter(); worst=[]
def run(r,a):
    T=Thr(r,a)
    for (rho,sig,low) in T.threads:
        pi=(T.e+(1 if low else 0))%2
        Tv=(-1)**(pi+1)*T.tau[rho]
        z,G=thread_G(T,rho,sig); I=len(z)
        Gf=lambda j: G[j+1] if j+1<len(G) and j>=-1 else (0 if j<-1 else None)
        for n in range(0,I-3):
            if (n-pi)%2==0: continue
            a1=Gf(n+1)-Gf(n); c=Gf(n+1)-Gf(n-2) if n>=1 else Gf(n+1)
            a3=Gf(n+3)-Gf(n+2)
            if c>=Tv and a1<Tv:
                stats['crit']+=1
                worst.append((a3-Tv,r,a,(rho,sig),n,Tv,[Gf(j) for j in range(max(-1,n-2),n+4)]))
for r in range(3,10):
    vals=[x for x in range(2,2*r+3) if x%r]
    for k in range(1,6):
        for a in itertools.combinations_with_replacement(vals,k):
            run(r,list(a))
print(stats)
worst.sort(key=lambda x:x[0])
for w in worst[:15]: print(w)
