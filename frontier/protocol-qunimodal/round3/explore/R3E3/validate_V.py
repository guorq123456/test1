# Numerical validation of V bounds (Lemma 4) and B_{p,s} domination (r=6)
import random
from lib4 import polyA, in_box
from pairs import pair_data
from vbound import vmax
from analytic_cert6 import V6
from analytic_cert6b import Bps
random.seed(17); viol={'V4':0,'V5':0,'V5m':0,'V6':0,'V6m':0,'B':0}; n=0
for it in range(1500):
    r=random.choice([4,5,6]); k=random.randint(1,25)
    a=sorted(random.choice([x for x in range(2,30) if x%r]) for _ in range(k))
    if not in_box(r,a): continue
    n+=1; m=sum(1 for x in a if 2<=x%r<=r-2)
    VA=max([abs(p['Ainf']) for p in pair_data(r,a)]+[0])
    if r==4:
        n2=sum(1 for x in a if x%4==2)
        if n2>=1 and VA>2**((n2-1)//2): viol['V4']+=1
    if r==5:
        if VA>vmax(5,k): viol['V5']+=1
        if m<=5 and VA>5: viol['V5m']+=1
    if r==6:
        p_=a.count(2); s_=k-p_
        if VA>V6(p_,s_): viol['V6']+=1
        if m<=5 and VA>11: viol['V6m']+=1
        c=polyA(a); B=Bps(p_,s_,len(c)-1)
        if any(c[x]<B[x] for x in range(len(c))): viol['B']+=1
print(n,viol)
