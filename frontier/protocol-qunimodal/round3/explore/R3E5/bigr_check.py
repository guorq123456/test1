# r>=1000 (allowed region): rule_T15 vs ground truth (tools/uni, exact int128), base + lifted instances, small nm
import random, subprocess, sys
from math import prod
sys.path.insert(0,'/tmp/claude-0/qu/explore3/R3E5')
from rule_T15 import domain, predict, _Bstar
random.seed(int(sys.argv[1])); T=int(sys.argv[2])
err=tot=inst=0
for _ in range(T):
    r=random.randint(1000,1600)
    nm=random.randint(0,8); n1=random.randint(0,2)
    mids=[random.randint(2,r-2) for _ in range(3)]
    if random.random()<0.5: mids=[random.choice([2,3,r-3,r-2,random.randint(2,r-2)]) for _ in range(3)]
    a=mids+[r-1]*nm+[1+r*random.randint(0,1) for _ in range(n1)]
    if random.random()<0.3: a[0]+=r
    a=sorted(a)
    if not domain(r,a): continue
    B=_Bstar(r,a); bs=list(range(1,B+4))
    D=sum(x-1 for x in a)
    if D+r*(B+3)>=65000 or prod(a)*(B+3)>=2**125: continue
    inp=''.join(f"{r} {len(a)} {' '.join(map(str,a))} {b}\n" for b in bs)
    out=subprocess.run(['/tmp/claude-0/qu/tools/uni'],input=inp,capture_output=True,text=True).stdout.split()
    inst+=1
    for b,o in zip(bs,out):
        tot+=1
        if predict(r,a,b)!=(o=='1'): err+=1; print("ERR",r,a,b,o)
print("instances",inst,"tests",tot,"errors",err)
