# Test rule_H1 against the exact big-integer ground truth (tools/gt_big.py) for large k (up to 40),
# r in [4,30], exactly three middle residues; b in [1, T6+3].
import random,sys
sys.path.insert(0,'/tmp/claude-0/qu/explore2/R2E8'); sys.path.insert(0,'/tmp/claude-0/qu/tools')
from core import stats
import gt_big, rule_H1
seed=int(sys.argv[1]); n=int(sys.argv[2]); random.seed(seed)
inst=0; errs=0; tests=0; bad=[]
for _ in range(n):
    r=random.randint(4,30)
    mids=[random.randint(2,r-2) for _ in range(3)]
    ko=random.randint(10,37); n1=random.randint(0,ko); nm=ko-n1
    FM=random.choice([0,1,2])
    a=[m+r*random.randint(0,FM) for m in mids]+[1+r*random.randint(1,max(1,FM)) for _ in range(n1)]+[r-1+r*random.randint(0,FM) for _ in range(nm)]
    a=sorted(x for x in a if x<=100)
    if len(a)>40 or not rule_H1.domain(r,a): continue
    D,F,Gam,mu,T6=stats(r,a); bs=list(range(1,T6+4))
    if sum(x-1 for x in a)+r*(T6+2) > 6000: continue
    prof=gt_big.profile(r,a,bs); inst+=1
    e=sum(1 for b,u in zip(bs,prof) if u!=rule_H1.predict(r,a,b)); errs+=e; tests+=len(bs)
    if e: bad.append((r,a))
print("instances",inst,"b-tests",tests,"errors",errs,bad[:5])
