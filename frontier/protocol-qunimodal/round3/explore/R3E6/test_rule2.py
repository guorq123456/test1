# Adversarial-ish sampler for four-middle instances (k<=19, box): few parts, small parts, many r-1 parts,
# all-quotient-zero etc. Tests rule file; also reports U-shape statistics relative to T6.
import sys, random, importlib.util
from collections import Counter
from core import U
spec=importlib.util.spec_from_file_location('rule',sys.argv[1]); R=importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
seed=int(sys.argv[2]); n=int(sys.argv[3]); rlo=int(sys.argv[4]); rhi=int(sys.argv[5])
random.seed(seed)
err=0; inst=0; bad=[]; shapes=Counter()
for it in range(n):
    r=random.randint(rlo,rhi)
    mode=random.randint(0,4)
    mids=[random.randint(2,r-2) for _ in range(4)]
    if mode==0: n1,nm=0,0
    elif mode==1: n1,nm=0,random.randint(0,15)
    elif mode==2: n1,nm=random.randint(0,15),0
    else: n1=random.randint(0,7); nm=random.randint(0,15-n1)
    res=mids+[1]*n1+[r-1]*nm
    a=[]
    for s in res:
        nmax=(400-s)//r
        if mode==4: n_=random.choice([0,0,0,0,1])
        else: n_=random.choice([0,0,1,random.randint(0,min(nmax,30))])
        n_=min(n_,nmax)
        a.append(r*n_+s)
    a.sort()
    if not R.domain(r,a): continue
    u,T6,_=U(r,a)
    inst+=1; e=0
    sh=tuple(b-T6 for b in u if b>T6-5)+(('full' if u==list(range(1,len(u)+1)) or (len(u) and set(range(1,max(u)-4))<=set(u)) else 'gap'),)
    shapes[sh]+=1
    for b in range(1,T6+3):
        if R.predict(r,a,b)!=(b in u): e+=1
    if e: err+=e; bad.append((r,a,u[-4:],T6))
print(sys.argv[1],'seed',seed,'instances',inst,'b-errors',err,'bad',len(bad))
print(dict(shapes))
for x in bad[:6]: print('  ',x)
