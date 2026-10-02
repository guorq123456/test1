# Critical (C) configurations in large-k regimes: n != pi, c_n >= T, a_{n+1} < T. Report n, slack a_{n+3}-T.
import sys, random
from collections import Counter
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E1')
from thr2 import Thr
from core import in_box
def thread_G(T,rho,sig):
    z=[];m=0
    while m<T.c0:
        if m%T.r in (rho,sig): z.append(m)
        m+=1
    return z,[0,0]+[T.g[x] for x in z]
def crit(r,a,out):
    T=Thr(r,a)
    for (rho,sig,low) in T.threads:
        pi=(T.e+(1 if low else 0))%2
        Tv=(-1)**(pi+1)*T.tau[rho]
        if Tv<0: out['TSneg']+=1
        z,G=thread_G(T,rho,sig); I=len(z)
        Gf=lambda j: G[j+1] if j>=-1 else 0
        for n in range(0,I-3):
            if (n-pi)%2==0: continue
            a1=Gf(n+1)-Gf(n); c=Gf(n+1)-(Gf(n-2) if n>=1 else 0)
            a3=Gf(n+3)-Gf(n+2)
            if c>=Tv and a1<Tv:
                out['crit_n%d'%n]+=1
                if a3<Tv: out['VIOL']+=1; print("VIOL",r,a,rho,sig,n,flush=True)
random.seed(int(sys.argv[1])); N=int(sys.argv[2])
out=Counter()
for it in range(N):
    r=random.randint(4,30)
    k=random.randint(10,40)
    style=random.random()
    if style<0.5:
        mid=list(range(2,r-1))
        a=sorted(random.choice(mid)+r*random.randint(0,(100-r)//r) for _ in range(k))
    else:
        a=[]
        while len(a)<k:
            x=random.randint(2,100)
            if x%r: a.append(x)
        a.sort()
    a=[x for x in a if x<=100]
    if not a or not in_box(r,a): continue
    crit(r,a,out); out['inst']+=1
print(dict(out))
