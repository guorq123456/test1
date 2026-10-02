# Compare simplified variants of rule_low on random four-middle instances (box, k<=19).
# V(W, use_ib, ii_only_j0): window W for (ia) (in units of r, or absolute), include (ib)?, restrict (ii) to j=0?
import sys, random
import rule_low as R
from core import U
def low_v(r,a,b,W,use_ib,j0):
    D,tau,mu,T6,g=R._data(r,a); K=D+1-r*(b+1); G=lambda i: g[i] if i>=0 else 0
    m0=max(1,-((K-1)//2))
    for m in range(m0,min(r*b,m0+W)+1):
        if G(K+m)<-tau[(-m)%r]: return False
    if use_ib:
        for n in range(0,min(r*b-m0+1,2*r)):
            if K+(r*b-n)>=0 and g[n]+tau[n%r]+tau[(K-n)%r]<0: return False
    for j in range(0,((K-1)//2+1) if not j0 else min(1,(K-1)//2+1)):
        if g[j]-g[K-j]>tau[j%r]: return False
    return True
random.seed(int(sys.argv[1])); n=int(sys.argv[2]); rlo,rhi=int(sys.argv[3]),int(sys.argv[4])
variants=[('W=2r,ib,ii',lambda r:2*r,1,0),('W=2r,noib,ii',lambda r:2*r,0,0),('W=2r,noib,j0',lambda r:2*r,0,1),
          ('W=r,noib,j0',lambda r:r,0,1),('W=r/2,noib,j0',lambda r:r//2,0,1),('W=3,noib,j0',lambda r:3,0,1),('W=1,noib,j0',lambda r:1,0,1),('W=0,noib,j0',lambda r:0,0,1)]
errs={v[0]:0 for v in variants}; inst=0
for it in range(n):
    r=random.randint(rlo,rhi)
    mids=[random.randint(2,r-2) for _ in range(4)]
    n1=random.randint(0,6); nm=random.randint(0,15-n1)
    a=[]
    for s in mids+[1]*n1+[r-1]*nm:
        nmax=(400-s)//r; n_=min(nmax,random.choice([0,0,1,random.randint(0,min(nmax,30))])); a.append(r*n_+s)
    a.sort()
    if not R.domain(r,a): continue
    inst+=1
    u,T6,_=U(r,a)
    for name,Wf,ib,j0 in variants:
        for b in range(1,T6+3):
            p = b<=T6-2 or (b<=T6 and low_v(r,a,b,Wf(r),ib,j0))
            if p!=(b in u): errs[name]+=1
print('inst',inst,errs)
