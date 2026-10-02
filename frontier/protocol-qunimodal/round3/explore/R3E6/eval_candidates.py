# Evaluate every candidate tried, on one fixed seeded sample of four-middle instances in the fit box
# (r in [4,40] x 3000 sampled + r in [41,120] x 400 sampled, k<=19, a_i<=400). Error = #(instance,b) mismatches, b=1..T6+2.
import random, importlib.util
from core import U, inv
import rule_low as RL, rule_simple as RS
spec=importlib.util.spec_from_file_location('v1','rule_low_v1_discarded.py'); V1=importlib.util.module_from_spec(spec); spec.loader.exec_module(V1)
def t15(r,a,b):
    D,F,tau,Gam=inv(r,a); mu=max([j for j in range(1,r) if tau[j]>0],default=0)
    T6=1+(D+1-2*mu)//r; s=(D+1)%r; fire= tau[s]<=-2 and s>=2*mu
    return b<=T6-2*fire
def c0(r,a,b):
    D,tau,mu,T6,g=RL._data(r,a); return b<=T6
def lowv2(r,a,b):  # v2: (ia) without the m0 lower bound (bug), discarded
    D,tau,mu,T6,g=RL._data(r,a); K=D+1-r*(b+1); G=lambda i: g[i] if i>=0 else 0
    for m in range(1,min(r*b,2*r)+1):
        if G(K+m)<-tau[(-m)%r]: return False
    for n in range(0,min(r*b,2*r)):
        if K+(r*b-n)>=0 and g[n]+tau[n%r]+tau[(K-n)%r]<0: return False
    for j in range(0,(K-1)//2+1):
        if g[j]-g[K-j]>tau[j%r]: return False
    return True
def mkW(Wf):
    def low(r,a,b):
        D,tau,mu,T6,g=RL._data(r,a); K=D+1-r*(b+1); G=lambda i: g[i] if i>=0 else 0
        m0=max(1,-((K-1)//2))
        for m in range(m0,min(r*b,m0+Wf(r))+1):
            if G(K+m)+tau[(-m)%r]<0: return False
        if K>=1 and 1-g[K]>tau[0]: return False
        return True
    return low
def wrap(low):
    def p(r,a,b):
        D,tau,mu,T6,g=RL._data(r,a)
        if b<=T6-2: return True
        if b>T6: return False
        return low(r,a,b)
    return p
C=[('C0 U=[1,T6] (Thm C bound tight)',c0),('C1 T15 formula U=[1,T6-2*FIRE]',t15),
   ('C2 rule_low_v1 (no (ia)) DISCARDED',V1.predict),('C3 rule_low_v2 (ia w/o m0 bound) DISCARDED',wrap(lowv2)),
   ('C4 rule_low final (W=2r; ia,ib,ii)',RL.predict),('C5 rule_simple (W=r; ia + ii at j=0)',RS.predict),
   ('C6 window W=r/2',wrap(mkW(lambda r:r//2))),('C7 window W=3',wrap(mkW(lambda r:3))),
   ('C8 window W=1',wrap(mkW(lambda r:1))),('C9 window W=0 (single condition)',wrap(mkW(lambda r:0)))]
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
