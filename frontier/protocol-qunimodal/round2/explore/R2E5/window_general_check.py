# sanity check of the Window Lemma on random general tuples (not all equal) in the fit box:
# P unimodal iff tau_m + g_{K-m} - g_m >= 0 for the r largest integers m < K/2, g = A(1-q)/(1-q^r), K = D+1-r(b+1)
import random,sys
sys.path.insert(0,'/tmp/claude-0/qu/tools')
from gt_big import poly_a, profile
from core import gseries
def window(r,a,b):
    A=poly_a(a); D=len(A)-1
    G=[0]*r
    for j,v in enumerate(A): G[j%r]+=v
    tau=[G[t]-G[t-1] for t in range(r)]
    K=D+1-r*(b+1); m0=(K-1)//2
    L=max(K-(m0-r+1),0)+1
    g=gseries(A,r,L); gg=lambda j: g[j] if j>=0 else 0
    return all(tau[m%r]+gg(K-m)-gg(m)>=0 for m in range(m0,m0-r,-1))
random.seed(11); tot=0; err=0
for t in range(1500):
    r=random.randint(2,30); k=random.randint(1,12)
    a=sorted(random.randint(1,60) for _ in range(k))
    D=sum(x-1 for x in a); F=sum(x//r for x in a)
    bs=list(range(1,F+D//r+4))
    if len(bs)>60: bs=random.sample(bs,60)
    pr=profile(r,a,bs)
    for b,v in zip(bs,pr):
        tot+=1
        if window(r,a,b)!=v: err+=1; print('ERR',r,a,b,v)
print('general window-lemma check: pairs',tot,'errors',err)
