# Print critical (C) configurations in bottom form with all local quantities.
import sys, random
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E1')
from thr2 import Thr
from core import in_box
def thread_G(T,rho,sig):
    z=[];m=0
    while m<T.c0:
        if m%T.r in (rho,sig): z.append(m)
        m+=1
    return z,[0,0]+[T.g[x] for x in z]
random.seed(int(sys.argv[1])); N=int(sys.argv[2]); shown=0
for it in range(N):
    r=random.randint(4,30); k=random.randint(4,40)
    if random.random()<0.5:
        a=sorted(random.choice(range(2,r-1))+r*random.randint(0,(100-r)//r) for _ in range(k))
    else:
        a=[]
        while len(a)<k:
            x=random.randint(2,100)
            if x%r: a.append(x)
        a.sort()
    if not in_box(r,a): continue
    T=Thr(r,a)
    for (rho,sig,low) in T.threads:
        pi=(T.e+(1 if low else 0))%2
        Tv=(-1)**(pi+1)*T.tau[rho]
        z,G=thread_G(T,rho,sig); I=len(z)
        Gf=lambda j: G[j+1] if j>=-1 else 0
        A=T.A; dl=lambda m: (A[m] if 0<=m<len(A) else 0)-(A[m-1] if 0<=m-1<len(A) else 0)
        for n in range(1,I-3):
            if (n-pi)%2==0: continue
            av=[Gf(j)-Gf(j-1) for j in range(n-1,n+4)]
            c=av[0]+av[1]+av[2]
            if c>=Tv and av[2]<Tv:
                dd=[dl(z[j-1]) if j>=1 else 0 for j in range(n-1,n+4)]
                print(f"r={r} k={len(a)} F={T.F} n={n} T={Tv} a[n-1..n+3]={av} dt[n-1..n+3]={dd} z={z[max(0,n-2):n+3]}")
                shown+=1
    if shown>25: break
