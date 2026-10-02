# Sanity checks (numerical, in fit box) of the lemmas used in the r=4 proof:
#  LB : alpha_{j-1}/alpha_j <= j/(k'-j+1)      (k' = #parts>=2, 1<=j<=k')
#  LB': alpha_{j-1}/alpha_j >= j/(j+k'-1)      (j>=1, alpha_j>0)
#  DOM: alpha_x >= C(k',x)
#  LC : alpha log-concave
#  V  : r=4, n2>=1: every pair has |A_inf| <= 2^floor((n2-1)/2) (and = or 0)
#  KI : L' at n*(C) for every pair (r=4)
import random
from fractions import Fraction as Fr
from math import comb
from lib4 import polyA, in_box
from pairs import pair_data
random.seed(7); viol={'LB':0,'LBp':0,'DOM':0,'LC':0,'V':0,'Lp':0}; n=0
for it in range(3000):
    k=random.randint(1,30); a=sorted(random.choice([x for x in range(1,40) if x%4]) for _ in range(k))
    if not in_box(4,a): continue
    n+=1; c=polyA(a); kp=sum(1 for x in a if x>=2); D=len(c)-1
    for j in range(1,D+1):
        if j<=kp and c[j-1]*(kp-j+1)>j*c[j]: viol['LB']+=1
        if c[j-1]*(j+kp-1)<j*c[j]: viol['LBp']+=1
    for x in range(D+1):
        if c[x]<comb(kp,x): viol['DOM']+=1
        if 0<x<D and c[x]*c[x]<c[x-1]*c[x+1]: viol['LC']+=1
    n2=sum(1 for x in a if x%4==2)
    if n2>=1:
        for p in pair_data(4,a):
            if p['Ainf']!=0 and abs(p['Ainf'])!=2**((n2-1)//2): viol['V']+=1
            m=p['nstar']
            if m is not None and p['y'](m+1)-p['y'](m+2)<p['y'](m+4): viol['Lp']+=1
print(n,viol)
