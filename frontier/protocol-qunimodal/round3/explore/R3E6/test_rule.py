# Test a rule file (predict, domain) on random four-middle instances in the box (k<=19).
import sys, random, importlib.util
from core import U
spec=importlib.util.spec_from_file_location('rule',sys.argv[1]); R=importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
seed=int(sys.argv[2]); n=int(sys.argv[3]); rlo=int(sys.argv[4]); rhi=int(sys.argv[5])
random.seed(seed)
err=0; inst=0; badinst=[]
for it in range(n):
    r=random.randint(rlo,rhi)
    mids=[random.randint(2,r-2) for _ in range(4)]
    n1=random.randint(0,8); nm=random.randint(0,15-n1)
    res=mids+[1]*n1+[r-1]*nm
    a=[]
    for s in res:
        nmax=(400-s)//r
        n_=random.choice([0,0,0,1,1,2,3,random.randint(0,min(nmax,12))]); n_=min(n_,nmax)
        a.append(r*n_+s)
    a.sort()
    if not R.domain(r,a): continue
    u,T6,_=U(r,a)
    inst+=1; e=0
    for b in range(1,T6+3):
        if R.predict(r,a,b)!=(b in u): e+=1
    if e: err+=e; badinst.append((r,a,u[-3:],T6))
print(sys.argv[1],'seed',seed,'instances',inst,'b-errors',err,'bad instances',len(badinst))
for x in badinst[:5]: print('  ',x)
