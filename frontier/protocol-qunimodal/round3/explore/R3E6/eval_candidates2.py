# Second batch of candidates (residue-level 'generic f' family), same fixed sample as eval_candidates.py.
import random
from core import U
import rule_low as RL, rule_gen as RG
def mk(W):
    def p(r,a,b):
        a2=[x for x in a if x!=1]; kp=len(a2)
        D=sum(x-1 for x in a2); tau=RG._tau(r,a2)
        mu=max([j for j in range(1,r) if tau[j]>0],default=0); T6=1+(D+1-2*mu)//r
        if b<=T6-2: return True
        if b>T6: return False
        K=D+1-r*(b+1); m0=max(1,-((K-1)//2)); f=RG._f(r,kp,max(4*r,K+m0+r+2)); G=lambda i: f[i] if i>=0 else 0
        for m in range(m0,min(r*b,m0+W(r))+1):
            if G(K+m)+tau[(-m)%r]<0: return False
        if K>=1 and 1-f[K]>tau[0]: return False
        return True
    return p
def gen_noii(r,a,b):
    a2=[x for x in a if x!=1]; kp=len(a2)
    D=sum(x-1 for x in a2); tau=RG._tau(r,a2)
    mu=max([j for j in range(1,r) if tau[j]>0],default=0); T6=1+(D+1-2*mu)//r
    if b<=T6-2: return True
    if b>T6: return False
    K=D+1-r*(b+1); m0=max(1,-((K-1)//2)); f=RG._f(r,kp,max(4*r,K+m0+r+2)); G=lambda i: f[i] if i>=0 else 0
    return all(G(K+m)+tau[(-m)%r]>=0 for m in range(m0,min(r*b,m0+r)+1))
def gen_k(r,a,b):  # generic f but with k (all parts, incl. a_i=1) instead of k'
    kp=len(a); D=sum(x-1 for x in a); tau=RG._tau(r,a)
    mu=max([j for j in range(1,r) if tau[j]>0],default=0); T6=1+(D+1-2*mu)//r
    if b<=T6-2: return True
    if b>T6: return False
    K=D+1-r*(b+1); m0=max(1,-((K-1)//2)); f=RG._f(r,kp,max(4*r,K+m0+r+2)); G=lambda i: f[i] if i>=0 else 0
    for m in range(m0,min(r*b,m0+r)+1):
        if G(K+m)+tau[(-m)%r]<0: return False
    if K>=1 and 1-f[K]>tau[0]: return False
    return True
C=[('C10 rule_gen (generic f with k\', W=r)',RG.predict),('C11 generic f, W=r/2',mk(lambda r:r//2)),
   ('C12 generic f, W=3',mk(lambda r:3)),('C13 generic f, W=0',mk(lambda r:0)),
   ('C14 generic f, W=r, without the j=0 (ii) test',gen_noii),('C15 generic f with k (counting a_i=1) instead of k\'',gen_k)]
random.seed(2026)
err={n:0 for n,_ in C}; inst=0; pairs=0
for (rlo,rhi,N) in [(4,40,3000),(41,120,400)]:
    for it in range(N):
        r=random.randint(rlo,rhi)
        mids=[random.randint(2,r-2) for _ in range(4)]
        n1=random.randint(0,7); nm=random.randint(0,15-n1)
        a=[]
        for s in mids+[1]*n1+[r-1]*nm:
            nmax=(400-s)//r; n_=min(nmax,random.choice([0,0,0,1,1,2,3,random.randint(0,min(nmax,30))])); a.append(r*n_+s)
        a.sort()
        if not RL.domain(r,a): continue
        inst+=1; u,T6,_=U(r,a)
        for b in range(1,T6+3):
            pairs+=1; t=(b in u)
            for n,f in C:
                if f(r,a,b)!=t: err[n]+=1
print('instances',inst,'(instance,b) pairs',pairs)
for n,_ in C: print(f'{n}: {err[n]}')
