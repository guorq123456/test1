# validate tcrit against ground truth uni_ref within fit box (small instances)
import random, sys
sys.path.insert(0,'/tmp/claude-0/qu/tools'); sys.path.insert(0,'.')
from uni_ref import poly, unimodal
from tcrit import TS
random.seed(1)
bad=0; n=0
for it in range(4000):
    r=random.randint(2,9); k=random.randint(1,6)
    a=sorted(random.randint(1,20) for _ in range(k)); b=random.randint(1,12)
    t=TS(r,a)
    g=unimodal(poly(r,a,b)); p=t.uni(b); pf=t.uni_fast(b)
    n+=1
    if g!=p or g!=pf: bad+=1; print("MISMATCH",r,a,b,g,p,pf)
print("tested",n,"mismatches",bad)
