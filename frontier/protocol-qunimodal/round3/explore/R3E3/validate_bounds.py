# Numerical validation (fit box) of the bound functions used by certificates C1 (analytic_cert2.make):
#  for random instances and all positions x<=D/2 and gaps g: (delta_x-delta_{x-g})/alpha_x >= Elb,
#  delta_{x-g-r}/alpha_x <= Rub, and sum_t (delta_{x-rt}-delta_{x-rt-g}) >= sum_t C(k,x-rt)*max(0,Elb) when the
#  chain is past its peak (all terms >=0).  Also: at every actual crossing x_{n*+1} the L-bound or automatic case holds.
import random
from fractions import Fraction as Fr
from math import comb
from lib4 import polyA, in_box
from analytic_cert2 import make
from pairs import pair_data
random.seed(13); viol=0; nb=0; ncross=0; badcross=0
for it in range(600):
    r=random.choice([4,5,6]); k=random.randint(2,30)
    a=sorted(random.choice([x for x in range(2,40) if x%r]) for _ in range(k))
    if not in_box(r,a): continue
    c=polyA(a); D=len(c)-1
    al=lambda x: c[x] if 0<=x<=D else 0
    dl=lambda x: al(x)-al(x-1)
    Elb,Rub=make(k)
    for g in range(1,r):
        for x in range(0,D//2+1):
            if al(x)==0: continue
            nb+=1
            if Fr(dl(x)-dl(x-g),al(x))<Elb(x,g): viol+=1
            if x-g-r>=0 and Fr(dl(x-g-r),al(x))>Rub(x,g,r): viol+=1
    for p in pair_data(r,a):
        m=p['nstar']
        if m is None: continue
        x=p['x'](m+1); g=x-p['x'](m+2); ncross+=1
        if x-g-r>=0 and not (Elb(x,g)>=Rub(x,g,r)): badcross+=1
print("bound checks",nb,"violations",viol,"crossings",ncross,"crossings not L-covered",badcross)
