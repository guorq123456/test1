# How local are the binding conditions? For four-middle instances, at b in {T6-1,T6}:
# record which branch (ia/ib/ii) is violated and the offset index (m-m0 for ia, n for ib, j for ii).
import sys, random
from collections import Counter
import rule_low as R
from core import U
random.seed(int(sys.argv[1])); n=int(sys.argv[2]); rlo,rhi=int(sys.argv[3]),int(sys.argv[4])
C=Counter(); maxoff={'ia':0,'ib':0,'ii':0}; inst=0
def branches(r,a,b):
    D,tau,mu,T6,g=R._data(r,a); K=D+1-r*(b+1); G=lambda i: g[i] if i>=0 else 0
    out=[]
    m0=max(1,-((K-1)//2))
    for m in range(m0, r*b+1):
        if K+m>=5*r: break
        if G(K+m) < -tau[(-m)%r]: out.append(('ia',m-m0,K+m))
    for nn in range(0,min(r*b-m0+1,4*r)):
        if K+(r*b-nn)>=0 and g[nn]+tau[nn%r]+tau[(K-nn)%r]<0: out.append(('ib',nn,nn))
    for j in range(0,(K-1)//2+1):
        if g[j]-g[K-j]>tau[j%r]: out.append(('ii',j,K-j))
    return K,out
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
    D,tau,mu,T6,g=R._data(r,a)
    for b in (T6-1,T6):
        if b<1: continue
        K,out=branches(r,a,b)
        kinds=tuple(sorted(set(o[0] for o in out)))
        C[(b-T6,kinds)]+=1
        for o in out: maxoff[o[0]]=max(maxoff[o[0]],o[1])
print('inst',inst,dict(C)); print('max offsets',maxoff)
