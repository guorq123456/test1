# informational: does the same rule also hold for k=2 (outside the declared domain)? fit box, gt_big ground truth
import sys
sys.path.insert(0,'/tmp/claude-0/qu/tools')
from gt_big import profile
from rule_allequal_middle import predict
tot=0;err=0
for r in range(4,31):
    for s in range(2,r-1):
        for n in range(0,(100-s)//r+1):
            a=[n*r+s]*2; F=2*n
            bs=list(range(1,F+(2*(s-1))//r+5))
            for b,v in zip(bs,profile(r,a,bs)):
                tot+=1; err+=(predict(r,a,b)!=v)
print('k=2 pairs',tot,'errors',err)
