# compare rule_T15 against ground truth inside the fit box (r<=120, k<=54 => no exclusion (b) issue; a_i<=400)
import random, subprocess, sys
sys.path.insert(0,'/tmp/claude-0/qu/explore3/R3E5'); sys.path.insert(0,'/tmp/claude-0/qu/tools')
from rule_T15 import domain, predict, _Bstar
from gt_big import profile
random.seed(int(sys.argv[1])); T=int(sys.argv[2])
err=0; tot=0; inst=0
for _ in range(T):
    r=random.choice(list(range(4,31))+list(range(31,121)))
    nm=random.randint(0,random.choice([5,15,40,50]))
    n1=random.randint(0,4)
    k=3+nm+n1
    if k>54: continue
    mids=[random.randint(2,r-2) for _ in range(3)]
    a=[]
    for m in mids: a.append(m+r*random.randint(0,(400-m)//r if random.random()<0.3 else 0))
    for _ in range(nm): a.append(r-1+r*(random.randint(0,(400-r+1)//r) if random.random()<0.2 else 0))
    for _ in range(n1): a.append(1+r*random.randint(0,(399)//r))
    a=sorted(a)
    if max(a)>400 or not domain(r,a): continue
    B=_Bstar(r,a)
    bs=list(range(1,B+4))
    # size guard: degree
    D=sum(x-1 for x in a)
    if D+r*(B+3)>60000: continue
    from math import prod
    if prod(a)*(B+3) < 2**125 and D+r*(B+3)<65000:
        inp=''.join(f"{r} {len(a)} {' '.join(map(str,a))} {b}\n" for b in bs)
        out=subprocess.run(['/tmp/claude-0/qu/tools/uni'],input=inp,capture_output=True,text=True).stdout.split()
        gt=[o=='1' for o in out]
    else:
        if D+r*(B+3)>6000: continue
        gt=profile(r,a,bs)
    inst+=1
    for b,v in zip(bs,gt):
        tot+=1
        if predict(r,a,b)!=v: err+=1; print("ERR",r,a,b,v)
print("instances",inst,"(r,a,b) tests",tot,"errors",err)
