# Distribution of the indices i = K+m at which the (ia) condition f_i + tau_{K-i} >= 0 fails (generic f),
# and of K for the (ii) j=0 test, over random four-middle instances; b in {T6-1,T6}.
import random
from collections import Counter
import rule_gen as RG, rule_low as RL
random.seed(99); C=Counter(); Cmin=Counter(); inst=0; ii=Counter()
for it in range(20000):
    r=random.randint(4,60)
    mids=[random.randint(2,r-2) for _ in range(4)]
    n1=random.randint(0,7); nm=random.randint(0,15-n1)
    a=[]
    for s in mids+[1]*n1+[r-1]*nm:
        nmax=(400-s)//r; n_=min(nmax,random.choice([0,0,0,1,1,2,3,random.randint(0,min(nmax,30))])); a.append(r*n_+s)
    a=[x for x in a if x!=1]
    if not RG.domain(r,a): continue
    inst+=1
    kp=len(a); D=sum(x-1 for x in a); tau=RG._tau(r,a)
    mu=max([j for j in range(1,r) if tau[j]>0],default=0); T6=1+(D+1-2*mu)//r
    for b in (T6-1,T6):
        if b<1: continue
        K=D+1-r*(b+1); m0=max(1,-((K-1)//2)); f=RG._f(r,kp,max(4*r,K+m0+r+2)); G=lambda i: f[i] if i>=0 else 0
        bad=[K+m for m in range(m0,min(r*b,m0+r)+1) if G(K+m)+tau[(-m)%r]<0]
        for i in bad: C[min(i,5) if i>=0 else 'neg']+=1
        if bad: Cmin[('neg' if min(bad)<0 else min(bad))]+=1
        if K>=1 and 1-f[K]>tau[0]: ii[K]+=1
print('instances',inst); print('violated indices (capped at 5):',dict(C)); print('smallest violated index:',dict(Cmin)); print('(ii) j=0 violations by K:',dict(ii))
