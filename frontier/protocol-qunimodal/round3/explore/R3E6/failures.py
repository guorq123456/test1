# Collect instances where T15 formula (U=[1,B*]) fails, four-middle random instances.
import random, sys, json
from core import U, inv
from explore1 import t15
seed=int(sys.argv[1]); n=int(sys.argv[2]); rmax=int(sys.argv[3])
random.seed(seed)
out=open(f'fail_{seed}.jsonl','w'); tot=0; nf=0
for it in range(n):
    r=random.randint(4,rmax)
    mids=[random.randint(2,r-2) for _ in range(4)]
    n1=random.randint(0,7); nm=random.randint(0,15-n1)
    res=mids+[1]*n1+[r-1]*nm
    a=[]
    for s in res:
        nmax=(400-s)//r
        n_=random.choice([0,0,1,1,2,3,random.randint(0,min(nmax,12))])
        n_=min(n_,nmax)
        if s==1 and n_==0: n_=1
        a.append(r*n_+s)
    a.sort()
    u,T6,mu=U(r,a)
    Bs,_,mu2,s,tau=t15(r,a)
    tot+=1
    if u!=list(range(1,Bs+1)):
        nf+=1
        D,F,_,_=inv(r,a)
        out.write(json.dumps(dict(r=r,a=a,U=u,T6=T6,Bs=Bs,mu=mu2,s=s,tau=tau,D=D,F=F))+'\n')
print(seed,"tot",tot,"fail",nf)
