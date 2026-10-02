# Random four-middle instances: U shape, T6, T15-style formula B*.
import random, sys
from core import U, inv
random.seed(int(sys.argv[1]) if len(sys.argv)>1 else 0)
def t15(r,a):
    D,F,tau,Gam=inv(r,a)
    mu=max([j for j in range(1,r) if tau[j]>0],default=0)
    T6=1+(D+1-2*mu)//r
    s=(D+1)%r
    fire= tau[s]<=-2 and s>=2*mu
    return T6-2*fire, T6, mu, s, tau
if __name__=="__main__":
    stats={}
    nonint=0; tot=0
    for it in range(int(sys.argv[2]) if len(sys.argv)>2 else 300):
        r=random.randint(4,30)
        mids=[random.randint(2,r-2) for _ in range(4)]
        n1=random.randint(0,7); nm=random.randint(0,7)
        res=mids+[1]*n1+[r-1]*nm
        a=[]
        for s in res:
            nmax=(400-s)//r
            n=random.choice([0,0,1,1,2,3,random.randint(0,min(nmax,12))])
            if s==1 and n==0: n=1
            a.append(r*n+s)
        a.sort()
        u,T6,mu=U(r,a)
        Bs,T6b,mu2,s,tau=t15(r,a)
        tot+=1
        isint = u==list(range(1,len(u)+1))
        if not isint: nonint+=1
        key=(isint, max(u)-Bs if u else None, T6-max(u))
        stats[key]=stats.get(key,0)+1
        if not isint or max(u)!=Bs:
            print(r,a,"U=",u,"T6",T6,"B*",Bs,"mu",mu,mu2,"s",s,"tau",tau)
    print(stats, "nonint",nonint,"tot",tot)
