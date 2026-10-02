# cross-validate window test vs brute force gt_big on small base instances (in box)
import sys, random; sys.path.insert(0,'/tmp/claude-0/qu/tools')
from gt_big import profile
from base import *
random.seed(1); bad=0; cnt=0
for _ in range(400):
    r=random.randint(4,14); n=random.randint(0,12)
    ms=sorted(random.randint(2,r-2) for _ in range(3))
    D,tau,mu,T6,s,fire,Bs=params(ms,n,r)
    bs=list(range(1,T6+3))
    pr=profile(r,ms+[r-1]*n,bs)
    for b,v in zip(bs,pr):
        cnt+=1
        if ok(ms,n,r,b)!=v: bad+=1
print("checked",cnt,"mismatch",bad)
