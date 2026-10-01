# Verify prior rule on fit box r=3, k<=8, a_i<=12 nondivisible by 3, b<=60
import sys
from common import *
def prior(a,b):
    S=sum(1 for x in a if x%3==2); F=sum(x//3 for x in a)
    return b<=F+1+2*(S//6)
err=0;tot=0;errs=[]
for a in box_instances():
    p=np.array(pprod(a),dtype=np.int64)  # fits int64? max coefficient check
    for b in range(1,61):
        c=withb(pprod(a),3,b) if False else None
    # faster: compute with int64
    pp=pprod(a)
    for b in range(1,61):
        u=unimodal(withb(pp,3,b))
        tot+=1
        if u!=prior(a,b):
            err+=1; errs.append((a,b,u))
print("total",tot,"errors",err)
for e in errs[:30]: print(e)
