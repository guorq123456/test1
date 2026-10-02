# validate core.Uset against gt_big.profile on random all-equal instances in the fit box
import random,sys
sys.path.insert(0,'/tmp/claude-0/qu/tools')
from gt_big import profile
from core import Uset
random.seed(1)
bad=0;tot=0
for trial in range(300):
    r=random.randint(4,30); s=random.randint(2,r-2); n=random.randint(0,3)
    a0=n*r+s
    if a0>100: continue
    k=random.randint(3,25)
    U,F,T6=Uset(r,[a0]*k,extra=4)
    bs=list(range(1,T6+5))
    pr=profile(r,[a0]*k,bs)
    U2=[b for b,v in zip(bs,pr) if v]
    tot+=1
    if U!=U2: bad+=1; print('MISMATCH',r,a0,k,U,U2)
print('validated',tot,'instances, mismatches',bad)
